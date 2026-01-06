import cohere
from typing import List, Optional
from src.models.document_chunk import DocumentChunk
from src.config.settings import settings
import logging
import time
from requests.exceptions import RequestException
import cohere
import random


class EmbeddingGenerator:
    """
    Service for generating vector embeddings using Cohere API
    """

    def __init__(self):
        self.client = cohere.Client(settings.cohere_api_key)
        self.logger = logging.getLogger(__name__)
        # Define available embedding models with their characteristics
        self.embedding_models = {
            'embed-multilingual-v2.0': {
                'dimensions': 768,
                'input_type': 'search_document',
                'description': 'Multilingual v2.0 model with 768 dimensions'
            },
            'embed-english-v3.0': {
                'dimensions': 1024,
                'input_type': 'search_document',
                'description': 'English v3.0 model with 1024 dimensions'
            }
        }
        # Default model
        self.default_model = 'embed-multilingual-v2.0'

    def _make_request_with_retry(self, func, *args, **kwargs):
        """
        Make a request with retry logic for API failures
        """
        last_exception = None

        for attempt in range(settings.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                last_exception = e

                # Check if it's a rate limit error and wait accordingly
                error_str = str(e)
                if "Too Many Requests" in error_str or "429" in error_str:
                    # Use a more conservative exponential backoff with jitter to avoid thundering herd
                    base_wait = settings.min_retry_delay
                    exponential_factor = 2 ** attempt
                    calculated_wait = base_wait * exponential_factor
                    # Cap at max_retry_delay seconds
                    max_wait_time = min(settings.max_retry_delay, calculated_wait)
                    # Add jitter to prevent synchronized retries
                    jitter = random.uniform(0.5, 1.0)
                    wait_time = max_wait_time * jitter
                    self.logger.info(f"Rate limited, waiting {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                elif attempt < settings.max_retries - 1:
                    # For other errors, wait before retrying with jitter
                    base_wait = settings.min_retry_delay * 2
                    exponential_factor = 2 ** attempt
                    calculated_wait = base_wait * exponential_factor
                    max_wait_time = min(settings.max_retry_delay / 2, calculated_wait)  # Use half the max for other errors
                    jitter = random.uniform(0.5, 1.0)
                    wait_time = max_wait_time * jitter
                    time.sleep(wait_time)

        # If all retries failed, log and return None
        self.logger.error(f"All {settings.max_retries} attempts failed. Last error: {str(last_exception)}")
        return None

    def generate_embedding(self, text: str, model: str = None) -> Optional[List[float]]:
        """
        Generate a single embedding for the provided text

        Args:
            text: The text to generate an embedding for
            model: The embedding model to use (optional, defaults to configured default)

        Returns:
            List of floats representing the embedding, or None if generation fails
        """
        if model is None:
            model = self.default_model

        model_config = self.embedding_models.get(model, self.embedding_models[self.default_model])

        def _embed_func():
            return self.client.embed(
                texts=[text],
                model=model,
                input_type=model_config['input_type']  # Specify the input type for better embeddings
            )

        response = self._make_request_with_retry(_embed_func)
        if response is None:
            return None

        return response.embeddings[0]  # Return the first (and only) embedding

    def generate_embeddings_batch(self, texts: List[str], model: str = None) -> Optional[List[List[float]]]:
        """
        Generate embeddings for a batch of texts

        Args:
            texts: List of texts to generate embeddings for
            model: The embedding model to use (optional, defaults to configured default)

        Returns:
            List of embeddings (each embedding is a list of floats), or None if generation fails
        """
        if model is None:
            model = self.default_model

        model_config = self.embedding_models.get(model, self.embedding_models[self.default_model])

        if not texts:
            return []

        def _embed_batch_func():
            # Cohere API has limits on batch size, so we'll process in chunks if needed
            max_batch_size = 96  # Cohere's limit is typically 96 texts per request
            all_embeddings = []

            for i in range(0, len(texts), max_batch_size):
                batch = texts[i:i + max_batch_size]
                response = self.client.embed(
                    texts=batch,
                    model=model,
                    input_type=model_config['input_type']
                )
                all_embeddings.extend(response.embeddings)

            return all_embeddings

        result = self._make_request_with_retry(_embed_batch_func)
        return result

    def generate_embeddings_batch_with_rate_limit_handling(self, texts: List[str],
                                                          model: str = None,
                                                          max_batch_size: int = 96,
                                                          delay_between_batches: float = 0.1) -> Optional[List[List[float]]]:
        """
        Generate embeddings for a batch of texts with enhanced rate limit handling.
        Processes texts in smaller batches with delays to prevent hitting rate limits.

        Args:
            texts: List of texts to generate embeddings for
            model: The embedding model to use (optional, defaults to configured default)
            max_batch_size: Maximum number of texts per API call (default 96 for Cohere)
            delay_between_batches: Delay in seconds between batches to avoid rate limits

        Returns:
            List of embeddings (each embedding is a list of floats), or None if generation fails
        """
        if model is None:
            model = self.default_model

        model_config = self.embedding_models.get(model, self.embedding_models[self.default_model])

        if not texts:
            return []

        all_embeddings = []

        for i in range(0, len(texts), max_batch_size):
            batch = texts[i:i + max_batch_size]

            # Try to generate embeddings for this batch
            def _embed_single_batch():
                response = self.client.embed(
                    texts=batch,
                    model=model,
                    input_type=model_config['input_type']
                )
                return response.embeddings

            batch_embeddings = self._make_request_with_retry(_embed_single_batch)

            if batch_embeddings is None:
                self.logger.error(f"Failed to generate embeddings for batch starting at index {i}")
                return None

            all_embeddings.extend(batch_embeddings)

            # Add delay between batches to prevent rate limiting
            if i + max_batch_size < len(texts) and delay_between_batches > 0:
                time.sleep(delay_between_batches)

        return all_embeddings

    def generate_embeddings_for_chunks(self, chunks: List[DocumentChunk], model: str = None) -> bool:
        """
        Generate embeddings for a list of document chunks in-place

        Args:
            chunks: List of DocumentChunk objects to generate embeddings for
            model: The embedding model to use (optional, defaults to configured default)

        Returns:
            True if successful, False otherwise
        """
        if not chunks:
            return True

        # Extract text content from chunks
        texts = [chunk.content for chunk in chunks]

        # Generate embeddings using the rate limit handling approach
        embeddings = self.generate_embeddings_batch_with_rate_limit_handling(texts, model=model)
        if embeddings is None:
            # Try with a fallback model if the default one failed
            fallback_model = 'embed-english-v3.0' if self.default_model == 'embed-multilingual-v2.0' else 'embed-multilingual-v2.0'
            self.logger.info(f"Default model failed, trying fallback model: {fallback_model}")
            embeddings = self.generate_embeddings_batch_with_rate_limit_handling(texts, model=fallback_model)
            if embeddings is None:
                return False

        # Assign embeddings back to chunks
        for i, chunk in enumerate(chunks):
            if i < len(embeddings):  # Safety check
                chunk.embedding = embeddings[i]

        return True

    def validate_embedding(self, embedding: List[float], expected_dimension: int = 768) -> bool:
        """
        Validate that an embedding has the correct dimensions

        Args:
            embedding: The embedding to validate
            expected_dimension: Expected number of dimensions (default for Cohere is 768)

        Returns:
            True if valid, False otherwise
        """
        if not embedding:
            return False

        return len(embedding) == expected_dimension