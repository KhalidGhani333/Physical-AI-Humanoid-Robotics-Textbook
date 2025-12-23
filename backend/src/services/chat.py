"""
Chat service for the RAG Chatbot API
Handles conversation management and chat interactions
"""
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.services.retrieval import RetrievalService
from src.services.gemini import GeminiAPIService
from src.services.storage import ContentStorageService
from src.models.conversation import ConversationSession
from src.models.chat import ChatMessage
from src.utils.logging import log_chat_interaction, app_logger

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for handling chat interactions and conversation management
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.retrieval_service = RetrievalService(db_session)
        self.gemini_service = GeminiAPIService()  # Using the Gemini service we created
        self.content_storage = ContentStorageService(db_session)

    async def create_conversation_session(
        self,
        user_id: Optional[str] = None,
        selected_text_mode: bool = False,
        selected_text_chunks: Optional[List[str]] = None
    ) -> ConversationSession:
        """
        Create a new conversation session
        """
        try:
            # Calculate session expiration (1 hour from now)
            expires_at = datetime.utcnow() + timedelta(minutes=60)

            # Create session metadata
            session_metadata = {
                "created_at": datetime.utcnow().isoformat(),
                "selected_text_mode": selected_text_mode,
                "selected_text_chunks": selected_text_chunks or []
            }

            # Create the conversation session
            session = ConversationSession(
                user_id=UUID(user_id) if user_id else None,
                session_metadata=session_metadata,
                expires_at=expires_at
            )

            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            logger.info(f"Created new conversation session: {session.id}")
            return session

        except Exception as e:
            logger.error(f"Error creating conversation session: {e}")
            self.db.rollback()
            raise

    async def get_conversation_session(self, session_id: UUID) -> Optional[ConversationSession]:
        """
        Get a conversation session by ID
        """
        try:
            session = self.db.query(ConversationSession).filter(
                ConversationSession.id == session_id
            ).first()

            if session:
                # Check if session is expired
                if session.expires_at and session.expires_at < datetime.utcnow():
                    logger.info(f"Session {session_id} has expired")
                    return None

            return session
        except Exception as e:
            logger.error(f"Error retrieving conversation session {session_id}: {e}")
            return None

    async def send_message(
        self,
        session_id: UUID,
        content: str,
        selected_text: Optional[str] = None,
        context_window: int = 5
    ) -> Dict[str, Any]:
        """
        Process a user message and generate a response
        """
        try:
            # Get the conversation session
            session = await self.get_conversation_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found or expired")

            # Determine retrieval mode based on session settings
            session_metadata = session.session_metadata or {}
            selected_text_mode = session_metadata.get("selected_text_mode", False)
            selected_chunks = session_metadata.get("selected_text_chunks", [])

            # If selected_text is provided in the request, use it for selected-text-only mode
            if selected_text and not selected_chunks:
                # In a real implementation, you would need to identify which chunks correspond to the selected text
                # For now, we'll use the provided selected_chunks from session or empty list
                retrieval_mode = "selected_text_only"
                text_chunks = selected_chunks
            elif selected_text_mode:
                retrieval_mode = "selected_text_only"
                text_chunks = selected_chunks
            else:
                retrieval_mode = "full_content"
                text_chunks = None

            # Retrieve relevant content based on the query
            retrieval_result = await self.retrieval_service.retrieve_content_with_validation(
                query=content,
                session_id=session_id,
                mode=retrieval_mode,
                selected_text_chunks=text_chunks
            )

            # Generate response using Gemini
            response_data = await self.gemini_service.generate_content_aware_response(
                query=content,
                retrieved_chunks=retrieval_result["results"],
                content_boundary_enforced=True
            )

            # Create user message record
            user_message = ChatMessage(
                session_id=session_id,
                role="user",
                content=content,
                retrieval_results=[r["chunk_id"] for r in retrieval_result["results"]],
                sources=[]  # User messages don't have sources
            )
            self.db.add(user_message)

            # Create assistant message record
            assistant_message = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=response_data["response"],
                retrieval_results=[r["chunk_id"] for r in retrieval_result["results"]],
                sources=response_data.get("sources_used", [])
            )
            self.db.add(assistant_message)

            # Commit both messages
            self.db.commit()

            # Prepare the response
            result = {
                "response": response_data["response"],
                "sources": response_data.get("sources_used", []),
                "retrieval_info": {
                    "mode": retrieval_result["mode"],
                    "retrieved_chunks": retrieval_result["results"],
                    "relevance_scores": [r["relevance_score"] for r in retrieval_result["results"]]
                },
                "message_id": str(assistant_message.id),
                "timestamp": datetime.utcnow().isoformat()
            }

            # Log the chat interaction
            log_chat_interaction(
                app_logger,
                session_id=str(session_id),
                user_input=content,
                response_length=len(response_data["response"]),
                sources_count=len(response_data.get("sources_used", []))
            )

            return result

        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            self.db.rollback()
            raise

    async def get_conversation_history(
        self,
        session_id: UUID,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get the conversation history for a session
        """
        try:
            # Get the conversation session
            session = await self.get_conversation_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found or expired")

            # Get messages for the session
            messages = self.db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.timestamp).limit(limit).all()

            # Format the messages
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "sources": msg.sources,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                })

            logger.info(f"Retrieved {len(formatted_messages)} messages for session {session_id}")
            return formatted_messages

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            raise

    async def validate_content_boundary(
        self,
        response: str,
        retrieved_content: List[Dict[str, Any]]
    ) -> bool:
        """
        Validate that the response only contains information from the retrieved content
        """
        try:
            is_valid = await self.gemini_service.validate_response_content(response, retrieved_content)
            logger.info("Content boundary validation completed")
            return is_valid
        except Exception as e:
            logger.error(f"Error during content boundary validation: {e}")
            return False

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired conversation sessions
        """
        try:
            expired_sessions = self.db.query(ConversationSession).filter(
                ConversationSession.expires_at < datetime.utcnow()
            ).all()

            count = 0
            for session in expired_sessions:
                # In a real implementation, you might want to also delete associated messages
                self.db.delete(session)
                count += 1

            if count > 0:
                self.db.commit()
                logger.info(f"Cleaned up {count} expired sessions")

            return count

        except Exception as e:
            logger.error(f"Error during expired session cleanup: {e}")
            self.db.rollback()
            return 0


# Global instance will be created when needed with proper DB session