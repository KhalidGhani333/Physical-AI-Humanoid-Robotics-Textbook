import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock

from src.main import app
from src.database.database import Base, get_db
from src.core.ingestion import ContentIngestionService

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Create test client
client = TestClient(app)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

def test_ingest_document():
    """Test document ingestion endpoint"""
    test_data = {
        "content": "This is a test document for the RAG chatbot system. It contains information about AI and robotics.",
        "document_id": "test_doc_1",
        "source_url": "https://example.com/test-doc",
        "metadata": {"author": "Test Author", "category": "AI"}
    }

    with patch('src.core.ingestion.ContentIngestionService.process_document', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = {
            "success": True,
            "document_id": "test_doc_1",
            "chunks_processed": 1,
            "message": "Successfully processed 1 content chunks"
        }

        response = client.post("/api/v1/ingest", json=test_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["document_id"] == "test_doc_1"
        assert data["chunks_processed"] == 1

def test_ingest_empty_content():
    """Test ingestion with empty content"""
    test_data = {
        "content": "",
        "document_id": "empty_doc",
        "source_url": "https://example.com/empty"
    }

    response = client.post("/api/v1/ingest", json=test_data)

    # Should fail validation
    assert response.status_code == 422  # Validation error

def test_ingest_large_content():
    """Test ingestion with large content"""
    large_content = "This is a large document. " * 1000  # Create a large string

    test_data = {
        "content": large_content,
        "document_id": "large_doc_1",
        "source_url": "https://example.com/large-doc"
    }

    with patch('src.core.ingestion.ContentIngestionService.process_document', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = {
            "success": True,
            "document_id": "large_doc_1",
            "chunks_processed": 5,
            "message": "Successfully processed 5 content chunks"
        }

        response = client.post("/api/v1/ingest", json=test_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["document_id"] == "large_doc_1"