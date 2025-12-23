"""
Embedding service for the RAG Chatbot API
Handles text embedding generation using Cohere API
"""
import logging
from typing import List, Union
from cohere import Client
from src.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using Cohere API
    """

    def __init__(self):
        self.client = Client(api_key=settings.COHERE_API_KEY)
        self.model = "embed-english-v3.0"  # Using Cohere's latest embedding model
        self.input_type = "search_document"  # Optimize for document search

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        """
        try:
            response = self.client.embed(
                texts=[text],
                model=self.model,
                input_type=self.input_type
            )
            embedding = response.embeddings[0]
            logger.info(f"Generated embedding for text of length {len(text)}")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        """
        try:
            # Cohere API has limits, so we'll process in batches if needed
            # For now, assuming the batch is reasonable
            response = self.client.embed(
                texts=texts,
                model=self.model,
                input_type=self.input_type
            )
            embeddings = response.embeddings
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a query (optimized for search)
        """
        try:
            response = self.client.embed(
                texts=[query],
                model=self.model,
                input_type="search_query"  # Optimize for query search
            )
            embedding = response.embeddings[0]
            logger.info(f"Generated query embedding for: {query[:50]}...")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise


# Global instance
embedding_service = EmbeddingService()