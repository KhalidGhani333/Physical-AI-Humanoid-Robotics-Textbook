from typing import List, Optional
import os

from src.models.document_chunk import DocumentChunk
from src.services.embedding_generator import EmbeddingGenerator
from src.services.vector_store import VectorStore
from src.config.settings import settings
import logging
import time


class RetrievalService:
    """
    Service for retrieving relevant content from vector store based on semantic similarity
    """

    def __init__(self, vector_store: VectorStore = None, embedding_generator: EmbeddingGenerator = None):
        self.vector_store = vector_store or VectorStore()
        self.embedding_generator = embedding_generator or EmbeddingGenerator()
        self.logger = logging.getLogger(__name__)

    def search(self, query: str, top_k: int = 5, min_similarity: float = 0.5) -> List[DocumentChunk]:
        """
        Search for relevant document chunks based on query

        Args:
            query: The search query string
            top_k: Number of top results to return (default 5)
            min_similarity: Minimum similarity threshold (default 0.5)

        Returns:
            List of relevant DocumentChunk objects
        """
        start_time = time.time()
        self.logger.info(f"Starting retrieval for query: {query[:100]}...")

        # Generate embedding for the query
        query_embedding = self.embedding_generator.generate_embedding(query)
        if not query_embedding:
            self.logger.error("Failed to generate embedding for query")
            return []

        # Validate embedding dimensions
        if not self.embedding_generator.validate_embedding(query_embedding):
            self.logger.error(f"Invalid embedding dimensions: expected 768, got {len(query_embedding) if query_embedding else 'None'}")
            return []

        # Search in vector store
        results = self.vector_store.search_similar(query_embedding, limit=top_k)

        # Filter by minimum similarity if needed (this is a basic filter based on Qdrant's scoring)
        filtered_results = []
        for result in results:
            # Note: In a real implementation, we would have access to similarity scores
            # For now, we'll return all results from Qdrant which are already ranked
            filtered_results.append(result)

        search_time = time.time() - start_time
        self.logger.info(f"Retrieved {len(filtered_results)} results in {search_time:.2f} seconds")

        return filtered_results

    def validate_retrieval_quality(self, query: str, expected_keywords: List[str] = None) -> dict:
        """
        Validate the quality of retrieval for a given query

        Args:
            query: The search query
            expected_keywords: Optional list of keywords that should appear in results

        Returns:
            Dictionary with validation metrics
        """
        results = self.search(query, top_k=10)  # Get more results for validation

        validation_metrics = {
            "query": query,
            "num_results": len(results),
            "has_content": len(results) > 0,
            "avg_content_length": sum(len(chunk.content) for chunk in results) / len(results) if results else 0,
            "content_keywords_present": 0
        }

        if expected_keywords:
            keyword_matches = 0
            for result in results:
                content_lower = result.content.lower()
                for keyword in expected_keywords:
                    if keyword.lower() in content_lower:
                        keyword_matches += 1
                        break  # Count each result only once
            validation_metrics["content_keywords_present"] = keyword_matches

        return validation_metrics

    def get_relevant_chunks(self, query: str, top_k: int = 5) -> List[dict]:
        """
        Get relevant chunks with additional metadata for response

        Args:
            query: The search query
            top_k: Number of top results to return

        Returns:
            List of dictionaries with chunk data and metadata
        """
        results = self.search(query, top_k=top_k)

        chunk_data = []
        for result in results:
            chunk_data.append({
                "id": result.id,
                "content": result.content,
                "source_url": result.source_url,
                "chunk_index": result.chunk_index,
                "document_id": result.document_id,
                "relevance_score": getattr(result, 'relevance_score', 0.0)  # Placeholder - Qdrant scoring would go here
            })

        return chunk_data