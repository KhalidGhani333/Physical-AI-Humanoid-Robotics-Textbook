"""
Rate limiting middleware for the RAG Chatbot API
Handles request rate limiting to prevent abuse
"""
import time
import logging
from collections import defaultdict, deque
from typing import Dict
from fastapi import HTTPException, status, Request
from src.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple in-memory rate limiter
    Tracks requests by IP address within a time window
    """

    def __init__(self):
        # Dictionary to store request timestamps for each IP
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.window_size = settings.RATE_LIMIT_WINDOW  # in seconds
        self.max_requests = settings.RATE_LIMIT_REQUESTS

    def is_allowed(self, ip_address: str) -> bool:
        """
        Check if a request from the given IP is allowed
        """
        current_time = time.time()

        # Remove requests that are outside the current window
        while (self.requests[ip_address] and
               current_time - self.requests[ip_address][0] > self.window_size):
            self.requests[ip_address].popleft()

        # Check if we're under the limit
        if len(self.requests[ip_address]) < self.max_requests:
            # Add current request
            self.requests[ip_address].append(current_time)
            return True

        # Rate limit exceeded
        return False

    def get_reset_time(self, ip_address: str) -> int:
        """
        Get the time when the rate limit will reset for this IP
        """
        if self.requests[ip_address]:
            oldest_request = self.requests[ip_address][0]
            reset_time = int(oldest_request + self.window_size)
            return reset_time
        return int(time.time())


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """
    FastAPI middleware function for rate limiting
    """
    client_ip = request.client.host

    # Check if request is allowed
    if not rate_limiter.is_allowed(client_ip):
        reset_time = rate_limiter.get_reset_time(client_ip)
        headers = {
            "X-RateLimit-Limit": str(rate_limiter.max_requests),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_time),
        }

        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers=headers
        )

    # Add rate limit headers to response
    remaining = rate_limiter.max_requests - len(rate_limiter.requests[client_ip])
    reset_time = rate_limiter.get_reset_time(client_ip)

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_requests)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset_time)

    return response