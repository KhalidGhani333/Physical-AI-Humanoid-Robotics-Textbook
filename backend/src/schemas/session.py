from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class SessionCreate(BaseModel):
    user_id: Optional[str] = None
    mode: Optional[str] = Field("full_content", description="Session mode: 'full_content' or 'selected_text_only'")
    selected_text_constraint: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    expires_in_minutes: Optional[int] = Field(30, ge=1, le=1440, description="Session expiry in minutes (1 minute to 24 hours)")


class SessionResponse(BaseModel):
    session_token: str
    mode: str
    created_at: datetime
    expires_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class ChatMessageBase(BaseModel):
    role: str = Field(..., description="Role of the message sender ('user' or 'assistant')")
    content: str = Field(..., min_length=1, description="Content of the message")
    sources: Optional[List[Dict[str, Any]]] = None


class ChatMessageResponse(ChatMessageBase):
    id: uuid.UUID
    session_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationHistoryResponse(BaseModel):
    session_token: str
    messages: List[ChatMessageResponse]
    mode: str
    created_at: datetime
    updated_at: Optional[datetime] = None