from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.sql import func
from src.database.database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid


class ChatMessage(Base):
    """
    Model for storing individual chat messages in a conversation
    """
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("conversation_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    retrieval_results = Column(JSON)  # JSON array of content chunk IDs used in response
    sources = Column(JSON)  # JSON array of source citations
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(JSON)  # Additional message metadata

    # Indexes for performance
    __table_args__ = (
        Index('idx_chat_message_session_timestamp', 'session_id', 'timestamp'),
        Index('idx_chat_message_role', 'role'),
    )

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, session_id={self.session_id}, role={self.role})>"


class RetrievalResult(Base):
    """
    Model for storing retrieval results from vector search
    """
    __tablename__ = "retrieval_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("conversation_sessions.id"), nullable=False)
    query = Column(Text, nullable=False)
    retrieved_chunks = Column(JSON)  # JSON array of content chunk IDs that were retrieved
    relevance_scores = Column(JSON)  # JSON array of relevance scores for each chunk
    mode = Column(String, default="full_content")  # "full_content" or "selected_text_only"
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(JSON)  # Additional retrieval metadata

    # Indexes for performance
    __table_args__ = (
        Index('idx_retrieval_result_session_timestamp', 'session_id', 'timestamp'),
        Index('idx_retrieval_result_mode', 'mode'),
    )

    def __repr__(self):
        return f"<RetrievalResult(id={self.id}, session_id={self.session_id}, mode={self.mode})>"