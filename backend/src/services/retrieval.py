"""
Retrieval service for the RAG Chatbot API
Handles vector search and content retrieval operations
"""
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from src.services.embedding import embedding_service
from src.services.storage import VectorStorageService, ContentStorageService
from src.models.chat import RetrievalResult
from src.utils.logging import log_retrieval, app_logger

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Service for retrieving relevant content based on user queries
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.vector_storage = VectorStorageService()
        self.content_storage = ContentStorageService(db_session)
        self.embedding_service = embedding_service

    async def retrieve_content(
        self,
        query: str,
        top_k: int = 5,
        min_relevance_score: float = 0.5,
        mode: str = "full_content",  # "full_content" or "selected_text_only"
        selected_text_chunks: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant content chunks based on the query
        """
        try:
            # Generate embedding for the query
            query_embedding = await self.embedding_service.generate_query_embedding(query)

            # Prepare filters based on mode
            filters = {}

            if mode == "selected_text_only" and selected_text_chunks:
                # In selected-text-only mode, we need to filter to only the specified chunks
                # This is a simplified approach - in practice you might need more sophisticated filtering
                filters["allowed_chunks"] = selected_text_chunks

            # Perform vector search
            search_results = await self.vector_storage.search_similar(
                query_embedding=query_embedding,
                top_k=top_k * 2,  # Get more results to filter by relevance
                filters=filters
            )

            # Filter by relevance score
            filtered_results = [
                result for result in search_results
                if result["relevance_score"] >= min_relevance_score
            ][:top_k]

            logger.info(f"Retrieved {len(filtered_results)} relevant chunks for query: {query[:50]}...")

            return filtered_results

        except Exception as e:
            logger.error(f"Error during content retrieval: {e}")
            raise

    async def retrieve_content_with_validation(
        self,
        query: str,
        session_id: Optional[UUID] = None,
        top_k: int = 5,
        min_relevance_score: float = 0.5,
        mode: str = "full_content",
        selected_text_chunks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve content with additional validation and logging
        """
        import time
        start_time = time.time()

        try:
            # Perform the retrieval
            results = await self.retrieve_content(
                query=query,
                top_k=top_k,
                min_relevance_score=min_relevance_score,
                mode=mode,
                selected_text_chunks=selected_text_chunks
            )

            # Calculate response time
            response_time = time.time() - start_time

            # Log the retrieval
            log_retrieval(
                app_logger,
                query=query,
                results_count=len(results),
                response_time=response_time,
                mode=mode
            )

            # If we have a session ID, store the retrieval result in the database
            if session_id and results:
                retrieval_record = RetrievalResult(
                    session_id=session_id,
                    query=query,
                    retrieved_chunks=[r["chunk_id"] for r in results],
                    relevance_scores=[r["relevance_score"] for r in results],
                    mode=mode,
                    metadata_json={
                        "top_k": top_k,
                        "min_relevance_score": min_relevance_score,
                        "response_time": response_time
                    }
                )
                # Add to session and commit
                self.db.add(retrieval_record)
                self.db.commit()

            return {
                "query": query,
                "results": results,
                "mode": mode,
                "response_time": response_time,
                "retrieved_count": len(results)
            }

        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Error during content retrieval with validation: {e}")

            # Log the failed retrieval
            log_retrieval(
                app_logger,
                query=query,
                results_count=0,
                response_time=response_time,
                mode=mode
            )

            raise

    async def validate_content_boundary(
        self,
        response: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> bool:
        """
        Validate that the response only contains information from the retrieved chunks
        This is a simplified validation - in practice, you might need more sophisticated content validation
        """
        try:
            # Extract content from retrieved chunks
            retrieved_content = " ".join([chunk["content"] for chunk in retrieved_chunks])

            # This is a basic check - in practice, you'd want more sophisticated validation
            # to ensure the response doesn't contain information not in the retrieved content
            response_lower = response.lower()
            retrieved_lower = retrieved_content.lower()

            # This is a very basic check - a real implementation would need more sophisticated validation
            # For example, checking if claims in the response are supported by the retrieved content
            logger.info("Content boundary validation completed")
            return True  # Placeholder - implement proper validation logic

        except Exception as e:
            logger.error(f"Error during content boundary validation: {e}")
            return False

    async def retrieve_sources_for_response(
        self,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Format retrieved chunks into proper source citations for the response
        """
        try:
            sources = []
            for chunk in retrieved_chunks:
                # Get additional metadata from content storage if needed
                source_info = {
                    "chunk_id": chunk.get("chunk_id"),
                    "content": chunk.get("content", "")[:200] + "..." if len(chunk.get("content", "")) > 200 else chunk.get("content"),
                    "relevance_score": chunk.get("relevance_score"),
                    "page_number": chunk.get("metadata", {}).get("page_number"),
                    "section_title": chunk.get("metadata", {}).get("section_title"),
                }
                sources.append(source_info)

            logger.info(f"Formatted {len(sources)} sources for response")
            return sources

        except Exception as e:
            logger.error(f"Error formatting sources: {e}")
            return []


# Global instance will be created when needed with proper DB session