"""
Middleware package for the RAG Chatbot API
"""
from .auth import api_key_auth
from .rate_limit import rate_limit_middleware
from .security import SecurityMiddleware, InputValidationMiddleware

__all__ = [
    "api_key_auth",
    "rate_limit_middleware",
    "SecurityMiddleware",
    "InputValidationMiddleware"
]


def add_middlewares(app):
    """
    Add all middlewares to the FastAPI app
    """
    # Add security middleware
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(InputValidationMiddleware)

    return app