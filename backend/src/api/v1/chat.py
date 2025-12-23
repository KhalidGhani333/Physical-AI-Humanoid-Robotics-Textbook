"""
Chat API endpoints for the RAG Chatbot API
Handles chat interactions and conversation management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID

from src.database.database import get_db
from src.services.chat import ChatService
from src.utils.logging import log_chat_interaction, app_logger
from src.middleware.auth import api_key_auth

router = APIRouter()


class CreateSessionRequest(BaseModel):
    """
    Request model for creating a chat session
    """
    user_id: Optional[str] = None
    selected_text_mode: bool = False
    selected_text_chunks: Optional[List[str]] = []
    session_metadata: Optional[Dict[str, Any]] = {}


class CreateSessionResponse(BaseModel):
    """
    Response model for creating a chat session
    """
    session_id: str
    expires_at: str
    selected_text_mode: bool


class SendMessageRequest(BaseModel):
    """
    Request model for sending a message
    """
    content: str
    selected_text: Optional[str] = None
    context_window: int = 5


class SendMessageResponse(BaseModel):
    """
    Response model for sending a message
    """
    response: str
    sources: List[Dict[str, Any]]
    retrieval_info: Dict[str, Any]
    message_id: str
    timestamp: str


class GetHistoryResponse(BaseModel):
    """
    Response model for getting conversation history
    """
    session_id: str
    messages: List[Dict[str, Any]]


@router.post("/chat/sessions",
             response_model=CreateSessionResponse,
             summary="Create a new conversation session",
             description="Create a new conversation session for a user")
async def create_session(
    request: CreateSessionRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint to create a new conversation session
    """
    # Authenticate the request - in a real implementation, this would be done via middleware
    # await api_key_auth.validate_api_key(request)

    try:
        # Initialize the chat service
        chat_service = ChatService(db)

        # Create the conversation session
        session = await chat_service.create_conversation_session(
            user_id=request.user_id,
            selected_text_mode=request.selected_text_mode,
            selected_text_chunks=request.selected_text_chunks
        )

        return CreateSessionResponse(
            session_id=str(session.id),
            expires_at=session.expires_at.isoformat(),
            selected_text_mode=request.selected_text_mode
        )

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error creating chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
        )


@router.post("/chat/sessions/{session_id}/messages",
             response_model=SendMessageResponse,
             summary="Send a message to the chatbot",
             description="Send a message to the chatbot and receive a response")
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint to send a message to the chatbot
    """
    # Authenticate the request - in a real implementation, this would be done via middleware
    # await api_key_auth.validate_api_key(request)

    try:
        # Validate session ID format
        try:
            uuid_session_id = UUID(session_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session ID format"
            )

        # Initialize the chat service
        chat_service = ChatService(db)

        # Send the message and get response
        response = await chat_service.send_message(
            session_id=uuid_session_id,
            content=request.content,
            selected_text=request.selected_text,
            context_window=request.context_window
        )

        return SendMessageResponse(**response)

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message"
        )


@router.get("/chat/sessions/{session_id}/history",
            response_model=GetHistoryResponse,
            summary="Get conversation history",
            description="Retrieve conversation history for a session")
async def get_conversation_history(
    session_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Endpoint to get conversation history for a session
    """
    try:
        # Validate session ID format
        try:
            uuid_session_id = UUID(session_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session ID format"
            )

        # Initialize the chat service
        chat_service = ChatService(db)

        # Get the conversation history
        messages = await chat_service.get_conversation_history(
            session_id=uuid_session_id,
            limit=limit
        )

        return GetHistoryResponse(
            session_id=session_id,
            messages=messages
        )

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error retrieving conversation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation history"
        )


@router.get("/chat/sessions/{session_id}",
            summary="Get session details",
            description="Get details about a conversation session")
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Endpoint to get session details
    """
    try:
        # Validate session ID format
        try:
            uuid_session_id = UUID(session_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session ID format"
            )

        # Initialize the chat service
        chat_service = ChatService(db)

        # Get the session
        session = await chat_service.get_conversation_session(uuid_session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or expired"
            )

        return {
            "session_id": str(session.id),
            "user_id": str(session.user_id) if session.user_id else None,
            "session_metadata": session.session_metadata,
            "expires_at": session.expires_at.isoformat(),
            "created_at": session.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error retrieving session details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session details"
        )


@router.get("/chat/health",
            summary="Health check for chat service",
            description="Check if the chat service is operational")
async def chat_health():
    """
    Health check endpoint for the chat service
    """
    return {
        "status": "healthy",
        "service": "chat",
        "message": "Chat service is operational"
    }