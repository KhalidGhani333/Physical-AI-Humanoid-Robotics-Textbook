from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator


class DocumentChunk(BaseModel):
    """
    Represents a segment of extracted content that has been processed into embeddings
    """
    id: str  # Unique identifier for the chunk (UUID or content hash)
    document_id: str  # Identifier for the original document
    source_url: str  # URL where the content was extracted from
    chunk_index: int  # Sequential index of this chunk within the document
    content: str  # The text content of the chunk
    embedding: Optional[List[float]] = None  # Vector embedding generated from the content
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

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

    @field_validator('chunk_index')
    def validate_chunk_index(cls, v):
        if v < 0:
            raise ValueError('chunk_index must be non-negative')
        return v

    @field_validator('content')
    def validate_content(cls, v):
        # Note: Maximum token length validation would happen at the application level
        # since it depends on the embedding model's limitations
        return v

    @field_validator('embedding')
    def validate_embedding(cls, v):
        # Embedding validation would happen at the application level
        # since dimensions depend on the specific model used
        return v