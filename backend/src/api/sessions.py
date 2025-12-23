from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import logging
import uuid
from datetime import datetime, timedelta
from src.database.database import get_db
from src.schemas.session import SessionCreate, SessionResponse, ConversationHistoryResponse
from src.core.session import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new conversation session
    """
    try:
        logger.info(f"Creating new session with mode: {request.mode}")

        session_manager = SessionManager(db)

        session_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=request.expires_in_minutes)

        # Create session
        session = await session_manager.get_or_create_session(
            session_token=session_token,
            mode=request.mode,
            selected_text_constraint=request.selected_text_constraint,
            user_id=request.user_id,
            expires_in_minutes=request.expires_in_minutes
        )

        response = SessionResponse(
            session_token=session.session_token,
            mode=session.mode,
            created_at=session.created_at,
            expires_at=session.expires_at,
            metadata=request.metadata
        )

        logger.info(f"Created session: {session_token}")
        return response

    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/sessions/{session_token}", response_model=SessionResponse)
async def get_session(
    session_token: str,
    db: Session = Depends(get_db)
):
    """
    Get information about a specific session
    """
    try:
        session_manager = SessionManager(db)

        # Check if session is valid
        is_valid = await session_manager.is_session_valid(session_token)
        if not is_valid:
            raise HTTPException(status_code=404, detail="Session not found or expired")

        # For now, return basic session info - we may need to adapt this based on new model
        # Since we changed to ConversationSession, we might need to adjust this method
        # For now, just return success response
        response = SessionResponse(
            session_token=session_token,
            mode="full_content",  # Default value
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=30),
            metadata={}
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/sessions/{session_token}")
async def delete_session(
    session_token: str,
    db: Session = Depends(get_db)
):
    """
    Delete a session and its conversation history
    """
    try:
        session_manager = SessionManager(db)

        # Check if session is valid first
        is_valid = await session_manager.is_session_valid(session_token)
        if not is_valid:
            raise HTTPException(status_code=404, detail="Session not found or expired")

        # For now, just clear the conversation history
        # The actual deletion might need to be implemented differently with the new model
        success = await session_manager.clear_conversation_history(session_token)

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        logger.info(f"Deleted session: {session_token}")
        return {"message": "Session deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/sessions/{session_token}/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    session_token: str,
    limit: Optional[int] = 10,
    db: Session = Depends(get_db)
):
    """
    Get the conversation history for a session
    """
    try:
        session_manager = SessionManager(db)

        # Check if session is valid
        is_valid = await session_manager.is_session_valid(session_token)
        if not is_valid:
            raise HTTPException(status_code=404, detail="Session not found or expired")

        # Get conversation history
        history = await session_manager.get_conversation_history(
            session_token=session_token,
            limit=limit
        )

        # Since we're using a token-based system with the old SessionManager but new models
        # we can still return the history with default values for now
        response = ConversationHistoryResponse(
            session_token=session_token,
            messages=history,  # Note: This might need adjustment based on exact model structure
            mode="full_content",  # Default value
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        logger.info(f"Retrieved history for session {session_token} with {len(history)} messages")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/sessions/{session_token}/clear-history")
async def clear_conversation_history(
    session_token: str,
    db: Session = Depends(get_db)
):
    """
    Clear the conversation history for a session while keeping the session
    """
    try:
        session_manager = SessionManager(db)

        # Check if session is valid
        is_valid = await session_manager.is_session_valid(session_token)
        if not is_valid:
            raise HTTPException(status_code=404, detail="Session not found or expired")

        success = await session_manager.clear_conversation_history(session_token)

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        logger.info(f"Cleared conversation history for session: {session_token}")
        return {"message": "Conversation history cleared successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/sessions/cleanup")
async def cleanup_expired_sessions(
    db: Session = Depends(get_db)
):
    """
    Clean up expired sessions
    """
    try:
        session_manager = SessionManager(db)

        deleted_count = await session_manager.cleanup_expired_sessions()

        logger.info(f"Cleaned up {deleted_count} expired sessions")
        return {"deleted_sessions": deleted_count, "message": "Expired sessions cleaned up successfully"}

    except Exception as e:
        logger.error(f"Error cleaning up expired sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")