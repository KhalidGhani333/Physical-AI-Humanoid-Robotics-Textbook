# API Contracts: Integrated RAG Chatbot for Digital Book / Website

## OpenAPI Specification for RAG Chatbot API

### Base URL
```
https://api.yourdomain.com/v1
```

### Content Types
- Request: `application/json`
- Response: `application/json`

---

## 1. Content Ingestion Endpoints

### POST /content/ingest
Ingest content from various formats (Markdown, HTML, PDF text extracts) into the RAG system.

#### Request
```json
{
  "source_type": "markdown",
  "source_path": "path/to/document.md",
  "title": "Document Title",
  "content": "# Document Title\n\nThis is the document content...",
  "metadata": {
    "author": "Author Name",
    "publication_date": "2025-01-01",
    "language": "en"
  }
}
```

#### Response (Success 201)
```json
{
  "document_id": "uuid-string",
  "status": "processing",
  "chunk_count": 15,
  "estimated_processing_time": 30
}
```

#### Response (Error 400)
```json
{
  "error": "validation_error",
  "message": "Content must be provided",
  "details": {
    "content": ["Content is required"]
  }
}
```

#### Response (Error 500)
```json
{
  "error": "ingestion_failed",
  "message": "Failed to process document content"
}
```

### GET /content/{document_id}
Get the status of a content ingestion job.

#### Response (Success 200)
```json
{
  "id": "uuid-string",
  "title": "Document Title",
  "status": "ingested",
  "chunk_count": 15,
  "source_type": "markdown",
  "created_at": "2025-12-14T10:30:00Z",
  "updated_at": "2025-12-14T10:30:30Z"
}
```

### DELETE /content/{document_id}
Remove a document and its associated chunks from the system.

#### Response (Success 200)
```json
{
  "status": "deleted",
  "document_id": "uuid-string"
}
```

---

## 2. Chat and Conversation Endpoints

### POST /chat/sessions
Create a new conversation session.

#### Request
```json
{
  "user_id": "optional-user-uuid",
  "selected_text_mode": false,
  "selected_text_chunks": [],
  "session_metadata": {
    "user_agent": "user-agent-string",
    "client_info": "additional client info"
  }
}
```

#### Response (Success 201)
```json
{
  "session_id": "uuid-string",
  "expires_at": "2025-12-14T11:30:00Z",
  "selected_text_mode": false
}
```

### POST /chat/sessions/{session_id}/messages
Send a message to the chatbot and receive a response.

#### Request
```json
{
  "content": "What is the main concept discussed in this book?",
  "selected_text": "Optional text selected by user for selected-text-only mode",
  "context_window": 5
}
```

#### Response (Success 200)
```json
{
  "response": "The main concept discussed in this book is...",
  "sources": [
    {
      "chunk_id": "chunk-uuid",
      "content": "Relevant content excerpt...",
      "page_number": 15,
      "section_title": "Chapter 2: Main Concepts"
    }
  ],
  "retrieval_info": {
    "mode": "full_content",
    "retrieved_chunks": ["chunk-uuid-1", "chunk-uuid-2"],
    "relevance_scores": [0.95, 0.87]
  },
  "message_id": "message-uuid",
  "timestamp": "2025-12-14T10:35:00Z"
}
```

#### Response (Error 400 - Out of Context)
```json
{
  "response": "I cannot answer this question based on the provided content.",
  "reason": "no_relevant_content",
  "message_id": "message-uuid",
  "timestamp": "2025-12-14T10:35:00Z"
}
```

### GET /chat/sessions/{session_id}/history
Retrieve conversation history for a session.

#### Response (Success 200)
```json
{
  "session_id": "uuid-string",
  "messages": [
    {
      "id": "message-uuid",
      "role": "user",
      "content": "What is the main concept?",
      "timestamp": "2025-12-14T10:30:00Z"
    },
    {
      "id": "message-uuid",
      "role": "assistant",
      "content": "The main concept is...",
      "sources": [{"chunk_id": "chunk-uuid", "content": "..."}],
      "timestamp": "2025-12-14T10:30:05Z"
    }
  ]
}
```

---

## 3. Retrieval Endpoints

### POST /retrieval/query
Perform a semantic search on the content corpus.

#### Request
```json
{
  "query": "Main concepts in the book",
  "mode": "full_content",  // or "selected_text_only"
  "selected_text_chunks": ["chunk-uuid-1"],  // required if mode is "selected_text_only"
  "top_k": 5,
  "min_relevance_score": 0.5
}
```

#### Response (Success 200)
```json
{
  "query": "Main concepts in the book",
  "results": [
    {
      "chunk_id": "chunk-uuid-1",
      "content": "The main concept discussed in this book is...",
      "relevance_score": 0.95,
      "metadata": {
        "source_document": "doc-uuid",
        "page_number": 15,
        "section_title": "Chapter 2: Main Concepts"
      }
    }
  ],
  "mode": "full_content"
}
```

---

## 4. Content Management Endpoints

### GET /content/documents
List all ingested documents.

#### Response (Success 200)
```json
{
  "documents": [
    {
      "id": "uuid-string",
      "title": "Document Title",
      "status": "ingested",
      "chunk_count": 15,
      "source_type": "markdown",
      "created_at": "2025-12-14T10:30:00Z"
    }
  ],
  "total_count": 1,
  "page": 1,
  "per_page": 10
}
```

### GET /content/chunks/{chunk_id}
Retrieve a specific content chunk.

#### Response (Success 200)
```json
{
  "id": "chunk-uuid",
  "content": "The content of the specific chunk...",
  "metadata": {
    "source_document": "doc-uuid",
    "page_number": 15,
    "section_title": "Chapter 2: Main Concepts",
    "position": 3
  },
  "created_at": "2025-12-14T10:30:00Z"
}
```

---

## 5. Error Responses

All API endpoints follow the same error response format:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    // Optional field with additional error details
  },
  "timestamp": "2025-12-14T10:30:00Z"
}
```

### Common Error Codes:
- `validation_error`: Request validation failed
- `not_found`: Requested resource does not exist
- `unauthorized`: Authentication required or failed
- `rate_limit_exceeded`: Rate limit exceeded
- `content_retrieval_failed`: Failed to retrieve relevant content
- `llm_generation_failed`: Failed to generate response from LLM
- `session_expired`: Conversation session has expired
- `content_boundary_violation`: Request violates content boundary constraints

---

## 6. Authentication

All endpoints require API key authentication via header:

```
Authorization: Bearer YOUR_API_KEY
```

Or alternatively:
```
X-API-Key: YOUR_API_KEY
```

---

## 7. Rate Limiting

All endpoints are subject to rate limiting:
- Standard users: 100 requests per minute per IP
- Premium users: 1000 requests per minute per API key
- Burst allowance: 10 requests over the limit before blocking

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the current window resets