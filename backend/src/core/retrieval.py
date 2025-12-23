import asyncio
import logging
from typing import List, Dict, Any, Optional
from src.database.database import qdrant_client
from qdrant_client.http import models
from src.config import settings
import cohere
from operator import itemgetter

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self):
        self.cohere_client = None
        if settings.COHERE_API_KEY:
            try:
                self.cohere_client = cohere.Client(settings.COHERE_API_KEY)
                logger.info("Cohere client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Cohere client: {str(e)}")
                logger.warning("Cohere functionality will be limited")
                self.cohere_client = None
        else:
            logger.info("COHERE_API_KEY not set - retrieval will use fallback methods")

    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for the query using Cohere
        """
        if not self.cohere_client:
            logger.warning("Cohere client not available - cannot generate embeddings")
            # Return None to indicate that embeddings can't be generated
            return None

        try:
            response = self.cohere_client.embed(
                texts=[query],
                model='embed-english-v3.0',
                input_type="search_query"  # Specify input type for query
            )
            return response.embeddings[0]  # Return first (and only) embedding
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            # Return None to indicate failure
            return None

    async def search_content(self, query: str, top_k: int = 5,
                            document_ids: Optional[List[str]] = None,
                            selected_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant content based on the query
        """
        logger.info(f"Searching for query: '{query[:50]}...' with top_k={top_k}")

        # Generate query embedding
        query_embedding = await self.generate_query_embedding(query)

        # If we can't generate embeddings, return empty results
        # since meaningful similarity search isn't possible without embeddings
        if query_embedding is None:
            logger.warning("Could not generate embeddings - returning empty results")
            return []

        # Prepare filters
        filters = []

        if document_ids:
            # Filter by specific documents
            filters.append(
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchAny(any=document_ids)
                )
            )

        if selected_text:
            # If selected text is provided, we'll search within it specifically
            # For now, we'll use it as an additional filter
            # In a real implementation, we might want to use it differently
            pass

        # Create filter condition
        filter_condition = None
        if filters:
            if len(filters) == 1:
                filter_condition = models.Filter(must=[filters[0]])
            else:
                filter_condition = models.Filter(must=filters)

        # Perform search in Qdrant - using the correct API based on Qdrant version
        try:
            # Check if the newer query_points API is available (newer versions)
            if hasattr(qdrant_client, 'query_points'):
                search_results = qdrant_client.query_points(
                    collection_name="content_chunks",
                    query=query_embedding,
                    using="content",  # Specify the vector field name
                    query_filter=filter_condition,
                    limit=top_k,
                    with_payload=True,
                    with_vectors=False
                )
                # Convert to expected format for newer API
                search_results = search_results.points
            else:
                # Fallback to older search API
                search_results = qdrant_client.search(
                    collection_name="content_chunks",
                    query_vector=("content", query_embedding),  # Specify the named vector and embedding
                    query_filter=filter_condition,
                    limit=top_k,
                    with_payload=True,
                    with_vectors=False
                )
        except Exception as e:
            logger.warning(f"Qdrant search failed: {str(e)}. Returning empty results.")
            # Return empty results if Qdrant is unavailable
            search_results = []

        # Process results
        results = []

        # Handle results based on API version
        for hit in search_results:
            # Check if this is from the newer query_points API or older search API
            if hasattr(hit, 'payload') and hit.payload is not None:
                # This is from the newer API format
                result = {
                    "id": hit.id,
                    "content": hit.payload.get("content", "") if hit.payload else "",
                    "document_id": hit.payload.get("document_id", "") if hit.payload else "",
                    "chunk_index": hit.payload.get("chunk_index", 0) if hit.payload else 0,
                    "source_url": hit.payload.get("source_url", "") if hit.payload else "",
                    "metadata": hit.payload.get("metadata", {}) if hit.payload else {},
                    "score": getattr(hit, 'score', 0)
                }
            else:
                # This might be from an older API format
                result = {
                    "id": getattr(hit, 'id', ''),
                    "content": getattr(hit, 'payload', {}).get("content", "") if hasattr(hit, 'payload') else "",
                    "document_id": getattr(hit, 'payload', {}).get("document_id", "") if hasattr(hit, 'payload') else "",
                    "chunk_index": getattr(hit, 'payload', {}).get("chunk_index", 0) if hasattr(hit, 'payload') else 0,
                    "source_url": getattr(hit, 'payload', {}).get("source_url", "") if hasattr(hit, 'payload') else "",
                    "metadata": getattr(hit, 'payload', {}).get("metadata", {}) if hasattr(hit, 'payload') else {},
                    "score": getattr(hit, 'score', 0)
                }
            results.append(result)

        logger.info(f"Found {len(results)} results for query")
        return results

    async def retrieve_and_rerank(self, query: str, top_k: int = 5,
                                 document_ids: Optional[List[str]] = None,
                                 selected_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve results and rerank them for better relevance
        """
        # Get initial results
        initial_results = await self.search_content(
            query=query,
            top_k=top_k * 2,  # Get more results for reranking
            document_ids=document_ids,
            selected_text=selected_text
        )

        if not initial_results:
            return []

        # If Cohere client is not available, return results without reranking
        if not self.cohere_client:
            logger.info("Cohere client not available - skipping reranking")
            # Return results sorted by initial score
            return sorted(initial_results, key=lambda x: x["score"], reverse=True)[:top_k]

        # Extract text contents for reranking
        texts = [result["content"] for result in initial_results]

        try:
            # Use Cohere's rerank functionality
            rerank_response = self.cohere_client.rerank(
                query=query,
                documents=texts,
                top_n=top_k
            )

            # Map reranked results back to original data
            reranked_results = []
            for idx, result in enumerate(rerank_response.results):
                original_result = initial_results[result.index]
                original_result["rerank_score"] = result.relevance_score
                original_result["rerank_position"] = idx + 1
                reranked_results.append(original_result)

            return reranked_results

        except Exception as e:
            logger.warning(f"Reranking failed, returning original results: {str(e)}")
            # If reranking fails, return the original results sorted by initial score
            return sorted(initial_results, key=lambda x: x["score"], reverse=True)[:top_k]

    async def enforce_content_boundaries(self, results: List[Dict[str, Any]],
                                       selected_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Enforce content boundaries by filtering results to only include those
        that are relevant to the selected text (if provided)
        """
        if not selected_text:
            # No boundary enforcement needed
            return results

        logger.info("Enforcing content boundaries based on selected text")

        # In selected text mode, we only want results that are highly relevant to the selected text
        filtered_results = []
        for result in results:
            content = result["content"]
            # Check if the content chunk has significant overlap with selected text
            # This is a simple implementation - in practice, you might want more sophisticated matching
            if self._is_relevant_to_selected_text(content, selected_text):
                filtered_results.append(result)

        logger.info(f"Content boundary enforcement: {len(results)} -> {len(filtered_results)} results")
        return filtered_results

    def _is_relevant_to_selected_text(self, content: str, selected_text: str) -> bool:
        """
        Check if content is relevant to selected text (simple keyword matching)
        """
        # Convert to lowercase for comparison
        content_lower = content.lower()
        selected_lower = selected_text.lower()

        # Check for significant overlap - this is a simple heuristic
        selected_words = set(selected_lower.split())
        content_words = set(content_lower.split())

        if not selected_words:
            return True  # If no selected text, accept all

        # Calculate overlap percentage
        intersection = selected_words.intersection(content_words)
        if len(intersection) == 0:
            return False

        overlap_percentage = len(intersection) / len(selected_words)
        return overlap_percentage >= 0.1  # At least 10% overlap