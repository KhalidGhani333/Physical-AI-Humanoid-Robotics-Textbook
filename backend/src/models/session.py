from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from src.database.database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Session(Base):
    """
    Model for storing conversation sessions
    """
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_token = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(String, nullable=True)  # Optional user identifier
    selected_text_constraint = Column(Text, nullable=True)  # For selected-text-only mode
    mode = Column(String(50), default="full_content")  # "full_content" or "selected_text_only"
    metadata_json = Column(Text)  # JSON string for additional session metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))  # When the session expires

    def __repr__(self):
        return f"<Session(id={self.id}, session_token={self.session_token}, mode={self.mode})>"


