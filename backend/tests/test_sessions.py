import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock
import uuid
from datetime import datetime, timedelta

from src.main import app
from src.database.database import Base, get_db
from src.core.session import SessionManager

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

def test_create_session():
    """Test session creation endpoint"""
    test_data = {
        "mode": "full_content",
        "expires_in_minutes": 60
    }

    response = client.post("/api/v1/sessions", json=test_data)

    assert response.status_code == 200
    data = response.json()
    assert "session_token" in data
    assert data["mode"] == "full_content"
    assert "expires_at" in data

def test_create_selected_text_session():
    """Test session creation with selected text constraint"""
    test_data = {
        "mode": "selected_text_only",
        "selected_text_constraint": "This is the selected text that should be used for all queries.",
        "expires_in_minutes": 30
    }

    response = client.post("/api/v1/sessions", json=test_data)

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "selected_text_only"
    # Note: metadata field might not be returned as expected based on schema

def test_get_session():
    """Test getting session information"""
    # First create a session
    create_response = client.post("/api/v1/sessions", json={"mode": "full_content"})
    assert create_response.status_code == 200
    session_data = create_response.json()
    session_token = session_data["session_token"]

    # Now get the session
    response = client.get(f"/api/v1/sessions/{session_token}")

    assert response.status_code == 200
    data = response.json()
    assert data["session_token"] == session_token
    assert data["mode"] == "full_content"

def test_get_nonexistent_session():
    """Test getting a nonexistent session"""
    fake_session_token = str(uuid.uuid4())

    response = client.get(f"/api/v1/sessions/{fake_session_token}")

    # Should return 404
    assert response.status_code == 404

def test_delete_session():
    """Test deleting a session"""
    # First create a session
    create_response = client.post("/api/v1/sessions", json={"mode": "full_content"})
    assert create_response.status_code == 200
    session_data = create_response.json()
    session_token = session_data["session_token"]

    # Now delete the session
    response = client.delete(f"/api/v1/sessions/{session_token}")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data

def test_session_history():
    """Test getting conversation history for a session"""
    # First create a session
    create_response = client.post("/api/v1/sessions", json={"mode": "full_content"})
    assert create_response.status_code == 200
    session_data = create_response.json()
    session_token = session_data["session_token"]

    # Now get the history (should be empty initially)
    response = client.get(f"/api/v1/sessions/{session_token}/history")

    assert response.status_code == 200
    data = response.json()
    assert data["session_token"] == session_token

def test_clear_conversation_history():
    """Test clearing conversation history"""
    # First create a session
    create_response = client.post("/api/v1/sessions", json={"mode": "full_content"})
    assert create_response.status_code == 200
    session_data = create_response.json()
    session_token = session_data["session_token"]

    # Now clear the history
    response = client.post(f"/api/v1/sessions/{session_token}/clear-history")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data

def test_session_cleanup():
    """Test cleaning up expired sessions"""
    response = client.post("/api/v1/sessions/cleanup")

    assert response.status_code == 200
    data = response.json()
    assert "deleted_sessions" in data