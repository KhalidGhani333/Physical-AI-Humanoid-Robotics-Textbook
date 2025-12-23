"""
Storage service for the RAG Chatbot API
Handles both vector storage (Qdrant) and relational storage (PostgreSQL)
"""
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
import json

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from sqlalchemy.orm import Session

from src.database.database import qdrant_client
from src.models.content import ContentChunk, SourceDocument
from src.models.conversation import ConversationSession
from src.models.chat import ChatMessage, RetrievalResult

logger = logging.getLogger(__name__)


class VectorStorageService:
    """
    Service for handling vector storage operations in Qdrant
    """

    def __init__(self):
        self.client = qdrant_client

    async def store_embedding(self,
                             chunk_id: str,
                             embedding: List[float],
                             content: str,
                             metadata: Dict[str, Any] = None) -> bool:
        """
        Store a content chunk with its embedding in Qdrant
        """
        try:
            # Prepare payload with content and metadata
            payload = {
                "content": content,
                "chunk_id": chunk_id
            }
            if metadata:
                payload.update(metadata)

            # Store in Qdrant
            self.client.upsert(
                collection_name="content_chunks",
                points=[
                    models.PointStruct(
                        id=chunk_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            logger.info(f"Successfully stored embedding for chunk {chunk_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store embedding for chunk {chunk_id}: {e}")
            return False

    async def search_similar(self,
                           query_embedding: List[float],
                           top_k: int = 5,
                           filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search for similar content chunks based on embedding similarity
        """
        try:
            # Prepare filters if provided
            qdrant_filters = None
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    filter_conditions.append(
                        models.FieldCondition(
                            key=f"metadata.{key}",
                            match=models.MatchValue(value=value)
                        )
                    )

                if filter_conditions:
                    qdrant_filters = models.Filter(
                        must=filter_conditions
                    )

            # Perform search
            search_results = self.client.search(
                collection_name="content_chunks",
                query_vector=query_embedding,
                limit=top_k,
                query_filter=qdrant_filters
            )

            # Format results
            results = []
            for hit in search_results:
                results.append({
                    "chunk_id": hit.payload.get("chunk_id"),
                    "content": hit.payload.get("content"),
                    "relevance_score": hit.score,
                    "metadata": hit.payload
                })

            logger.info(f"Found {len(results)} similar chunks for query")
            return results
        except Exception as e:
            logger.error(f"Failed to search similar chunks: {e}")
            return []

    async def delete_embedding(self, chunk_id: str) -> bool:
        """
        Delete an embedding from Qdrant
        """
        try:
            self.client.delete(
                collection_name="content_chunks",
                points_selector=models.PointIdsList(
                    points=[chunk_id]
                )
            )
            logger.info(f"Successfully deleted embedding for chunk {chunk_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete embedding for chunk {chunk_id}: {e}")
            return False


class ContentStorageService:
    """
    Service for handling content storage operations in PostgreSQL
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def create_source_document(self,
                             title: str,
                             source_type: str,
                             source_path: str,
                             metadata: Dict[str, Any] = None) -> SourceDocument:
        """
        Create a new source document record
        """
        try:
            document = SourceDocument(
                title=title,
                source_type=source_type,
                source_path=source_path,
                metadata_json=metadata or {},
                status="processing"
            )
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)

            logger.info(f"Created source document: {document.id}")
            return document
        except Exception as e:
            logger.error(f"Failed to create source document: {e}")
            self.db.rollback()
            raise

    def update_document_status(self, document_id: UUID, status: str, chunk_count: int = None) -> SourceDocument:
        """
        Update the status of a source document
        """
        try:
            document = self.db.query(SourceDocument).filter(SourceDocument.id == document_id).first()
            if not document:
                raise ValueError(f"Document with ID {document_id} not found")

            document.status = status
            if chunk_count is not None:
                document.chunk_count = chunk_count
            document.updated_at = self.db.query(SourceDocument).filter(SourceDocument.id == document_id).value(SourceDocument.updated_at)

            self.db.commit()
            self.db.refresh(document)

            logger.info(f"Updated document {document_id} status to {status}")
            return document
        except Exception as e:
            logger.error(f"Failed to update document {document_id} status: {e}")
            self.db.rollback()
            raise

    def create_content_chunk(self,
                           content: str,
                           source_document_id: UUID,
                           embedding_vector_id: str,
                           position: int = 0,
                           metadata: Dict[str, Any] = None,
                           page_number: int = None,
                           section_title: str = None) -> ContentChunk:
        """
        Create a new content chunk record
        """
        try:
            chunk = ContentChunk(
                content=content,
                source_document_id=source_document_id,
                embedding_vector_id=embedding_vector_id,
                position=position,
                metadata_json=metadata or {},
                page_number=page_number,
                section_title=section_title
            )
            self.db.add(chunk)
            self.db.commit()
            self.db.refresh(chunk)

            logger.info(f"Created content chunk: {chunk.id}")
            return chunk
        except Exception as e:
            logger.error(f"Failed to create content chunk: {e}")
            self.db.rollback()
            raise

    def get_content_chunks_by_document(self, document_id: UUID) -> List[ContentChunk]:
        """
        Get all content chunks for a specific document
        """
        try:
            chunks = self.db.query(ContentChunk).filter(
                ContentChunk.source_document_id == document_id
            ).order_by(ContentChunk.position).all()

            logger.info(f"Retrieved {len(chunks)} chunks for document {document_id}")
            return chunks
        except Exception as e:
            logger.error(f"Failed to retrieve chunks for document {document_id}: {e}")
            return []

    def get_source_document(self, document_id: UUID) -> SourceDocument:
        """
        Get a source document by ID
        """
        try:
            document = self.db.query(SourceDocument).filter(SourceDocument.id == document_id).first()

            if document:
                logger.info(f"Retrieved source document: {document_id}")
            else:
                logger.warning(f"Source document not found: {document_id}")

            return document
        except Exception as e:
            logger.error(f"Failed to retrieve source document {document_id}: {e}")
            return None


# Global instances
vector_storage_service = VectorStorageService()