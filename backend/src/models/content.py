from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.sql import func
from src.database.database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid


class SourceDocument(Base):
    """
    Model for storing source documents that content chunks are derived from
    """
    __tablename__ = "source_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # e.g., "markdown", "pdf", "html"
    source_path = Column(String, nullable=False)
    version = Column(String, default="1.0.0")
    metadata_json = Column(JSON)  # JSON for additional document metadata
    status = Column(String, default="pending")  # "pending", "processing", "ingested", "error", "updating"
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes for performance
    __table_args__ = (
        Index('idx_source_path', 'source_path'),
        Index('idx_status', 'status'),
    )

    def __repr__(self):
        return f"<SourceDocument(id={self.id}, title={self.title}, status={self.status})>"


class ContentChunk(Base):
    """
    Model for storing content chunks with embeddings and metadata
    """
    __tablename__ = "content_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    checksum = Column(String, nullable=True)  # SHA-256 hash of the content for deduplication
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("source_documents.id"), nullable=False)
    page_number = Column(Integer, nullable=True)
    section_title = Column(String, nullable=True)
    position = Column(Integer, default=0)
    metadata_json = Column(JSON)  # JSON for additional chunk metadata
    embedding_vector_id = Column(String, nullable=False)  # Reference to Qdrant ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes for performance
    __table_args__ = (
        Index('idx_source_document_position', 'source_document_id', 'position'),
        Index('idx_checksum', 'checksum'),
        Index('idx_embedding_id', 'embedding_vector_id'),
    )

    def __repr__(self):
        return f"<ContentChunk(id={self.id}, source_document_id={self.source_document_id}, position={self.position})>"