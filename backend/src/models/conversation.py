from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.sql import func
from src.database.database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid


class ConversationSession(Base):
    """
    Model for storing conversation sessions with user interactions
    """
    __tablename__ = "conversation_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_token = Column(String, unique=True, nullable=False)  # Session identifier
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Optional for anonymous sessions
    mode = Column(String, default="full_content")  # Chat mode: 'full_content' or 'selected_text_only'
    selected_text_constraint = Column(Text, nullable=True)  # Text constraint for selected text mode
    session_metadata = Column(JSON)  # JSON for additional session metadata
    expires_at = Column(DateTime(timezone=True))  # When the session expires
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes for performance
    __table_args__ = (
        Index('idx_session_token', 'session_token'),
        Index('idx_expires_at', 'expires_at'),
        Index('idx_user_id', 'user_id'),
    )

    def __repr__(self):
        return f"<ConversationSession(id={self.id}, session_token={self.session_token}, user_id={self.user_id})>"