#!/usr/bin/env python3
"""
RAG Spec-2: Retrieval Pipeline validation

This script implements the complete retrieval pipeline validation for RAG systems.
It connects to Qdrant Cloud, loads existing vector collections, accepts test queries,
performs top-k similarity search, validates results using returned text, metadata
and source URLs, and logs retrieval scores for pipeline verification.

The script follows these main steps:
1. Initialize Cohere client for embedding generation
2. Initialize Qdrant client for vector search
3. Generate embedding for the input query
4. Perform similarity search in Qdrant
5. Process and validate results
6. Generate comprehensive validation report

Usage:
    python retrieve.py --query "your query here" --top-k 5 --collection "documents"

Environment Variables Required:
    - QDRANT_URL: URL for Qdrant Cloud instance
    - QDRANT_API_KEY: API key for Qdrant Cloud
    - COHERE_API_KEY: API key for Cohere service

Performance Target:
    - Complete retrieval pipeline should execute within 5 seconds
"""

import os
import sys
import logging
import argparse
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
from dataclasses import dataclass, asdict
from urllib.parse import urlparse

# Import required dependencies
try:
    import cohere
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install required dependencies: pip install cohere qdrant-client python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()


@dataclass
class Query:
    """User input text that needs to be semantically matched against stored content"""
    text: str
    embedding: Optional[List[float]] = None
    top_k: int = 5


@dataclass
class SearchResult:
    """Individual result from the similarity search"""
    id: str
    text: str
    metadata: Dict[str, Any]
    score: float
    source_url: str


@dataclass
class RetrievalResult:
    """Collection of top-k search results for a query"""
    query: Query
    results: List[SearchResult]
    execution_time: float
    timestamp: datetime


@dataclass
class ValidationReport:
    """Report containing validation results for the retrieval pipeline"""
    retrieval_result: RetrievalResult
    is_valid: bool
    validation_details: Dict[str, Any]
    log_entries: List[str]


def setup_logging():
    """Set up logging configuration for the retrieval pipeline."""
    # For Windows compatibility, ensure proper encoding handling
    import io
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('retrieval_validation.log', encoding='utf-8')
        ],
        force=True  # This ensures the configuration is applied even if logging was already configured
    )
    return logging.getLogger(__name__)


def parse_arguments():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="RAG Retrieval Pipeline Validation Tool"
    )
    parser.add_argument(
        "--query", "-q",
        type=str,
        required=True,
        help="The text query to validate"
    )
    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=5,
        help="Number of results to retrieve (default: 5, range: 1-100)"
    )
    parser.add_argument(
        "--collection", "-c",
        type=str,
        default="documents",
        help="Qdrant collection name to search in (default: 'documents')"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.top_k < 1 or args.top_k > 100:
        parser.error("--top-k must be between 1 and 100")

    return args


def create_cohere_client():
    """Implement Cohere embedding function to convert queries to vectors"""
    api_key = os.getenv('COHERE_API_KEY')
    if not api_key:
        raise ValueError("COHERE_API_KEY environment variable is not set")

    return cohere.Client(api_key)


def create_qdrant_client():
    """Implement Qdrant Cloud connection function"""
    url = os.getenv('QDRANT_URL')
    api_key = os.getenv('QDRANT_API_KEY')

    if not url or not api_key:
        raise ValueError("QDRANT_URL and QDRANT_API_KEY environment variables must be set")

    # For Qdrant Cloud, make sure to use HTTPS and proper URL format
    if url.startswith('https://') or url.startswith('http://'):
        # URL already includes protocol, use as is
        full_url = url
    else:
        # Add HTTPS if not present
        full_url = f"https://{url}" if not url.startswith('http') else url

    return QdrantClient(
        url=full_url,
        api_key=api_key,
        timeout=120,  # Increased from 30 to 120 seconds to prevent SSL handshake timeouts
        prefer_grpc=False,  # Use HTTP instead of gRPC for better compatibility
        https=True  # Explicitly enable HTTPS for cloud connections
    )


def validate_result(result: SearchResult) -> bool:
    """Create validation functions for results"""
    # Check that text is not empty
    if not result.text or len(result.text.strip()) == 0:
        return False

    # Check that score is between 0 and 1
    if not (0 <= result.score <= 1):
        return False

    # Check that source_url is a valid URL format (basic validation)
    # Accept both proper URLs and file paths
    try:
        parsed = urlparse(result.source_url)
        # Valid if it's a proper URL with scheme and netloc
        if parsed.scheme and parsed.netloc:
            return True
        # Also accept file paths (which typically have no scheme/netloc)
        # Check if it's a file path by looking for common patterns
        if '\\' in result.source_url or '/' in result.source_url or result.source_url.endswith(('.md', '.txt', '.html', '.pdf')):
            return bool(result.source_url and result.source_url.strip())
        return False
    except:
        # If URL parsing fails, check if it's at least a non-empty string
        return bool(result.source_url and result.source_url.strip())


def perform_top_k_search(qdrant_client: QdrantClient, query_embedding: List[float],
                        collection_name: str, top_k: int):
    """Implement top-k similarity search function"""
    # First, try without specifying vector name (the default approach that worked for textbook_content)
    try:
        search_results = qdrant_client.query_points(
            collection_name=collection_name,
            query=query_embedding,
            limit=top_k,
            with_payload=True,
            with_vectors=False
        )
    except Exception as e:
        # If it fails with a vector name error, try specifying the vector name
        if "requires specified vector name" in str(e).lower() or "vector name" in str(e).lower():
            # Try with the 'content' vector name (as indicated in the error message)
            search_results = qdrant_client.query_points(
                collection_name=collection_name,
                query=query_embedding,
                using="content",  # Specify the vector field name
                limit=top_k,
                with_payload=True,
                with_vectors=False
            )
        else:
            # If it's a different error, raise it
            raise e
    return search_results


def validate_similarity_search_accuracy(search_results: List[SearchResult]) -> Dict[str, Any]:
    """Implement accuracy validation function for search results"""
    if not search_results:
        return {
            "accuracy_valid": False,
            "metrics": {
                "count": 0,
                "avg_score": 0,
                "score_variance": 0
            },
            "details": "No results to validate"
        }

    scores = [result.score for result in search_results]
    avg_score = sum(scores) / len(scores)

    # Calculate variance as a measure of consistency
    score_variance = sum((score - avg_score) ** 2 for score in scores) / len(scores)

    # Determine if results are accurate based on score distribution
    accuracy_valid = avg_score > 0.3  # Threshold for relevance

    return {
        "accuracy_valid": accuracy_valid,
        "metrics": {
            "count": len(search_results),
            "avg_score": avg_score,
            "score_variance": score_variance,
            "min_score": min(scores),
            "max_score": max(scores)
        },
        "details": f"Average score: {avg_score:.3f}, Variance: {score_variance:.3f}"
    }


def measure_content_relevance(query_text: str, search_results: List[SearchResult]) -> Dict[str, Any]:
    """Create function to measure relevance of returned content"""
    if not search_results:
        return {
            "relevance_score": 0,
            "metrics": {
                "result_count": 0,
                "keyword_matches": 0
            },
            "details": "No results to measure relevance"
        }

    # Simple relevance measure based on keyword overlap between query and results
    query_words = set(query_text.lower().split())
    total_keyword_matches = 0
    result_count = len(search_results)

    for result in search_results:
        result_words = set(result.text.lower().split())
        keyword_matches = len(query_words.intersection(result_words))
        total_keyword_matches += keyword_matches

    avg_keyword_matches = total_keyword_matches / result_count if result_count > 0 else 0

    # Calculate a simple relevance score (0-1) based on keyword matches
    relevance_score = min(avg_keyword_matches / 5, 1.0)  # Normalize to 0-1 range

    return {
        "relevance_score": relevance_score,
        "metrics": {
            "result_count": result_count,
            "total_keyword_matches": total_keyword_matches,
            "avg_keyword_matches": avg_keyword_matches
        },
        "details": f"Average keyword matches per result: {avg_keyword_matches:.2f}"
    }


def make_cohere_request_with_retry(cohere_client, texts, model, input_type, logger, max_retries=3):
    """Make a Cohere API request with retry logic for handling rate limits."""
    import random
    for attempt in range(max_retries):
        try:
            response = cohere_client.embed(
                texts=texts,
                model=model,
                input_type=input_type
            )
            return response
        except Exception as e:
            if "Too Many Requests" in str(e) or (hasattr(e, 'status_code') and e.status_code == 429):
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff with jitter
                    logger.info(f"Rate limited, waiting {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    continue
            elif attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Request failed, retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            # If all retries failed, re-raise the exception
            raise e


def main():
    """Main function to run the retrieval validation."""
    logger = setup_logging()
    args = parse_arguments()

    logger.info("="*60)
    logger.info("STARTING RAG RETRIEVAL VALIDATION")
    logger.info(f"Query: '{args.query}'")
    logger.info(f"Parameters - top_k: {args.top_k}, collection: {args.collection}")
    logger.info("="*60)

    # Record start time for total execution time calculation
    total_start_time = time.time()

    # Validate environment variables
    required_env_vars = ['QDRANT_URL', 'QDRANT_API_KEY', 'COHERE_API_KEY']
    for var in required_env_vars:
        if not os.getenv(var):
            logger.error(f"Missing required environment variable: {var}")
            sys.exit(1)

    logger.info("[OK] All required environment variables are present")

    try:
        # Step 1: Initialize Cohere client (pipeline step logging)
        logger.info("Step 1: Initializing Cohere client for embedding generation...")
        cohere_client = create_cohere_client()
        logger.info("[OK] Cohere client initialized successfully")

        # Step 2: Initialize Qdrant client (pipeline step logging)
        logger.info("Step 2: Initializing Qdrant client for vector search...")
        qdrant_client = create_qdrant_client()
        logger.info("[OK] Qdrant client initialized successfully")

        # Step 3: Test connection to Qdrant (pipeline step logging)
        logger.info("Step 3: Testing connection to Qdrant Cloud...")

        # Add retry logic for Qdrant operations
        collections = None
        for attempt in range(3):
            try:
                collections = qdrant_client.get_collections()
                break
            except Exception as e:
                logger.warning(f"Qdrant connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < 2:  # Don't sleep on the last attempt
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise e

        logger.info(f"[OK] Connected to Qdrant, available collections: {[col.name for col in collections.collections]}")

        if args.collection not in [col.name for col in collections.collections]:
            logger.error(f"Collection '{args.collection}' not found in Qdrant")
            logger.info(f"Available collections: {[col.name for col in collections.collections]}")
            sys.exit(1)

        logger.info(f"[OK] Target collection '{args.collection}' exists and is accessible")

        # Step 4: Query processing (pipeline step logging)
        logger.info("Step 4: Processing query through embedding pipeline...")
        logger.info(f"  - Input query: '{args.query}'")

        # Accept test query and convert to embedding using Cohere (US1)
        logger.info("  - Generating embedding for query...")
        embed_start_time = time.time()

        # Use different models based on collection name to match vector dimensions
        if args.collection == "content_chunks":
            # content_chunks collection expects 1024-dim vectors (likely from embed-english-v3.0)
            model = "embed-english-v3.0"
            logger.info(f"  - Using {model} model for {args.collection} collection (1024-dim vectors)")
        else:
            # Other collections expect 768-dim vectors (from embed-multilingual-v2.0)
            model = "embed-multilingual-v2.0"
            logger.info(f"  - Using {model} model for {args.collection} collection (768-dim vectors)")

        response = make_cohere_request_with_retry(
            cohere_client=cohere_client,
            texts=[args.query],
            model=model,
            input_type="search_query",
            logger=logger
        )
        query_embedding = response.embeddings[0]
        embed_time = time.time() - embed_start_time
        logger.info(f"  - Query embedding generated in {embed_time:.3f} seconds")
        logger.info("[OK] Embedding generation completed")

        # Step 5: Similarity search execution (pipeline step logging)
        logger.info("Step 5: Executing similarity search in Qdrant...")
        search_start_time = time.time()

        # Verify that the query_points method exists
        if not hasattr(qdrant_client, 'query_points'):
            logger.error("[ERROR] Qdrant client does not have a query_points method. This might be a version compatibility issue.")
            logger.error(f"[ERROR] Available methods: {[method for method in dir(qdrant_client) if not method.startswith('_')]}")
            sys.exit(1)

        # Add retry logic for the search operation
        search_results = None
        for attempt in range(3):
            try:
                search_results = perform_top_k_search(qdrant_client, query_embedding, args.collection, args.top_k)
                break
            except Exception as e:
                logger.warning(f"Qdrant search attempt {attempt + 1} failed: {str(e)}")
                if attempt < 2:  # Don't sleep on the last attempt
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise e

        search_time = time.time() - search_start_time
        logger.info(f"[OK] Search completed in {search_time:.3f} seconds")
        # Handle the new response format - QueryResponse object
        if hasattr(search_results, 'points'):
            search_results_list = search_results.points
        else:
            search_results_list = search_results
        logger.info(f"  - Retrieved {len(search_results_list)} results from Qdrant")

        # Step 6: Results processing and validation (pipeline step logging)
        logger.info("Step 6: Processing and validating results...")
        logger.info(f"  - Processing {len(search_results_list)} search results...")

        if not search_results_list:
            logger.warning("[WARN] No results returned from search")
            print("No results found for the query.")
            return

        # Convert search results to our data model
        logger.info("  - Converting results to data model...")
        search_result_objects = []
        for result in search_results_list:
            search_result_obj = SearchResult(
                id=str(result.id),
                text=result.payload.get('content', result.payload.get('text', 'No content available')) if hasattr(result, 'payload') else 'No content available',
                metadata=result.payload if hasattr(result, 'payload') else {},
                score=result.score if hasattr(result, 'score') else 0.0,
                source_url=result.payload.get('source_url', result.payload.get('source', 'No source URL')) if hasattr(result, 'payload') else 'No source URL'
            )
            search_result_objects.append(search_result_obj)

        # Validate returned text content and metadata (US1)
        logger.info("  - Validating result content and metadata...")
        valid_results = []
        invalid_results = []
        for result in search_result_objects:
            if validate_result(result):
                valid_results.append(result)
            else:
                invalid_results.append(result)

        logger.info(f"  - Validation results: {len(valid_results)} valid, {len(invalid_results)} invalid")
        logger.info("[OK] Results processing and validation completed")

        # Calculate total execution time
        execution_time = time.time() - total_start_time

        # Print results in a structured format
        print("\n" + "="*80)
        print(f"RETRIEVAL RESULTS FOR: '{args.query}'")
        print(f"TOP-{args.top_k} RESULTS FROM COLLECTION: '{args.collection}'")
        print(f"EXECUTION TIME: {execution_time:.2f} seconds")
        print("="*80)

        for i, result in enumerate(search_result_objects, 1):
            # Safely print results, handling any encoding issues
            try:
                print(f"\n{i}. SCORE: {result.score:.4f}")
                # Clean the content to remove problematic characters for display
                clean_content = result.text[:200].encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                print(f"   CONTENT: {clean_content}{'...' if len(result.text) > 200 else ''}")
                clean_source = result.source_url.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                print(f"   SOURCE: {clean_source}")
                print(f"   ID: {result.id}")
            except Exception as e:
                print(f"\n{i}. SCORE: {result.score:.4f}")
                print(f"   CONTENT: [Content with encoding issues - {len(result.text)} chars]")
                print(f"   SOURCE: {result.source_url}")
                print(f"   ID: {result.id}")

        print("\n" + "="*80)

        # Create data models for the results
        query_obj = Query(text=args.query, embedding=query_embedding, top_k=args.top_k)
        retrieval_result = RetrievalResult(
            query=query_obj,
            results=search_result_objects,
            execution_time=execution_time,
            timestamp=datetime.now()
        )

        # Validate similarity search accuracy (US2)
        accuracy_validation = validate_similarity_search_accuracy(search_result_objects)
        logger.info(f"[OK] Accuracy validation: {accuracy_validation['details']}")

        # Measure content relevance (US2)
        relevance_metrics = measure_content_relevance(args.query, search_result_objects)
        logger.info(f"[OK] Relevance metrics: {relevance_metrics['details']}")

        # Validation report
        validation_report = ValidationReport(
            retrieval_result=retrieval_result,
            is_valid=len(valid_results) > 0,
            validation_details={
                "total_results": len(search_results_list),
                "valid_results": len(valid_results),
                "invalid_results": len(invalid_results),
                "avg_similarity_score": sum(r.score for r in search_result_objects) / len(search_result_objects) if search_result_objects else 0,
                "accuracy_validation": accuracy_validation,
                "relevance_metrics": relevance_metrics
            },
            log_entries=[
                f"Query processed: {args.query}",
                f"Execution time: {execution_time:.2f}s",
                f"Results: {len(search_result_objects)}",
                f"Valid results: {len(valid_results)}",
                f"Accuracy validation: {accuracy_validation['details']}",
                f"Relevance score: {relevance_metrics['relevance_score']:.3f}"
            ]
        )

        print("\nVALIDATION REPORT:")
        print(json.dumps(asdict(validation_report), indent=2, default=str))

        # Step 7: Performance metrics logging (US3)
        logger.info("Step 7: Performance metrics and final validation...")
        logger.info(f"  - Total execution time: {execution_time:.3f} seconds")
        logger.info(f"  - Embedding generation time: {embed_time:.3f} seconds")
        logger.info(f"  - Search execution time: {search_time:.3f} seconds")
        logger.info(f"  - Total results: {len(search_result_objects)}")
        logger.info(f"  - Valid results: {len(valid_results)}")
        logger.info(f"  - Invalid results: {len(invalid_results)}")
        logger.info(f"  - Average similarity score: {validation_report.validation_details['avg_similarity_score']:.3f}")
        logger.info(f"  - Accuracy validation passed: {accuracy_validation['accuracy_valid']}")
        logger.info(f"  - Relevance score: {relevance_metrics['relevance_score']:.3f}")

        # Test with real book content queries and verify relevance (US2)
        if len(search_result_objects) > 0:
            logger.info(f"[OK] Pipeline validation successful: {len(search_result_objects)} results returned")
            logger.info(f"[OK] Average similarity score: {validation_report.validation_details['avg_similarity_score']:.4f}")

            # Validate similarity scores are within expected range (US2)
            scores = [r.score for r in search_result_objects]
            if all(0 <= s <= 1 for s in scores):
                logger.info("[OK] All similarity scores are in expected range (0-1)")
            else:
                logger.warning("[WARN] Some similarity scores are outside expected range (0-1)")

            # Check accuracy validation results
            if accuracy_validation["accuracy_valid"]:
                logger.info("[OK] Search accuracy is above threshold")
            else:
                logger.info("[INFO] Search accuracy may be below optimal threshold")

            # Check relevance metrics
            if relevance_metrics["relevance_score"] > 0.1:  # Basic threshold for relevance
                logger.info("[OK] Content relevance is acceptable")
            else:
                logger.info("[INFO] Content relevance may be low - consider query refinement")
        else:
            logger.error("[ERROR] Pipeline validation failed: No results returned")

        # Add execution time validation (T031)
        performance_target = 5.0  # seconds
        if execution_time <= performance_target:
            logger.info(f"[OK] Performance target met: {execution_time:.3f}s <= {performance_target}s")
        else:
            logger.warning(f"[WARN] Performance target exceeded: {execution_time:.3f}s > {performance_target}s")

        # Final summary logging
        logger.info("="*60)
        logger.info("RAG RETRIEVAL VALIDATION COMPLETED")
        logger.info(f"Status: {'SUCCESS' if len(search_result_objects) > 0 else 'FAILED'}")
        logger.info(f"Total execution time: {execution_time:.3f} seconds")
        logger.info(f"Performance target (<= {performance_target}s): {'[OK] MET' if execution_time <= performance_target else '[ERROR] EXCEEDED'}")
        logger.info(f"Results returned: {len(search_result_objects)}")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"[ERROR] Error during retrieval validation: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()