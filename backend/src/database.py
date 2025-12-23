"""
Database utilities for the RAG Chatbot API
Handles connections to both Postgres and Qdrant databases
"""
import os
import logging
from typing import Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv

import asyncpg
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Global database connection instances
postgres_pool = None
qdrant_client = None

async def init_postgres_pool():
    """Initialize the Postgres connection pool"""
    global postgres_pool
    try:
        database_url = os.getenv("NEON_DB_URL")
        if not database_url:
            raise ValueError("NEON_DB_URL environment variable is not set")

        postgres_pool = await asyncpg.create_pool(
            database_url,
            min_size=5,
            max_size=20,
            command_timeout=60,
        )
        logger.info("PostgreSQL connection pool initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL connection pool: {e}")
        raise

def get_postgres_pool():
    """Get the global Postgres connection pool"""
    global postgres_pool
    if postgres_pool is None:
        raise RuntimeError("PostgreSQL connection pool not initialized")
    return postgres_pool

def get_qdrant_client():
    """Get the global Qdrant client instance"""
    global qdrant_client
    if qdrant_client is None:
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if not qdrant_url or not qdrant_api_key:
            raise ValueError("QDRANT_URL or QDRANT_API_KEY environment variables are not set")

        qdrant_client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            timeout=10.0
        )
        logger.info("Qdrant client initialized successfully")

    return qdrant_client

async def init_database():
    """Initialize all database connections and collections"""
    # Initialize Postgres pool
    await init_postgres_pool()

    # Initialize Qdrant collections
    qdrant = get_qdrant_client()

    # Create content_chunks collection if it doesn't exist
    try:
        qdrant.get_collection("content_chunks")
        logger.info("Content chunks collection already exists")
    except:
        # Create collection with appropriate vector configuration
        qdrant.create_collection(
            collection_name="content_chunks",
            vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),  # Assuming Cohere embeddings
        )
        logger.info("Content chunks collection created")

    # Create conversation_sessions collection if it doesn't exist
    try:
        qdrant.get_collection("conversation_sessions")
        logger.info("Conversation sessions collection already exists")
    except:
        # Create collection for session-related embeddings if needed
        qdrant.create_collection(
            collection_name="conversation_sessions",
            vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
        )
        logger.info("Conversation sessions collection created")

async def close_database():
    """Close all database connections"""
    global postgres_pool, qdrant_client

    if postgres_pool:
        postgres_pool.close()
        await postgres_pool.wait_closed()
        logger.info("PostgreSQL connection pool closed")

    if qdrant_client:
        qdrant_client.close()
        logger.info("Qdrant client closed")

# Context manager for Postgres transactions
@asynccontextmanager
async def get_db_connection():
    """Context manager for getting a Postgres database connection"""
    pool = get_postgres_pool()
    async with pool.acquire() as connection:
        yield connection