from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # API Keys and URLs - with defaults for testing
    cohere_api_key: str = os.getenv('COHERE_API_KEY', 'dummy_key_for_testing')
    openai_api_key: str = os.getenv('OPENAI_API_KEY', '')  # Empty default for OpenAI
    qdrant_url: str = os.getenv('QDRANT_URL', 'https://dummy-url.qdrant.io')
    qdrant_api_key: str = os.getenv('QDRANT_API_KEY', 'dummy_key_for_testing')

    # Additional environment variables
    deployed_vercel_url: str = os.getenv('DEPLOYED_VERCEL_URL', 'https://example.com')
    api_key: str = os.getenv('API_KEY', 'test-api-key')

    # Configuration parameters
    chunk_size: int = 512
    chunk_overlap: int = 50
    batch_size: int = 10
    environment: str = "development"

    # Qdrant settings
    qdrant_collection_name: str = "textbook_content"

    # Model settings
    agent_model: str = "gpt-4o"

    # Rate limiting and timeouts
    request_timeout: int = 30
    max_retries: int = 5
    min_retry_delay: float = 1.0  # Minimum delay between retries in seconds
    max_retry_delay: float = 60.0  # Maximum delay between retries in seconds

    model_config = {
        "env_file": ".env",
        "env_file_encoding": 'utf-8',
        "extra": "ignore"  # This will ignore extra fields that are not defined
    }


# Create a singleton instance of settings
settings = Settings()