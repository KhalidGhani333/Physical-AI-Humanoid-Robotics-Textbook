"""
Logging utilities for the RAG Chatbot API
Provides standardized logging configuration and utilities
"""
import logging
import sys
from typing import Optional
from datetime import datetime
from enum import Enum

from src.config import settings


class LogLevels(Enum):
    """
    Standardized log levels for the application
    """
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def setup_logging(service_name: str = "rag-chatbot-api") -> logging.Logger:
    """
    Set up standardized logging for the application
    """
    # Create logger
    logger = logging.getLogger(service_name)

    # Set level based on config
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Avoid adding multiple handlers if logger already configured
    if logger.handlers:
        return logger

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False

    return logger


def log_api_call(
    logger: logging.Logger,
    endpoint: str,
    method: str,
    client_ip: str,
    user_agent: Optional[str] = None,
    response_time: Optional[float] = None,
    status_code: Optional[int] = None
):
    """
    Log API call details
    """
    log_data = {
        "endpoint": endpoint,
        "method": method,
        "client_ip": client_ip,
        "timestamp": datetime.utcnow().isoformat(),
        "response_time_ms": round(response_time * 1000, 2) if response_time else None,
        "status_code": status_code
    }

    if user_agent:
        log_data["user_agent"] = user_agent

    logger.info(f"API_CALL: {log_data}")


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: str = "",
    extra_data: Optional[dict] = None
):
    """
    Log error with context and additional data
    """
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "timestamp": datetime.utcnow().isoformat()
    }

    if extra_data:
        error_data.update(extra_data)

    logger.error(f"ERROR: {error_data}")


def log_content_operation(
    logger: logging.Logger,
    operation: str,
    document_id: Optional[str] = None,
    chunk_id: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """
    Log content-related operations
    """
    log_data = {
        "operation": operation,
        "timestamp": datetime.utcnow().isoformat()
    }

    if document_id:
        log_data["document_id"] = document_id

    if chunk_id:
        log_data["chunk_id"] = chunk_id

    if metadata:
        log_data["metadata"] = metadata

    logger.info(f"CONTENT_OP: {log_data}")


def log_retrieval(
    logger: logging.Logger,
    query: str,
    results_count: int,
    response_time: float,
    mode: str = "full_content"
):
    """
    Log retrieval operations
    """
    log_data = {
        "operation": "retrieval",
        "query_length": len(query),
        "results_count": results_count,
        "response_time_ms": round(response_time * 1000, 2),
        "mode": mode,
        "timestamp": datetime.utcnow().isoformat()
    }

    logger.info(f"RETRIEVAL: {log_data}")


def log_chat_interaction(
    logger: logging.Logger,
    session_id: str,
    user_input: str,
    response_length: int,
    sources_count: int = 0
):
    """
    Log chat interactions
    """
    log_data = {
        "operation": "chat_interaction",
        "session_id": session_id,
        "input_length": len(user_input),
        "response_length": response_length,
        "sources_count": sources_count,
        "timestamp": datetime.utcnow().isoformat()
    }

    logger.info(f"CHAT: {log_data}")


# Global logger instance
app_logger = setup_logging()