# Quickstart Guide: Integrated RAG Chatbot for Digital Book / Website

## Overview
This guide provides a quick setup and usage guide for the RAG chatbot system. The system enables users to ask questions about digital book content with strict content boundary enforcement.

## Prerequisites
- Python 3.10+
- Qdrant Cloud account with cluster access
- Neon Postgres database
- Google Gemini API key
- Cohere API key

## Environment Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd backend
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables
Create a `.env` file with the following variables:
```env
QDRANT_URL=https://14fb50c8-7092-4dac-b4bb-0307eba15694.us-east-1-1.aws.cloud.qdrant.io
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.lfXmYTU5jvExx52sbt8o3d0xnFzAZ2i987Cgg0TTFkk
NEON_DB_URL=postgresql://neondb_owner:npg_kJBYfVSFI40o@ep-fragrant-king-ahlrdz58-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
GEMINI_API_KEY=your-gemini-api-key
COHERE_API_KEY=QjAOzx3HgGOOKjrY2mYgq9tCLnvQ5Emoi8UrjnSj
```

## Running the Application

### 1. Start the Development Server
```bash
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Initialize the Database
The application will automatically create necessary tables and collections on first run.

## Basic Usage

### 1. Ingest Content
First, you need to ingest your book content:

```bash
curl -X POST http://localhost:8000/v1/content/ingest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "source_type": "markdown",
    "source_path": "book/chapter1.md",
    "title": "Chapter 1: Introduction",
    "content": "# Introduction\n\nThis is the content of chapter 1...",
    "metadata": {
      "author": "Author Name",
      "publication_date": "2025-01-01",
      "language": "en"
    }
  }'
```

### 2. Create a Session
Create a conversation session:

```bash
curl -X POST http://localhost:8000/v1/chat/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "selected_text_mode": false
  }'
```

### 3. Ask Questions
Send a question to the chatbot:

```bash
curl -X POST http://localhost:8000/v1/chat/sessions/{session_id}/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "content": "What is the main concept discussed in this book?"
  }'
```

### 4. Selected Text Only Mode
To use the selected-text-only mode:

```bash
curl -X POST http://localhost:8000/v1/chat/sessions/{session_id}/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "content": "Explain this concept in more detail?",
    "selected_text": "The main concept discussed in this book is..."
  }'
```

## API Endpoints

### Content Management
- `POST /v1/content/ingest` - Ingest new content
- `GET /v1/content/{document_id}` - Get document status
- `DELETE /v1/content/{document_id}` - Remove content

### Chat & Conversation
- `POST /v1/chat/sessions` - Create new session
- `POST /v1/chat/sessions/{session_id}/messages` - Send message
- `GET /v1/chat/sessions/{session_id}/history` - Get conversation history

### Retrieval
- `POST /v1/retrieval/query` - Perform semantic search

## Configuration Options

### Content Chunking
- `CHUNK_SIZE`: Maximum characters per chunk (default: 1000)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 200)

### Retrieval Parameters
- `TOP_K`: Number of chunks to retrieve (default: 5)
- `MIN_RELEVANCE_SCORE`: Minimum relevance for retrieved chunks (default: 0.5)

### Session Management
- `SESSION_TIMEOUT`: Session expiration in minutes (default: 60)

## Testing

Run the test suite:

```bash
cd backend
pytest tests/
```

For specific test categories:
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# API contract tests
pytest tests/contract/
```

## Deployment

### Docker
Build and run with Docker:

```bash
docker build -t rag-chatbot .
docker run -p 8000:8000 -e QDRANT_URL=... -e GEMINI_API_KEY=... rag-chatbot
```

### Production Deployment
1. Set up production environment with SSL
2. Configure load balancing for high availability
3. Set up monitoring and logging
4. Implement backup strategies for data persistence

## Troubleshooting

### Common Issues
- **Content not found**: Verify that content has been properly ingested and indexed
- **Rate limiting**: Check API key and rate limit headers
- **Slow responses**: Optimize chunk size and retrieval parameters

### Logging
Check application logs for detailed error information:
- Access logs for API requests
- Error logs for system errors
- Performance logs for response times