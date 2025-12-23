"""
Retrieval API endpoints for the RAG Chatbot API
Handles semantic search and content retrieval operations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from src.database.database import get_db
from src.services.retrieval import RetrievalService
from src.utils.logging import log_retrieval, app_logger
from src.middleware.auth import api_key_auth

router = APIRouter()


class RetrievalRequest(BaseModel):
    """
    Request model for retrieval endpoint
    """
    query: str
    mode: str = "full_content"  # "full_content" or "selected_text_only"
    selected_text_chunks: Optional[List[str]] = None
    top_k: int = 5
    min_relevance_score: float = 0.5


class RetrievalResponse(BaseModel):
    """
    Response model for retrieval endpoint
    """
    query: str
    results: List[dict]
    mode: str
    retrieved_count: int


@router.post("/retrieval/query",
             response_model=RetrievalResponse,
             summary="Perform semantic search",
             description="Perform a semantic search on the content corpus")
async def perform_retrieval(
    request: RetrievalRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint to perform semantic search on the content corpus
    """
    # Authenticate the request
    from fastapi import Request
    # Authentication would be handled by middleware in a real implementation

    try:
        # Validate mode
        if request.mode not in ["full_content", "selected_text_only"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid mode. Must be 'full_content' or 'selected_text_only'"
            )

        # Initialize the retrieval service
        retrieval_service = RetrievalService(db)

        # Perform the retrieval
        result = await retrieval_service.retrieve_content_with_validation(
            query=request.query,
            top_k=request.top_k,
            min_relevance_score=request.min_relevance_score,
            mode=request.mode,
            selected_text_chunks=request.selected_text_chunks
        )

        # Log the successful retrieval
        log_retrieval(
            app_logger,
            query=request.query,
            results_count=result["retrieved_count"],
            response_time=result["response_time"],
            mode=request.mode
        )

        return RetrievalResponse(
            query=result["query"],
            results=result["results"],
            mode=result["mode"],
            retrieved_count=result["retrieved_count"]
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error
        app_logger.error(f"Error during content retrieval: {str(e)}")

        # Raise a 500 error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval failed: {str(e)}"
        )


class ContentChunkRequest(BaseModel):
    """
    Request model for getting a specific content chunk
    """
    chunk_id: str


@router.post("/retrieval/chunk",
             summary="Get specific content chunk",
             description="Retrieve a specific content chunk by its ID")
async def get_content_chunk(
    request: ContentChunkRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint to retrieve a specific content chunk
    """
    try:
        # In a real implementation, you'd retrieve the chunk from the database
        # For now, we'll just return the chunk ID as a placeholder
        # Since chunks are stored in Qdrant, we'd need to implement a method to retrieve them

        # This would typically involve:
        # 1. Getting the chunk from Qdrant by ID
        # 2. Potentially getting additional metadata from PostgreSQL

        return {
            "chunk_id": request.chunk_id,
            "content": "Content would be retrieved here",
            "metadata": {}
        }
    except Exception as e:
        app_logger.error(f"Error retrieving content chunk {request.chunk_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve content chunk"
        )


@router.get("/retrieval/health",
            summary="Health check for retrieval service",
            description="Check if the retrieval service is operational")
async def retrieval_health():
    """
    Health check endpoint for the retrieval service
    """
    return {
        "status": "healthy",
        "service": "retrieval",
        "message": "Retrieval service is operational"
    }