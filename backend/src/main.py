from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys

# Import API routers
from src.api import chat, ingestion, retrieval, sessions
from src.middleware import add_middlewares
from src.middleware.security import SecurityMiddleware, InputValidationMiddleware
from src.database.utils import init_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for application startup and shutdown
    """
    logger.info("Starting up RAG Chatbot API...")
    # Initialize database connections and collections
    init_database()
    yield
    # Shutdown logic here
    logger.info("Shutting down RAG Chatbot API...")

# Create FastAPI app instance
app = FastAPI(
    title="RAG Chatbot API",
    description="Integrated RAG Chatbot for Digital Book / Website (Gemini-based)",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:8080", "http://localhost:8000"],  # Allow Docusaurus dev server and backend
    allow_credentials=True,
    allow_methods=["GET","POST","PUT","DELETE"],
    allow_headers=["*"],
)

# Add custom middlewares
add_middlewares(app)

# Include API routers
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(ingestion.router, prefix="/api/v1", tags=["ingestion"])
app.include_router(retrieval.router, prefix="/api/v1", tags=["retrieval"])
app.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])

@app.get("/api/v1/health", tags=["health"])
async def health_check():
    """
    Health check endpoint to verify API is running
    """
    return {"status": "healthy", "service": "RAG Chatbot API"}

@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint that provides API information
    """
    return {"message": "RAG Chatbot API - Integrated RAG Chatbot for Digital Book / Website (Gemini-based)"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)