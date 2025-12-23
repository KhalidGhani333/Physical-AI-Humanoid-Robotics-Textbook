from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class ContentChunkBase(BaseModel):
    document_id: str
    chunk_index: int
    content: str
    source_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ContentChunkCreate(ContentChunkBase):
    pass


class ContentChunk(ContentChunkBase):
    id: uuid.UUID
    embedding_vector_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentIngestRequest(BaseModel):
    content: str = Field(..., description="The content to be ingested")
    document_id: str = Field(..., description="Unique identifier for the document")
    source_url: Optional[str] = Field(None, description="URL where the content originated")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the document")
    chunk_size: Optional[int] = Field(None, description="Size of content chunks (default from config)")


class DocumentIngestResponse(BaseModel):
    success: bool
    document_id: str
    chunks_processed: int
    message: str


class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="The search query")
    document_ids: Optional[List[str]] = Field(None, description="Specific documents to search within")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of results to return")
    selected_text_only: Optional[bool] = Field(False, description="Whether to search only in selected text")


class RetrievalResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    sources: List[Dict[str, Any]]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="The user's message")
    session_token: Optional[str] = Field(None, description="Session token for conversation continuity")
    mode: Optional[str] = Field("full_content", description="Chat mode: 'full_content' or 'selected_text_only'")
    selected_text: Optional[str] = Field(None, description="Text selected by user for 'selected_text_only' mode")
    document_ids: Optional[List[str]] = Field(None, description="Specific documents to search within")


class ChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]]
    session_token: str
    query: str