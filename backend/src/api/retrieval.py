from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import logging
from src.database.database import get_db
from src.schemas.content import RetrievalRequest, RetrievalResponse
from src.core.retrieval import RetrievalService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_content(
    request: RetrievalRequest,
    db: Session = Depends(get_db)
):
    """
    Retrieve relevant content based on a query
    """
    try:
        logger.info(f"Retrieving content for query: '{request.query[:50]}...'")

        # Initialize retrieval service
        retrieval_service = RetrievalService()

        # Perform retrieval
        results = await retrieval_service.retrieve_and_rerank(
            query=request.query,
            top_k=request.top_k or 5,
            document_ids=request.document_ids,
            selected_text=request.selected_text_only
        )

        # Prepare response
        response = RetrievalResponse(
            query=request.query,
            results=results,
            sources=[{
                "document_id": result.get("document_id", ""),
                "content_snippet": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", ""),
                "score": result.get("score", 0),
                "source_url": result.get("source_url", "")
            } for result in results]
        )

        logger.info(f"Retrieved {len(results)} results for query")
        return response

    except Exception as e:
        logger.error(f"Error in content retrieval: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/retrieve/boundary-check")
async def check_content_boundaries(
    query: str,
    selected_text: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Check if a query can be answered within content boundaries
    """
    try:
        retrieval_service = RetrievalService()

        if selected_text:
            # Check relevance to selected text
            results = await retrieval_service.search_content(
                query=query,
                top_k=5,
                selected_text=selected_text
            )

            # Enforce boundaries
            filtered_results = await retrieval_service.enforce_content_boundaries(
                results=results,
                selected_text=selected_text
            )

            can_answer = len(filtered_results) > 0

            return {
                "query": query,
                "selected_text_provided": True,
                "can_answer_from_selected": can_answer,
                "relevant_chunks_count": len(filtered_results),
                "message": "Query can be answered from selected text" if can_answer else "Query cannot be answered from selected text"
            }
        else:
            # Without selected text constraint, check general relevance
            results = await retrieval_service.search_content(
                query=query,
                top_k=5
            )

            can_answer = len(results) > 0

            return {
                "query": query,
                "selected_text_provided": False,
                "can_answer_from_full_content": can_answer,
                "relevant_chunks_count": len(results),
                "message": "Query can be answered from full content" if can_answer else "Query cannot be answered from available content"
            }

    except Exception as e:
        logger.error(f"Error in content boundary check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/collections")
async def list_collections():
    """
    List available collections in the vector database
    """
    try:
        import src.database.database as db_module
        collections = db_module.qdrant_client.get_collections()

        return {
            "collections": [collection.name for collection in collections.collections],
            "total_collections": len(collections.collections)
        }
    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/collections/{collection_name}")
async def get_collection_info(collection_name: str):
    """
    Get information about a specific collection
    """
    try:
        import src.database.database as db_module
        collection_info = db_module.qdrant_client.get_collection(collection_name)

        return {
            "name": collection_info.config.params.vectors,
            "vector_size": collection_info.config.params.vectors["content"].size if "content" in collection_info.config.params.vectors else 0,
            "points_count": collection_info.points_count,
            "indexed_vectors_count": collection_info.indexed_vectors_count
        }
    except Exception as e:
        logger.error(f"Error getting collection info: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Collection not found: {str(e)}")