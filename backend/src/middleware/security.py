from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
import time
from src.core.security import rate_limiter, input_validator

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle security concerns including rate limiting and input validation
    """
    async def dispatch(self, request: Request, call_next):
        # Rate limiting
        if not rate_limiter.is_allowed(request):
            reset_time = rate_limiter.get_reset_time(request)
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "type": "rate_limit_exceeded",
                        "message": "Rate limit exceeded. Please try again later.",
                        "reset_time": reset_time
                    }
                },
                headers={"Retry-After": str(reset_time - int(time.time()))}
            )

        # Input validation for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            # For now, we'll validate the request body if it's JSON
            if "application/json" in request.headers.get("content-type", ""):
                try:
                    body_bytes = await request.body()
                    if body_bytes:
                        # Basic validation - check for null bytes
                        if b'\x00' in body_bytes:
                            raise HTTPException(
                                status_code=400,
                                detail="Invalid input: null bytes detected"
                            )
                except Exception as e:
                    logger.error(f"Error validating request body: {str(e)}")
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid request body"
                    )

        response = await call_next(request)
        return response

class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware specifically for input validation
    """
    async def dispatch(self, request: Request, call_next):
        # Add security headers
        response = await call_next(request)

        # Add security headers to all responses (skip for /docs and /redoc in development)
        if not request.url.path.startswith(('/docs', '/redoc', '/openapi.json')):
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response