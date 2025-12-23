# Data Model: Integrated RAG Chatbot for Digital Book / Website

## Entity Models

### 1. Content Chunk
Represents a segment of ingested book content with associated embedding vector and metadata.

**Fields**:
- `id` (UUID): Unique identifier for the chunk
- `content` (Text): The actual text content of the chunk
- `embedding` (Vector): The embedding vector for semantic search
- `metadata` (JSON): Additional metadata including source, page, section, etc.
  - `source_document`: Identifier for the source document
  - `page_number`: Page number in the source (if applicable)
  - `section_title`: Title of the section containing this chunk
  - `position`: Position of the chunk within the document
  - `created_at`: Timestamp of when the chunk was created
- `checksum` (String): SHA-256 hash of the content for deduplication
- `created_at` (DateTime): Timestamp of creation
- `updated_at` (DateTime): Timestamp of last update

**Relationships**:
- Belongs to one `SourceDocument`
- Associated with multiple `RetrievalResult` entries

**Validation Rules**:
- Content must not exceed 2000 characters
- Embedding vector must have fixed dimension (per embedding model)
- Checksum must be valid SHA-256 hash
- Metadata must include source_document identifier

### 2. Source Document
Represents the original document from which content chunks were derived.

**Fields**:
- `id` (UUID): Unique identifier for the document
- `title` (String): Title of the document
- `source_type` (String): Type of source (e.g., "markdown", "pdf", "html")
- `source_path` (String): Path or URL of the original document
- `version` (String): Version identifier for the document
- `metadata` (JSON): Additional document metadata
  - `author`: Author of the document
  - `publication_date`: Date of publication
  - `word_count`: Total word count in the document
  - `language`: Language of the document
- `status` (String): Processing status (e.g., "ingested", "processing", "error")
- `chunk_count` (Integer): Number of chunks derived from this document
- `created_at` (DateTime): Timestamp of creation
- `updated_at` (DateTime): Timestamp of last update

**Relationships**:
- Has many `ContentChunk` entries
- Associated with many `RetrievalResult` entries through chunks

**Validation Rules**:
- Title must be provided
- Source_type must be one of the supported types
- Status must be one of the valid statuses
- Version must follow semantic versioning

### 3. Conversation Session
Represents a user's ongoing interaction with the chatbot, maintaining context and history.

**Fields**:
- `id` (UUID): Unique identifier for the session
- `user_id` (UUID): Identifier for the user (optional for anonymous sessions)
- `session_metadata` (JSON): Additional session metadata
  - `created_ip`: IP address of the session creator
  - `user_agent`: User agent string of the client
  - `selected_text_mode`: Whether selected-text-only mode is active
  - `selected_text_chunks`: IDs of chunks from user-selected text (when applicable)
- `expires_at` (DateTime): Timestamp when the session expires
- `created_at` (DateTime): Timestamp of creation
- `updated_at` (DateTime): Timestamp of last update

**Relationships**:
- Has many `ChatMessage` entries
- Associated with many `RetrievalResult` entries through messages

**Validation Rules**:
- Expires_at must be in the future
- Selected_text_chunks must be valid when selected_text_mode is active
- Session must be active (not expired) for new messages

### 4. Chat Message
Represents a single turn in a conversation, including user query and system response.

**Fields**:
- `id` (UUID): Unique identifier for the message
- `session_id` (UUID): Reference to the conversation session
- `role` (String): Role of the message ("user" or "assistant")
- `content` (Text): The actual content of the message
- `retrieval_results` (JSON): IDs of content chunks used in generating the response
- `sources` (JSON): Source citations for the response content
- `timestamp` (DateTime): When the message was created
- `metadata` (JSON): Additional message metadata
  - `response_time`: Time taken to generate the response
  - `model_used`: Model used for generation
  - `tokens_used`: Number of tokens in the request/response

**Relationships**:
- Belongs to one `ConversationSession`
- Associated with multiple `ContentChunk` entries through retrieval_results
- Associated with multiple `RetrievalResult` entries

**Validation Rules**:
- Role must be either "user" or "assistant"
- Session must be active
- Content must not be empty
- Retrieval_results must be valid chunk IDs when role is "assistant"

### 5. Retrieval Result
Represents the content fragments retrieved from the vector database based on a query.

**Fields**:
- `id` (UUID): Unique identifier for the retrieval result
- `session_id` (UUID): Reference to the conversation session
- `query` (Text): The original query that triggered the retrieval
- `retrieved_chunks` (JSON): Array of content chunk IDs that were retrieved
- `relevance_scores` (JSON): Relevance scores for each retrieved chunk
- `mode` (String): Retrieval mode ("full_content" or "selected_text_only")
- `timestamp` (DateTime): When the retrieval was performed
- `metadata` (JSON): Additional retrieval metadata
  - `query_embedding`: The embedding used for the search
  - `search_params`: Parameters used for the vector search

**Relationships**:
- Belongs to one `ConversationSession`
- Associated with multiple `ContentChunk` entries through retrieved_chunks
- Associated with many `ChatMessage` entries

**Validation Rules**:
- Mode must be one of the valid modes
- Retrieved_chunks must be valid content chunk IDs
- Relevance_scores must match the length of retrieved_chunks

## State Transitions

### Source Document States
- `pending` → `processing`: When ingestion begins
- `processing` → `ingested`: When ingestion completes successfully
- `processing` → `error`: When ingestion fails
- `ingested` → `updating`: When document is being reprocessed
- `updating` → `ingested`: When update completes successfully
- `updating` → `error`: When update fails

### Conversation Session States
- `active` → `expired`: When session reaches expiration time
- `active` → `archived`: When session is explicitly archived
- `active` → `active` (mode change): When switching between full-content and selected-text modes

## Indexes and Performance Considerations

### Content Chunk Indexes
- Primary index on `id`
- Composite index on `source_document` and `position` for document order
- Index on `checksum` for deduplication
- Vector index on `embedding` for similarity search (handled by Qdrant)

### Source Document Indexes
- Primary index on `id`
- Index on `source_path` for uniqueness
- Index on `status` for filtering by processing status

### Conversation Session Indexes
- Primary index on `id`
- Index on `expires_at` for cleanup
- Index on `user_id` for user-specific queries

### Chat Message Indexes
- Primary index on `id`
- Index on `session_id` and `timestamp` for chronological ordering
- Index on `role` for filtering by message type

## Data Integrity Constraints

1. **Referential Integrity**: All foreign key relationships must be validated
2. **Uniqueness**: Checksum-based deduplication for content chunks
3. **Temporal Consistency**: Timestamps must follow logical order
4. **Content Boundary Enforcement**: Retrieved chunks must match the requested mode (full content vs selected text only)
5. **Session Validation**: Messages must belong to active sessions