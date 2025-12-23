"""
Content API endpoints for the RAG Chatbot API
Handles content ingestion and management operations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.models.content import ContentIngestionRequest, ContentIngestionResponse
from src.services.ingestion import ContentIngestionService
from src.utils.logging import log_content_operation, app_logger
from src.middleware.auth import api_key_auth

router = APIRouter()


@router.post("/content/ingest",
             response_model=ContentIngestionResponse,
             summary="Ingest content",
             description="Ingest content from various formats (Markdown, HTML, PDF text extracts) into the RAG system")
async def ingest_content(
    request: ContentIngestionRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint to ingest content into the RAG system
    """
    # Authenticate the request
    await api_key_auth.validate_api_key(request)

    try:
        # Initialize the ingestion service
        ingestion_service = ContentIngestionService(db)

        # Perform the ingestion
        result = await ingestion_service.ingest_content(
            title=request.title,
            source_type=request.source_type,
            source_path=request.source_path,
            content=request.content,
            metadata=request.metadata
        )

        # Log the successful ingestion
        log_content_operation(
            app_logger,
            operation="api_ingest",
            document_id=result["document_id"],
            metadata={
                "title": request.title,
                "source_type": request.source_type,
                "chunk_count": result["chunk_count"]
            }
        )

        # Return the response
        return ContentIngestionResponse(
            document_id=result["document_id"],
            status=result["status"],
            chunk_count=result["chunk_count"],
            estimated_processing_time=30  # Fixed estimation as per spec
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error
        app_logger.error(f"Error during content ingestion: {str(e)}")

        # Raise a 500 error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )


@router.get("/content/{document_id}",
            summary="Get document status",
            description="Get the status of a content ingestion job")
async def get_document_status(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Endpoint to get the status of a document ingestion
    """
    # Authenticate the request
    from fastapi import Request
    # Note: In a real implementation, you'd extract the request object properly
    # For now, we'll assume authentication is handled by middleware

    try:
        # Initialize the content storage service
        from src.services.storage import ContentStorageService
        content_storage = ContentStorageService(db)

        # Get the source document
        from uuid import UUID
        try:
            uuid_doc_id = UUID(document_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document ID format"
            )

        document = content_storage.get_source_document(uuid_doc_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        return {
            "id": str(document.id),
            "title": document.title,
            "status": document.status,
            "chunk_count": document.chunk_count,
            "source_type": document.source_type,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error getting document status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document status"
        )


@router.delete("/content/{document_id}",
               summary="Delete content",
               description="Remove a document and its associated chunks from the system")
async def delete_content(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Endpoint to delete content from the system
    """
    # Authenticate the request - in a real implementation, this would be done via middleware

    try:
        # Initialize the content storage service
        from src.services.storage import ContentStorageService, VectorStorageService
        content_storage = ContentStorageService(db)
        vector_storage = VectorStorageService()  # This doesn't require a DB session

        # Get the source document
        from uuid import UUID
        try:
            uuid_doc_id = UUID(document_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document ID format"
            )

        document = content_storage.get_source_document(uuid_doc_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Get all chunks for this document
        from src.models.content import ContentChunk
        chunks = db.query(ContentChunk).filter(
            ContentChunk.source_document_id == uuid_doc_id
        ).all()

        # Delete embeddings from vector storage
        for chunk in chunks:
            await vector_storage.delete_embedding(chunk.embedding_vector_id)

        # Delete the chunks from content storage
        # Note: In a real implementation, you'd want to use SQLAlchemy's cascade delete
        # or implement proper deletion logic

        # Delete the source document
        db.delete(document)
        db.commit()

        # Log the deletion
        log_content_operation(
            app_logger,
            operation="delete_content",
            document_id=document_id
        )

        return {
            "status": "deleted",
            "document_id": document_id
        }

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error deleting content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete content"
        )


@router.get("/content/documents",
            summary="List documents",
            description="List all ingested documents")
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Endpoint to list all ingested documents
    """
    try:
        from src.models.content import SourceDocument

        documents = db.query(SourceDocument)\
                     .offset(skip)\
                     .limit(limit)\
                     .all()

        total_count = db.query(SourceDocument).count()

        return {
            "documents": [
                {
                    "id": str(doc.id),
                    "title": doc.title,
                    "status": doc.status,
                    "chunk_count": doc.chunk_count,
                    "source_type": doc.source_type,
                    "created_at": doc.created_at.isoformat(),
                }
                for doc in documents
            ],
            "total_count": total_count,
            "page": skip // limit + 1 if limit > 0 else 1,
            "per_page": limit
        }
    except Exception as e:
        app_logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents"
        )