from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import logging
from src.database.database import get_db
from src.schemas.content import DocumentIngestRequest, DocumentIngestResponse
from src.core.ingestion import ContentIngestionService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/ingest", response_model=DocumentIngestResponse)
async def ingest_document(
    request: DocumentIngestRequest,
    db: Session = Depends(get_db)
):
    """
    Ingest a document into the RAG system
    """
    try:
        logger.info(f"Starting ingestion for document: {request.document_id}")

        # Initialize ingestion service
        ingestion_service = ContentIngestionService()

        # Process the document
        result = await ingestion_service.process_document(
            content=request.content,
            document_id=request.document_id,
            source_url=request.source_url,
            metadata=request.metadata
        )

        if result["success"]:
            logger.info(f"Successfully ingested document {request.document_id}: {result['chunks_processed']} chunks")
        else:
            logger.error(f"Failed to ingest document {request.document_id}: {result['message']}")

        response = DocumentIngestResponse(
            success=result["success"],
            document_id=result["document_id"],
            chunks_processed=result["chunks_processed"],
            message=result["message"]
        )

        return response

    except Exception as e:
        logger.error(f"Error in document ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/ingest/batch")
async def batch_ingest(
    documents: list[DocumentIngestRequest],
    db: Session = Depends(get_db)
):
    """
    Ingest multiple documents in a batch
    """
    try:
        logger.info(f"Starting batch ingestion for {len(documents)} documents")

        ingestion_service = ContentIngestionService()
        results = []

        for doc_request in documents:
            result = await ingestion_service.process_document(
                content=doc_request.content,
                document_id=doc_request.document_id,
                source_url=doc_request.source_url,
                metadata=doc_request.metadata
            )
            results.append(result)

        success_count = sum(1 for r in results if r["success"])
        total_count = len(results)

        logger.info(f"Batch ingestion completed: {success_count}/{total_count} documents successful")

        return {
            "total_documents": total_count,
            "successful_ingestions": success_count,
            "failed_ingestions": total_count - success_count,
            "results": results
        }

    except Exception as e:
        logger.error(f"Error in batch ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/documents/{document_id}")
async def get_document_info(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Get information about a specific document
    """
    try:
        from src.models.content import ContentChunk

        # Count chunks for this document
        chunk_count = db.query(ContentChunk).filter(
            ContentChunk.document_id == document_id
        ).count()

        if chunk_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "document_id": document_id,
            "chunk_count": chunk_count,
            "status": "available"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a document and all its chunks from the system
    """
    try:
        from src.models.content import ContentChunk
        import src.database.database as db_module

        # Get all chunks for this document to delete from Qdrant
        chunks = db.query(ContentChunk).filter(
            ContentChunk.document_id == document_id
        ).all()

        if not chunks:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete chunks from Qdrant
        qdrant_ids = [chunk.embedding_vector_id for chunk in chunks]
        db_module.qdrant_client.delete(
            collection_name="content_chunks",
            points_selector=qdrant_ids
        )

        # Delete chunks from PostgreSQL
        db.query(ContentChunk).filter(
            ContentChunk.document_id == document_id
        ).delete()

        db.commit()

        logger.info(f"Deleted document {document_id} with {len(chunks)} chunks")
        return {
            "document_id": document_id,
            "chunks_deleted": len(chunks),
            "message": "Document successfully deleted"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")