from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from src.database.database import engine
import logging
from typing import Optional

logger = logging.getLogger(__name__)

async def check_db_connection():
    """
    Check if the database connection is working
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False

async def check_qdrant_connection(qdrant_client):
    """
    Check if the Qdrant connection is working
    """
    try:
        # Try to get collections to verify connection
        collections = qdrant_client.get_collections()
        logger.info(f"Qdrant connection successful. Found {len(collections.collections)} collections")
        return True
    except Exception as e:
        logger.error(f"Qdrant connection check failed: {str(e)}")
        return False

def create_vector_collection(qdrant_client, collection_name: str, vector_size: int = 1024):
    """
    Create a vector collection in Qdrant if it doesn't exist
    """
    try:
        # Check if collection exists
        try:
            qdrant_client.get_collection(collection_name)
            logger.info(f"Collection '{collection_name}' already exists")
            return True
        except:
            # Collection doesn't exist, create it
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "content": {
                        "size": vector_size,
                        "distance": "Cosine"
                    }
                }
            )
            logger.info(f"Created collection '{collection_name}' with vector size {vector_size}")
            return True
    except Exception as e:
        logger.error(f"Failed to create collection '{collection_name}': {str(e)}")
        return False

def init_database():
    """
    Initialize database connections and create required collections
    """
    logger.info("Initializing database connections...")

    # Import models to register them with SQLAlchemy
    from src.models.content import ContentChunk, SourceDocument
    from src.models.conversation import ConversationSession
    from src.models.chat import ChatMessage, RetrievalResult

    # Create tables
    from src.database.database import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

    # Initialize Qdrant collections
    from src.database.database import qdrant_client
    create_vector_collection(qdrant_client, "content_chunks")
    logger.info("Qdrant collections initialized")