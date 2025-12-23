from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
import logging
import time
import traceback
from typing import Callable, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log incoming requests and responses
    """
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()

        # Log request
        logger.info(f"Request: {request.method} {request.url}")
        if request.query_params:
            logger.info(f"Query params: {request.query_params}")

        try:
            response = await call_next(request)
        except Exception as e:
            # Log exceptions
            logger.error(f"Exception in {request.method} {request.url}: {str(e)}")
            logger.error(traceback.format_exc())
            raise e

        # Calculate response time
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        # Log response
        logger.info(f"Response: {response.status_code} - Process time: {process_time:.4f}s")

        return response

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle errors and format responses consistently
    """
    async def dispatch(self, request: Request, call_next: Callable):
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            logger.error(f"HTTP Exception: {e.status_code} - {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "type": "http_exception",
                        "message": str(e.detail),
                        "status_code": e.status_code
                    }
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "type": "internal_error",
                        "message": "An unexpected error occurred"
                    }
                }
            )

def add_middlewares(app):
    """
    Add all required middlewares to the FastAPI app
    """
    # Add security middleware first (rate limiting, etc.)
    from src.middleware.security import SecurityMiddleware, InputValidationMiddleware
    app.add_middleware(SecurityMiddleware)

    # Add logging middleware
    app.add_middleware(LoggingMiddleware)

    # Add error handling middleware
    app.add_middleware(ErrorHandlingMiddleware)

    # Add input validation and security headers
    app.add_middleware(InputValidationMiddleware)