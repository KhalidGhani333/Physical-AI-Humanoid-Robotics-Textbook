import asyncio
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
import uuid
from src.models.conversation import ConversationSession as SessionModel
from src.models.chat import ChatMessage
from src.config import settings

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self, db: Session):
        self.db = db

    async def get_or_create_session(
        self,
        session_token: str,
        mode: str = "full_content",
        selected_text_constraint: Optional[str] = None,
        user_id: Optional[str] = None,
        expires_in_minutes: int = 30
    ) -> SessionModel:
        """
        Get an existing session or create a new one
        """
        # Try to find existing session
        existing_session = self.db.query(SessionModel).filter(
            SessionModel.session_token == session_token
        ).first()

        if existing_session:
            # Update session if needed
            if selected_text_constraint:
                existing_session.selected_text_constraint = selected_text_constraint
            if mode:
                existing_session.mode = mode
            self.db.commit()
            return existing_session

        # Create new session
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)

        new_session = SessionModel(
            session_token=session_token,
            user_id=user_id,
            mode=mode,
            selected_text_constraint=selected_text_constraint,
            expires_at=expires_at
        )

        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)

        logger.info(f"Created new session: {session_token}")
        return new_session

    async def update_session_constraint(
        self,
        session_token: str,
        selected_text: str
    ) -> bool:
        """
        Update the selected text constraint for a session
        """
        session = self.db.query(SessionModel).filter(
            SessionModel.session_token == session_token
        ).first()

        if not session:
            return False

        session.selected_text_constraint = selected_text
        session.mode = "selected_text_only"  # Automatically switch to selected text mode
        self.db.commit()

        logger.info(f"Updated session constraint for {session_token}")
        return True

    async def get_conversation_history(
        self,
        session_token: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session
        """
        session = self.db.query(SessionModel).filter(
            SessionModel.session_token == session_token
        ).first()

        if not session:
            return []

        # Get recent messages
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(desc(ChatMessage.timestamp)).limit(limit).all()

        # Convert to dict format and reverse to get chronological order
        history = []
        for msg in reversed(messages):
            history.append({
                "role": msg.role,
                "content": msg.content,
                "sources": msg.sources,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
            })

        logger.info(f"Retrieved {len(history)} messages for session {session_token}")
        return history

    async def add_message_to_conversation(
        self,
        session_token: str,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Add a message to the conversation history
        """
        session = self.db.query(SessionModel).filter(
            SessionModel.session_token == session_token
        ).first()

        if not session:
            logger.error(f"Session {session_token} not found")
            return False

        # Create new message
        chat_message = ChatMessage(
            session_id=session.id,
            role=role,
            content=content,
            sources=str(sources) if sources else None
        )

        self.db.add(chat_message)
        self.db.commit()

        logger.info(f"Added {role} message to session {session_token}")
        return True

    async def clear_conversation_history(
        self,
        session_token: str
    ) -> bool:
        """
        Clear conversation history for a session
        """
        session = self.db.query(SessionModel).filter(
            SessionModel.session_token == session_token
        ).first()

        if not session:
            return False

        # Delete all messages for this session
        self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).delete()

        self.db.commit()
        logger.info(f"Cleared conversation history for session {session_token}")
        return True

    async def is_session_valid(
        self,
        session_token: str
    ) -> bool:
        """
        Check if a session is still valid (not expired)
        """
        session = self.db.query(SessionModel).filter(
            SessionModel.session_token == session_token
        ).first()

        if not session:
            return False

        if session.expires_at and session.expires_at < datetime.utcnow():
            # Session has expired
            return False

        return True

    async def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions from the database
        """
        expired_count = self.db.query(SessionModel).filter(
            SessionModel.expires_at < datetime.utcnow()
        ).delete()

        self.db.commit()
        logger.info(f"Cleaned up {expired_count} expired sessions")
        return expired_count