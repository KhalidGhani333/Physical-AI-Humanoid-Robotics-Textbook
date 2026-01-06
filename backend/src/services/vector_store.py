from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import List, Optional
from src.config.settings import settings
from src.models.document_chunk import DocumentChunk
from src.models.embedding import EmbeddingVector
import logging


class VectorStore:
    """
    Service for storing and retrieving embeddings in Qdrant Cloud
    """

    def __init__(self, use_mock=False):
        self.use_mock = use_mock
        if not use_mock:
            # Initialize Qdrant client with cloud configuration
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
                timeout=30
            )
            self.collection_name = settings.qdrant_collection_name
        else:
            # For testing purposes, we'll use an in-memory Qdrant client
            from qdrant_client.local.qdrant_local import QdrantLocal
            self.client = QdrantLocal(location=":memory:")
            self.collection_name = "test_collection"

        self.logger = logging.getLogger(__name__)
        if not use_mock:  # Only initialize collection if not using mock
            self._initialize_collection()
        else:
            # Create collection for testing
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=768,  # Size for Cohere embeddings (most common)
                    distance=models.Distance.COSINE
                )
            )

    def _initialize_collection(self):
        """
        Initialize the Qdrant collection with appropriate vector dimensions
        """
        # For Cohere embeddings, we'll use 768 dimensions (for the model being used)
        # This may need to be adjusted based on the specific Cohere model used
        vector_size = 768  # Size for Cohere embeddings (most common)

        try:
            # Check if collection exists
            self.client.get_collection(self.collection_name)
        except Exception as e:
            self.logger.warning(f"Collection {self.collection_name} does not exist, creating it: {str(e)}")
            # Create collection if it doesn't exist
            try:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE
                    )
                )
                self.logger.info(f"Successfully created collection {self.collection_name}")
            except Exception as create_error:
                self.logger.error(f"Failed to create collection {self.collection_name}: {str(create_error)}")
                raise create_error

    def store_embedding(self, document_chunk: DocumentChunk) -> bool:
        """
        Store a document chunk with its embedding in Qdrant

        Args:
            document_chunk: The document chunk to store

        Returns:
            True if successfully stored, False otherwise
        """
        try:
            if not document_chunk.embedding:
                raise ValueError("Document chunk must have an embedding to store")

            # Prepare payload with metadata
            payload = {
                "document_id": document_chunk.document_id,
                "source_url": document_chunk.source_url,
                "chunk_index": document_chunk.chunk_index,
                "content": document_chunk.content,
                "created_at": document_chunk.created_at.isoformat(),
                "updated_at": document_chunk.updated_at.isoformat()
            }

            # Store in Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=document_chunk.id,
                        vector=document_chunk.embedding,
                        payload=payload
                    )
                ]
            )
            return True
        except Exception as e:
            self.logger.error(f"Error storing embedding: {str(e)}")
            return False

    def store_embeddings_batch(self, document_chunks: List[DocumentChunk]) -> int:
        """
        Store multiple document chunks in a batch operation

        Args:
            document_chunks: List of document chunks to store

        Returns:
            Number of successfully stored chunks
        """
        successful_count = 0
        points = []

        for chunk in document_chunks:
            if not chunk.embedding:
                continue

            payload = {
                "document_id": chunk.document_id,
                "source_url": chunk.source_url,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "created_at": chunk.created_at.isoformat(),
                "updated_at": chunk.updated_at.isoformat()
            }

            point = models.PointStruct(
                id=chunk.id,
                vector=chunk.embedding,
                payload=payload
            )
            points.append(point)

        try:
            if points:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                successful_count = len(points)
        except Exception as e:
            self.logger.error(f"Error storing embeddings batch: {str(e)}")

        return successful_count

    def search_similar(self, query_embedding: List[float], limit: int = 10) -> List[DocumentChunk]:
        """
        Search for similar content using vector similarity

        Args:
            query_embedding: The embedding vector to search for similarity
            limit: Maximum number of results to return

        Returns:
            List of similar document chunks
        """
        # Try the search method first (most common in Qdrant versions)
        fallback_methods = ['search', 'query', 'search_points', 'query_points', 'retrieve']

        for method_name in fallback_methods:
            if hasattr(self.client, method_name):
                try:
                    search_method = getattr(self.client, method_name)

                    # Different methods may have different signatures
                    if method_name == 'search':
                        search_results = search_method(
                            collection_name=self.collection_name,
                            query_vector=query_embedding,
                            limit=limit
                        )
                    elif method_name == 'query':
                        # For query method, try different approaches
                        try:
                            # First try with query parameter
                            search_results = search_method(
                                collection_name=self.collection_name,
                                query=query_embedding,
                                limit=limit
                            )
                        except TypeError:
                            # If that fails, try with query_vector
                            search_results = search_method(
                                collection_name=self.collection_name,
                                query_vector=query_embedding,
                                limit=limit
                            )
                    elif method_name == 'search_points':
                        search_results = search_method(
                            collection_name=self.collection_name,
                            query_vector=query_embedding,
                            limit=limit
                        )
                    elif method_name == 'query_points':
                        search_results = search_method(
                            collection_name=self.collection_name,
                            query=query_embedding,
                            limit=limit
                        )
                    elif method_name == 'retrieve':
                        # For retrieve, we might need IDs instead of similarity search
                        # This is not the same as search, so skip it for similarity search
                        continue
                    else:
                        # Generic approach
                        search_results = search_method(
                            collection_name=self.collection_name,
                            query_vector=query_embedding,
                            limit=limit
                        )

                    # Process results based on the method used
                    document_chunks = []
                    if hasattr(search_results, '__iter__'):
                        for result in search_results:
                            if hasattr(result, 'payload'):
                                payload = result.payload
                                chunk = DocumentChunk(
                                    id=getattr(result, 'id', 'unknown'),
                                    document_id=payload.get("document_id"),
                                    source_url=payload.get("source_url"),
                                    chunk_index=payload.get("chunk_index"),
                                    content=payload.get("content"),
                                    embedding=query_embedding,
                                    created_at=payload.get("created_at"),
                                    updated_at=payload.get("updated_at")
                                )
                                document_chunks.append(chunk)
                    else:
                        # If it's a response object with points attribute
                        points = getattr(search_results, 'points', [])
                        for result in points:
                            if hasattr(result, 'payload'):
                                payload = result.payload
                                chunk = DocumentChunk(
                                    id=getattr(result, 'id', 'unknown'),
                                    document_id=payload.get("document_id"),
                                    source_url=payload.get("source_url"),
                                    chunk_index=payload.get("chunk_index"),
                                    content=payload.get("content"),
                                    embedding=query_embedding,
                                    created_at=payload.get("created_at"),
                                    updated_at=payload.get("updated_at")
                                )
                                document_chunks.append(chunk)

                    self.logger.info(f"Successfully used method '{method_name}' for search")
                    return document_chunks
                except Exception as method_error:
                    self.logger.debug(f"Method {method_name} failed: {str(method_error)}")
                    continue  # Try next method

        # If all methods fail, return empty results
        self.logger.error("All search/query methods failed")
        return []

    def get_by_source_url(self, source_url: str) -> List[DocumentChunk]:
        """
        Retrieve all chunks from a specific source URL

        Args:
            source_url: The source URL to filter by

        Returns:
            List of document chunks from the specified source URL
        """
        try:
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="source_url",
                            match=models.MatchValue(value=source_url)
                        )
                    ]
                )
            )

            document_chunks = []
            for point in results[0]:  # Results come as (points, next_page_offset)
                payload = point.payload
                chunk = DocumentChunk(
                    id=point.id,
                    document_id=payload.get("document_id"),
                    source_url=payload.get("source_url"),
                    chunk_index=payload.get("chunk_index"),
                    content=payload.get("content"),
                    embedding=point.vector,
                    created_at=payload.get("created_at"),
                    updated_at=payload.get("updated_at")
                )
                document_chunks.append(chunk)

            return document_chunks
        except Exception as e:
            self.logger.error(f"Error retrieving chunks by source URL: {str(e)}")
            return []

    def health_check(self) -> bool:
        """
        Check if the Qdrant connection is healthy

        Returns:
            True if the connection is healthy, False otherwise
        """
        try:
            # Try to get collection info to verify connection
            self.client.get_collection(self.collection_name)
            return True
        except Exception as e:
            self.logger.error(f"Qdrant health check failed: {str(e)}")
            return False