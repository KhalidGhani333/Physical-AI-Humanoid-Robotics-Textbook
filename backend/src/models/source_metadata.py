from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class SourceMetadata(BaseModel):
    """
    Information that tracks the origin of content including document_id, source_url, and chunk_index for traceability and filtering
    """
    document_id: str  # Unique identifier for the source document
    source_url: str  # Original URL where content was found
    title: Optional[str] = None  # Title of the source document (if available)
    author: Optional[str] = None  # Author of the source document (if available)
    published_date: Optional[datetime] = None  # Date when the source was published (if available)
    crawl_timestamp: Optional[datetime] = datetime.now()  # When the content was crawled
    content_hash: Optional[str] = None  # Hash of the content for duplicate detection
    status: str = "pending"  # Status of the ingestion (e.g., "processed", "failed", "pending")

    @field_validator('document_id')
    def validate_document_id(cls, v):
        if not v or v.strip() == "":
            raise ValueError('document_id must not be empty')
        return v

    @field_validator('source_url')
    def validate_source_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('source_url must be a valid URL format')
        return v

    @field_validator('status')
    def validate_status(cls, v):
        valid_statuses = ['pending', 'processed', 'failed', 'running']
        if v not in valid_statuses:
            raise ValueError(f'status must be one of {valid_statuses}')
        return v

    @field_validator('content_hash')
    def validate_content_hash(cls, v):
        # Basic validation for SHA256 hash format (64 hexadecimal characters)
        if v and len(v) != 64:
            raise ValueError('content_hash must be a valid SHA256 hash (64 characters)')
        return v