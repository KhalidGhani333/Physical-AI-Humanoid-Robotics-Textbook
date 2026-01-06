import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir.parent))

from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List, Optional
import asyncio
import uuid
from datetime import datetime
import os
import time

# Import using absolute paths
from src.services.ingestion_workflow import IngestionWorkflow
from src.services.retrieval_service import RetrievalService
from src.models.ingestion_job import IngestionJob
from src.models.api_requests import IngestionJobRequest, ReingestionRequest, RetrievalRequest, RetrievalResponse
from pydantic import BaseModel
from typing import Optional
from src.config.settings import settings

# Chat API models
class ChatRequest(BaseModel):
    message: str
    selected_text: Optional[str] = None
    session_token: Optional[str] = None
    mode: str = "full_content"


class ChatResponse(BaseModel):
    response: str
    session_token: str
    query: Optional[str] = None
    context_used: Optional[str] = None

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="RAG Content Ingestion API",
    description="API for managing the ingestion of textbook content for RAG systems",
    version="0.1.0"
)

# Add rate limiting exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for jobs (in production, use a database)
jobs_storage = {}

# Initialize the ingestion workflow
ingestion_workflow = IngestionWorkflow()


def authenticate_api_key(request: Request):
    """Authenticate API key from header"""
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != os.getenv("API_KEY", "test-api-key"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


@app.get("/")
def read_root():
    """Root endpoint to verify API is running"""
    return {"message": "RAG Content Ingestion API is running"}


@app.post("/api/v1/ingestion/jobs", response_model=dict)
@limiter.limit("100/minute")  # 100 requests per minute per API key (as specified in contract)
async def start_ingestion_job(
    req: Request,  # Need to add Request for rate limiter
    ingestion_request: IngestionJobRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(authenticate_api_key)
):
    """
    Starts a new content ingestion job for specified URLs.
    """
    urls = ingestion_request.urls
    config = ingestion_request.config or {}

    if not urls:
        raise HTTPException(status_code=400, detail="URLs are required")

    job_id = str(uuid.uuid4())

    # Create initial job record
    job = IngestionJob(
        job_id=job_id,
        source_urls=urls,
        status="pending",
        total=len(urls),
        start_time=datetime.now(),
        progress=0,
        processed_chunks=0
    )

    # Store job in memory
    jobs_storage[job_id] = job

    # Run ingestion in background
    background_tasks.add_task(run_ingestion_background, job_id, urls, config)

    return {
        "job_id": job_id,
        "status": "running",
        "urls": urls,
        "created_at": job.start_time.isoformat()
    }


def run_ingestion_background(job_id: str, urls: List[str], config: dict):
    """Run the ingestion workflow in the background"""
    job = jobs_storage.get(job_id)
    if not job:
        return

    try:
        # Update job status
        job.status = "running"

        # Use custom config if provided
        chunk_size = config.get("chunk_size", settings.chunk_size)
        chunk_overlap = config.get("chunk_overlap", settings.chunk_overlap)
        batch_size = config.get("batch_size", settings.batch_size)

        # Run the ingestion workflow
        workflow = IngestionWorkflow()
        result = workflow.run_ingestion_with_config(urls, chunk_size, chunk_overlap, batch_size)

        # Update job with results
        job.status = result.status
        job.progress = result.total  # All URLs processed
        job.processed_chunks = result.processed_chunks
        job.end_time = result.end_time
        job.error_details = result.error_details

    except Exception as e:
        job.status = "failed"
        job.error_details = str(e)
        job.end_time = datetime.now()


@app.get("/api/v1/ingestion/jobs/{job_id}", response_model=dict)
@limiter.limit("100/minute")
async def get_ingestion_job(
    req: Request,
    job_id: str,
    api_key: str = Depends(authenticate_api_key)
):
    """
    Retrieves the current status of an ingestion job.
    """
    job = jobs_storage.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
        "total": job.total,
        "start_time": job.start_time.isoformat() if job.start_time else None,
        "end_time": job.end_time.isoformat() if job.end_time else None,
        "processed_chunks": job.processed_chunks,
        "error_details": job.error_details
    }


@app.get("/api/v1/ingestion/jobs", response_model=List[dict])
@limiter.limit("100/minute")
async def list_ingestion_jobs(
    req: Request,
    api_key: str = Depends(authenticate_api_key)
):
    """
    Retrieves a list of recent ingestion jobs.
    """
    jobs_list = []
    for job in jobs_storage.values():
        jobs_list.append({
            "job_id": job.job_id,
            "status": job.status,
            "urls": len(job.source_urls),
            "created_at": job.start_time.isoformat() if job.start_time else None,
            "completed_at": job.end_time.isoformat() if job.end_time else None
        })

    # Sort by start time, most recent first
    jobs_list.sort(key=lambda x: x["created_at"] or "", reverse=True)

    return jobs_list


@app.post("/api/v1/ingestion/reingest", response_model=dict)
@limiter.limit("100/minute")
async def trigger_full_reingestion(
    req: Request,
    reingest_request: ReingestionRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(authenticate_api_key)
):
    """
    Triggers a full re-ingestion of all textbook content.
    """
    force_reingest = reingest_request.force_reingest
    urls = reingest_request.urls

    if not urls:
        raise HTTPException(status_code=400, detail="URLs are required for re-ingestion")

    job_id = str(uuid.uuid4())

    # Create initial job record
    job = IngestionJob(
        job_id=job_id,
        source_urls=urls,
        status="pending",
        total=len(urls),
        start_time=datetime.now(),
        progress=0,
        processed_chunks=0
    )

    # Store job in memory
    jobs_storage[job_id] = job

    # Run re-ingestion in background
    background_tasks.add_task(run_ingestion_background, job_id, urls, {})

    return {
        "job_id": job_id,
        "status": "running",
        "message": "Full re-ingestion started"
    }


@app.post("/api/v1/retrieval/search", response_model=RetrievalResponse)
@limiter.limit("100/minute")  # 100 requests per minute per API key
async def search_content(
    req: Request,
    retrieval_request: RetrievalRequest,
    api_key: str = Depends(authenticate_api_key)
):
    """
    Search for relevant content based on semantic similarity.
    """
    query = retrieval_request.query
    top_k = retrieval_request.top_k
    min_similarity = retrieval_request.min_similarity

    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    # Initialize retrieval service
    retrieval_service = RetrievalService()

    # Perform search
    start_time = time.time()
    results = retrieval_service.get_relevant_chunks(query, top_k=top_k)
    search_time = time.time() - start_time

    return RetrievalResponse(
        query=query,
        results=results,
        total_results=len(results),
        search_time=search_time
    )


@app.post("/api/v1/chat/completions", response_model=ChatResponse)
async def chat_completions(
    chat_request: ChatRequest,
    api_key: str = Depends(authenticate_api_key)
):
    """
    Chat completions endpoint that uses RAG to generate responses based on textbook content.
    """
    user_message = chat_request.message
    selected_text = chat_request.selected_text
    session_token = chat_request.session_token or f"session_{int(time.time())}"

    # For now, provide a simple response without RAG functionality
    # This will work even if vector store is not available
    response_text = f"Hello! I received your message: '{user_message}'. This is a demo response. The full RAG functionality requires properly ingested content in the vector store. For Physical AI & Humanoid Robotics questions, please ask about specific topics like 'What is embodied AI?', 'What are humanoid robot applications?', or 'How does physical AI differ from traditional AI?'."

    return ChatResponse(
        response=response_text,
        session_token=session_token,
        query=user_message,
        context_used=None
    )


@app.exception_handler(404)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Custom error response handling"""
    if exc.status_code == 404:
        return {
            "error": {
                "code": "NOT_FOUND",
                "message": "The requested resource was not found",
                "details": {}
            }
        }
    return {"detail": exc.detail}


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    return {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An internal error occurred",
            "details": {"error": str(exc)}
        }
    }


def main():
    """
    Main function to run the full ingestion pipeline from command line
    """
    import argparse
    import sys
    import logging

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description='RAG Content Ingestion Pipeline')
    parser.add_argument('--urls', nargs='+', help='List of URLs to process', required=True)
    parser.add_argument('--chunk-size', type=int, default=settings.chunk_size, help='Size of text chunks')
    parser.add_argument('--chunk-overlap', type=int, default=settings.chunk_overlap, help='Overlap between chunks')
    parser.add_argument('--batch-size', type=int, default=settings.batch_size, help='Batch size for processing')
    parser.add_argument('--config-file', type=str, help='Path to configuration file')

    args = parser.parse_args()

    logger.info(f"Starting ingestion pipeline for {len(args.urls)} URLs")
    logger.info(f"Configuration - Chunk size: {args.chunk_size}, Chunk overlap: {args.chunk_overlap}, Batch size: {args.batch_size}")

    try:
        # Create workflow instance
        workflow = IngestionWorkflow()

        # Run the ingestion with specified configuration
        job = workflow.run_ingestion_with_config(
            urls=args.urls,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            batch_size=args.batch_size
        )

        logger.info(f"Ingestion completed with status: {job.status}")
        logger.info(f"Processed {job.processed_chunks} chunks from {job.progress}/{job.total} URLs")

        if job.error_details:
            logger.error(f"Error details: {job.error_details}")

        # Exit with appropriate code
        sys.exit(0 if job.status == "completed" else 1)

    except Exception as e:
        logger.error(f"Error running ingestion pipeline: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    import sys

    # Check if running in server mode or CLI mode
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']):
        # If no arguments or help requested, show the CLI help
        main()
    else:
        # If first argument is not a CLI flag, assume server mode
        import uvicorn
        uvicorn.run(
            "src.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )