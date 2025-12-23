"""
Base service class for the RAG Chatbot API
Provides common functionality and patterns for all services
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.database.database import SessionLocal


class BaseService(ABC):
    """
    Abstract base class for all services in the application
    Provides common functionality like database session management
    """

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self.logger = logging.getLogger(self.__class__.__name__)

    @contextmanager
    def get_db_session(self):
        """
        Context manager to get a database session
        Handles session creation and cleanup automatically
        """
        if self.db_session:
            # Use provided session
            yield self.db_session
        else:
            # Create new session
            db = SessionLocal()
            try:
                yield db
            except SQLAlchemyError as e:
                db.rollback()
                self.logger.error(f"Database error: {str(e)}")
                raise
            finally:
                db.close()

    def handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """
        Standardized error handling for services
        """
        error_msg = f"Error in {context}: {str(error)}"
        self.logger.error(error_msg)
        return {
            "success": False,
            "error": str(error),
            "context": context
        }

    @abstractmethod
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """
        Validate input data before processing
        """
        pass

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """
        Execute the main business logic of the service
        """
        pass