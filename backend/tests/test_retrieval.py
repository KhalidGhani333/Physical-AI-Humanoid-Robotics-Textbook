import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock

from src.main import app
from src.database.database import Base, get_db
from src.core.retrieval import RetrievalService

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

def test_retrieve_content():
    """Test content retrieval endpoint"""
    test_data = {
        "query": "What is artificial intelligence?",
        "top_k": 3
    }

    mock_results = [
        {
            "id": "test_id_1",
            "content": "Artificial intelligence (AI) is intelligence demonstrated by machines.",
            "document_id": "doc_1",
            "chunk_index": 0,
            "source_url": "https://example.com/doc1",
            "metadata": {},
            "score": 0.9
        }
    ]

    with patch('src.core.retrieval.RetrievalService.retrieve_and_rerank', new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.return_value = mock_results

        response = client.post("/api/v1/retrieve", json=test_data)

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "What is artificial intelligence?"
        assert len(data["results"]) == 1
        assert data["results"][0]["content"] == "Artificial intelligence (AI) is intelligence demonstrated by machines."

def test_retrieve_with_document_filter():
    """Test retrieval with specific document filtering"""
    test_data = {
        "query": "Robotics concepts",
        "document_ids": ["robot_doc_1", "robot_doc_2"],
        "top_k": 5
    }

    mock_results = [
        {
            "id": "test_id_1",
            "content": "Robotics is an interdisciplinary branch of engineering...",
            "document_id": "robot_doc_1",
            "chunk_index": 0,
            "source_url": "https://example.com/robotics",
            "metadata": {},
            "score": 0.85
        }
    ]

    with patch('src.core.retrieval.RetrievalService.retrieve_and_rerank', new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.return_value = mock_results

        response = client.post("/api/v1/retrieve", json=test_data)

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Robotics concepts"
        assert data["results"][0]["document_id"] == "robot_doc_1"

def test_retrieve_empty_query():
    """Test retrieval with empty query"""
    test_data = {
        "query": "",
        "top_k": 3
    }

    response = client.post("/api/v1/retrieve", json=test_data)

    # Should fail validation
    assert response.status_code == 422  # Validation error

def test_boundary_check():
    """Test content boundary check"""
    query = "What does this selected text say?"
    selected_text = "This selected text contains specific information about AI models."

    mock_results = [
        {
            "id": "test_id_1",
            "content": "This selected text contains specific information about AI models.",
            "document_id": "doc_1",
            "chunk_index": 0,
            "source_url": "https://example.com/doc1",
            "metadata": {},
            "score": 0.95
        }
    ]

    with patch('src.core.retrieval.RetrievalService.search_content', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_results

        response = client.post(
            "/api/v1/retrieve/boundary-check",
            params={"query": query, "selected_text": selected_text}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == query
        assert data["selected_text_provided"] is True
        assert data["can_answer_from_selected"] is True