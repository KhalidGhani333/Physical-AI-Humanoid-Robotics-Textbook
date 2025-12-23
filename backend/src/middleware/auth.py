"""
Authentication middleware for the RAG Chatbot API
Handles API key validation and authentication
"""
import os
import logging
from typing import Optional
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader

logger = logging.getLogger(__name__)


class APIKeyAuth:
    """
    API Key authentication handler
    """

    def __init__(self):
        # Get the expected API key from environment or config
        self.expected_api_key = os.getenv("API_KEY", "test-api-key")
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
        self.bearer_scheme = HTTPBearer(auto_error=False)

    async def authenticate(self, request: Request) -> bool:
        """
        Authenticate request using API key
        Supports both X-API-Key header and Bearer token
        """
        # Check X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if api_key and api_key == self.expected_api_key:
            return True

        # Check Authorization header for Bearer token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            if token == self.expected_api_key:
                return True

        # Check query parameter as fallback
        query_api_key = request.query_params.get("api_key")
        if query_api_key and query_api_key == self.expected_api_key:
            return True

        return False

    async def validate_api_key(self, request: Request) -> bool:
        """
        Validate API key and raise HTTPException if invalid
        """
        is_valid = await self.authenticate(request)
        if not is_valid:
            logger.warning(f"Invalid API key access attempt from {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key"
            )
        return True


# Global instance
api_key_auth = APIKeyAuth()