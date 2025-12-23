from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import logging
from src.database.database import get_db
from src.schemas.content import ChatRequest, ChatResponse
from src.core.gemini import GeminiService
from src.core.retrieval import RetrievalService
from src.core.session import SessionManager
from src.models.conversation import ConversationSession as SessionModel
from src.models.chat import ChatMessage

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat/completions", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Main chat completion endpoint that processes user queries and returns AI-generated responses
    """
    try:
        logger.info(f"Received chat request: '{request.message[:50]}'")

        # Initialize services
        gemini_service = GeminiService()
        retrieval_service = RetrievalService()
        session_manager = SessionManager(db)

        # Get or create session
        session_token = request.session_token or str(uuid.uuid4())
        session = await session_manager.get_or_create_session(
            session_token=session_token,
            mode=request.mode,
            selected_text_constraint=request.selected_text
        )

        # Update session with selected text if provided
        if request.selected_text and session.mode == "selected_text_only":
            await session_manager.update_session_constraint(
                session_token=session_token,
                selected_text=request.selected_text
            )

        # Get conversation history for context
        conversation_history = await session_manager.get_conversation_history(
            session_token=session_token
        )

        # Perform retrieval based on mode
        if session.mode == "selected_text_only" and request.selected_text:
            # In selected text mode, search within the selected text
            context = await retrieval_service.retrieve_and_rerank(
                query=request.message,
                top_k=5,
                selected_text=request.selected_text
            )
            # Enforce content boundaries
            context = await retrieval_service.enforce_content_boundaries(
                results=context,
                selected_text=request.selected_text
            )
        else:
            # In full content mode, search across all documents
            context = await retrieval_service.retrieve_and_rerank(
                query=request.message,
                top_k=5,
                document_ids=request.document_ids
            )

        # Generate response using Gemini
        response_data = await gemini_service.generate_response(
            query=request.message,
            context=context,
            conversation_history=conversation_history,
            mode=session.mode
        )

        # Validate response grounding
        is_grounding_valid = await gemini_service.validate_response_grounding(
            response=response_data["response"],
            context=context
        )

        if not is_grounding_valid and session.mode == "selected_text_only":
            # In selected text mode, ensure strict grounding
            response_data["response"] = (
                "I couldn't find sufficient information in the selected text to answer your question. "
                "The provided context does not contain the information needed to answer your query."
            )
            response_data["sources"] = []

        # Save the conversation to the database
        await session_manager.add_message_to_conversation(
            session_token=session_token,
            role="user",
            content=request.message,
            sources=[]
        )

        await session_manager.add_message_to_conversation(
            session_token=session_token,
            role="assistant",
            content=response_data["response"],
            sources=response_data["sources"]
        )

        # Prepare response
        response = ChatResponse(
            response=response_data["response"],
            sources=response_data["sources"],
            session_token=session_token,
            query=request.message
        )

        logger.info(f"Successfully generated chat response for session {session_token}")
        return response

    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        # Return a more user-friendly error message
        error_detail = str(e)
        if "timeout" in error_detail.lower():
            response_text = "Request timed out. Please try again."
        elif "API key" in error_detail or "Authentication" in error_detail:
            response_text = "Authentication error: Please check your API key configuration."
        elif "model" in error_detail or "404" in error_detail:
            response_text = "AI model unavailable: The system tried multiple models but none are accessible. Please check your API key and model access permissions."
        else:
            response_text = "I encountered an error while processing your request. Please try again later."

        # Create a response even when there's an error
        error_response = ChatResponse(
            response=response_text,
            sources=[],
            session_token=request.session_token or str(uuid.uuid4()),
            query=request.message
        )

        return error_response


@router.post("/chat/validate-boundaries")
async def validate_content_boundaries(
    query: str,
    selected_text: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Validate that a query can be answered within content boundaries
    """
    try:
        retrieval_service = RetrievalService()

        if selected_text:
            # Check if query can be answered from selected text
            results = await retrieval_service.search_content(
                query=query,
                top_k=3,
                selected_text=selected_text
            )

            # Enforce boundaries
            filtered_results = await retrieval_service.enforce_content_boundaries(
                results=results,
                selected_text=selected_text
            )

            can_answer = len(filtered_results) > 0

            return {
                "can_answer": can_answer,
                "relevant_chunks": len(filtered_results),
                "message": "Query can be answered from selected text" if can_answer else "Query cannot be answered from selected text"
            }
        else:
            return {
                "can_answer": True,
                "relevant_chunks": 0,
                "message": "No selected text constraint provided, query can be answered from full content"
            }

    except Exception as e:
        logger.error(f"Error in content boundary validation: {str(e)}")
        # Return a default response when there's an error
        return {
            "can_answer": False,
            "relevant_chunks": 0,
            "message": "Error validating content boundaries"
        }