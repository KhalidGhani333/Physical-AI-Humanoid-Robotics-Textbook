import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql://neondb_owner:npg_kJBYfVSFI40o@ep-fragrant-king-ahlrdz58-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require",
        description="Neon Serverless Postgres connection string"
    )

    # Additional settings from .env
    NEON_DB_URL: str = Field(
        default="",
        description="Neon Serverless Postgres connection string (for backward compatibility)"
    )
    APP_ENV: str = Field(
        default="development",
        description="Application environment"
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )

    # Qdrant settings
    QDRANT_URL: str = Field(
        default="https://14fb50c8-7092-4dac-b4bb-0307eba15694.us-east-1-1.aws.cloud.qdrant.io",
        description="Qdrant Cloud cluster URL"
    )
    QDRANT_API_KEY: str = Field(
        default="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.lfXmYTU5jvExx52sbt8o3d0xnFzAZ2i987Cgg0TTFkk",
        description="Qdrant API key"
    )

    # Gemini API settings
    GEMINI_API_KEY: str = Field(
        default="",
        description="Google Gemini API key - optional but required for AI responses"
    )

    # Cohere API settings
    COHERE_API_KEY: str = Field(
        default="",
        description="Cohere API key for embeddings - optional but required for full functionality"
    )

    # Application settings
    APP_NAME: str = "RAG Chatbot API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100  # requests per minute
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # Content processing
    CHUNK_SIZE: int = 1000  # characters per chunk
    CHUNK_OVERLAP: int = 200  # overlap between chunks

    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Validate required settings
def validate_settings():
    if not settings.GEMINI_API_KEY:
        print("WARNING: GEMINI_API_KEY not found in environment variables. AI features will be limited.")
        print("To enable AI responses, set GEMINI_API_KEY in your .env file with a valid Google Gemini API key.")

    if not settings.COHERE_API_KEY:
        print("WARNING: COHERE_API_KEY not found in environment variables. Embedding features will be limited.")
        print("To enable full RAG functionality, set COHERE_API_KEY in your .env file with a valid Cohere API key.")

# Validate settings on import
validate_settings()