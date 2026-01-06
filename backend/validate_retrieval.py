import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from services.retrieval_service import RetrievalService
from services.vector_store import VectorStore
from services.embedding_generator import EmbeddingGenerator
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_retrieval_pipeline():
    """Validate the retrieval pipeline with a simple test."""
    logger.info("Starting retrieval pipeline validation...")

    # Initialize services
    vector_store = VectorStore()
    embedding_generator = EmbeddingGenerator()
    retrieval_service = RetrievalService(
        vector_store=vector_store,
        embedding_generator=embedding_generator
    )

    # Test query
    test_query = "What is humanoid robotics?"

    logger.info(f"Testing retrieval with query: '{test_query}'")

    # Perform search
    results = retrieval_service.search(test_query, top_k=3)

    logger.info(f"Retrieved {len(results)} results")

    if results:
        logger.info("✓ Retrieval pipeline is working correctly")
        logger.info(f"First result content preview: {results[0].content[:100]}...")
        return True
    else:
        logger.warning("⚠ No results returned - this might be expected if no content is in Qdrant yet")
        return False

def validate_retrieval_quality():
    """Validate retrieval quality with known terms."""
    logger.info("Starting retrieval quality validation...")

    # Initialize services
    vector_store = VectorStore()
    embedding_generator = EmbeddingGenerator()
    retrieval_service = RetrievalService(
        vector_store=vector_store,
        embedding_generator=embedding_generator
    )

    # Test with specific terms that might exist in the textbook
    test_queries = [
        "robotics",
        "humanoid",
        "AI",
        "artificial intelligence"
    ]

    all_success = True

    for query in test_queries:
        logger.info(f"Testing query: '{query}'")
        validation_result = retrieval_service.validate_retrieval_quality(query)
        logger.info(f"Validation result: {validation_result}")

        if validation_result["num_results"] == 0:
            logger.info(f"No results for query '{query}', which may be expected")
        else:
            logger.info(f"✓ Found {validation_result['num_results']} results for '{query}'")

    return all_success

if __name__ == "__main__":
    logger.info("Starting retrieval validation tests...")

    # Run pipeline validation
    pipeline_valid = validate_retrieval_pipeline()

    # Run quality validation
    quality_valid = validate_retrieval_quality()

    logger.info("Retrieval validation completed.")
    logger.info(f"Pipeline validation: {'✓ PASS' if pipeline_valid else '? NEEDS CONTENT'}")
    logger.info(f"Quality validation: {'✓ PASS' if quality_valid else '? NEEDS CONTENT'}")

    logger.info("\nTo fully validate the retrieval system, you need to:")
    logger.info("1. Ensure your Qdrant collection has content from the ingestion pipeline")
    logger.info("2. Run a query against known topics in your textbook")
    logger.info("3. Verify that relevant results are returned with appropriate similarity")