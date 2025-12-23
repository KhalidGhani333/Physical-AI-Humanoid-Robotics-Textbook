import asyncio
import logging
import time
from typing import Dict, List, Optional
from fastapi import HTTPException, Request
from collections import defaultdict
from datetime import datetime, timedelta
import hashlib
import secrets

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Rate limiting implementation to prevent abuse of the API
    """
    def __init__(self, requests: int = 100, window: int = 60):
        self.requests = requests  # Number of requests allowed
        self.window = window      # Time window in seconds
        self.requests_log: Dict[str, List[float]] = defaultdict(list)

    def get_client_identifier(self, request: Request) -> str:
        """
        Get a unique identifier for the client
        """
        # Try to get API key from headers
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
        if api_key:
            # Hash the API key for privacy
            return hashlib.sha256(api_key.encode()).hexdigest()[:16]

        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        return client_ip

    def is_allowed(self, request: Request) -> bool:
        """
        Check if the request is allowed based on rate limits
        """
        client_id = self.get_client_identifier(request)
        now = time.time()

        # Clean up old requests outside the window
        self.requests_log[client_id] = [
            req_time for req_time in self.requests_log[client_id]
            if now - req_time < self.window
        ]

        # Check if limit exceeded
        if len(self.requests_log[client_id]) >= self.requests:
            return False

        # Add current request to log
        self.requests_log[client_id].append(now)
        return True

    def get_reset_time(self, request: Request) -> int:
        """
        Get the time when the rate limit will reset for this client
        """
        client_id = self.get_client_identifier(request)
        if client_id in self.requests_log:
            oldest_request = min(self.requests_log[client_id])
            return int(oldest_request + self.window)
        return int(time.time() + self.window)

class APIKeyManager:
    """
    Manage API keys for authentication
    """
    def __init__(self):
        self.api_keys: Dict[str, Dict] = {}

    def create_api_key(self, name: str, permissions: List[str] = None) -> str:
        """
        Create a new API key
        """
        api_key = secrets.token_urlsafe(32)
        self.api_keys[api_key] = {
            "name": name,
            "created_at": datetime.utcnow(),
            "permissions": permissions or ["read", "write"],
            "active": True
        }
        logger.info(f"Created new API key for: {name}")
        return api_key

    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate if an API key is valid and active
        """
        if api_key in self.api_keys:
            return self.api_keys[api_key]["active"]
        return False

    def revoke_api_key(self, api_key: str) -> bool:
        """
        Revoke an API key
        """
        if api_key in self.api_keys:
            self.api_keys[api_key]["active"] = False
            logger.info(f"Revoked API key")
            return True
        return False

    def get_api_key_info(self, api_key: str) -> Optional[Dict]:
        """
        Get information about an API key
        """
        if api_key in self.api_keys:
            return self.api_keys[api_key]
        return None

class InputValidator:
    """
    Validate and sanitize user inputs
    """
    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Sanitize user input to prevent injection attacks
        """
        if not text:
            return text

        # Remove null bytes and control characters
        sanitized = text.replace('\x00', '').strip()

        # Additional sanitization can be added here based on requirements
        # For example, removing specific patterns, limiting length, etc.

        return sanitized

    @staticmethod
    def validate_query(query: str) -> bool:
        """
        Validate if a query is safe to process
        """
        if not query or len(query.strip()) == 0:
            return False

        # Check for minimum length
        if len(query.strip()) < 1:
            return False

        # Check for maximum length
        if len(query) > 2000:  # Adjust as needed
            return False

        # Additional validation can be added here
        return True

    @staticmethod
    def validate_document_content(content: str) -> bool:
        """
        Validate document content before ingestion
        """
        if not content:
            return False

        # Check for maximum size (e.g., 10MB)
        if len(content.encode('utf-8')) > 10 * 1024 * 1024:
            return False

        return True

# Global instances
rate_limiter = RateLimiter(requests=100, window=60)  # 100 requests per minute
api_key_manager = APIKeyManager()
input_validator = InputValidator()