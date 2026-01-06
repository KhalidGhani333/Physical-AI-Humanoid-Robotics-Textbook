# RAG Content Ingestion System

A backend service for crawling and extracting content from deployed textbook website URLs, chunking content deterministically, generating embeddings using Cohere models, and storing embeddings with metadata in Qdrant Cloud for RAG usage.

## Features

- **Content Extraction**: Crawls and extracts structured content from deployed textbook website URLs
- **Text Chunking**: Deterministic chunking with configurable size and overlap to maintain semantic boundaries
- **Embedding Generation**: Generates vector embeddings using Cohere embedding models
- **Vector Storage**: Stores embeddings and metadata in Qdrant Cloud with proper indexing
- **API Interface**: RESTful API for managing ingestion jobs
- **Duplicate Detection**: Identifies and handles duplicate content to prevent redundancy
- **Incremental Ingestion**: Detects and updates only changed content
- **Performance Monitoring**: Tracks metrics and performance of the ingestion pipeline

## Prerequisites

- Python 3.10 or higher
- uv package manager
- Access to Cohere API (API key)
- Access to Qdrant Cloud (URL and API key)

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. **Navigate to backend directory**
   ```bash
   cd backend
   ```

3. **Install dependencies with uv**
   ```bash
   uv sync
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` file with your API keys:
   ```env
   COHERE_API_KEY=your_cohere_api_key_here
   QDRANT_URL=your_qdrant_cloud_url_here
   QDRANT_API_KEY=your_qdrant_api_key_here
   ```

## Configuration

The system uses Pydantic Settings for configuration management. Key settings include:

- `COHERE_API_KEY`: Your Cohere API key for embedding generation
- `QDRANT_URL`: Your Qdrant Cloud instance URL
- `QDRANT_API_KEY`: Your Qdrant Cloud API key
- `CHUNK_SIZE`: Maximum size of text chunks (default: 512 tokens)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 50 tokens)
- `BATCH_SIZE`: Number of embeddings to process per API call (default: 10)

## Usage

### Running the Service

Start the API server:

```bash
cd backend
uv run python src/main.py
```

The API will be available at `http://localhost:8000`.

### Command Line Interface

Run the ingestion pipeline directly from the command line:

```bash
uv run python src/main.py --urls "https://example.com/page1" "https://example.com/page2"
```

Additional options:
```bash
uv run python src/main.py --urls "https://example.com/page1" --chunk-size 256 --chunk-overlap 25 --batch-size 5
```

### API Endpoints

#### Start Ingestion Job
```
POST /api/v1/ingestion/jobs
```

Starts a new content ingestion job for specified URLs.

Request body:
```json
{
  "urls": [
    "https://example.com/textbook/chapter1",
    "https://example.com/textbook/chapter2"
  ],
  "config": {
    "chunk_size": 512,
    "chunk_overlap": 50,
    "batch_size": 10
  }
}
```

#### Get Ingestion Job Status
```
GET /api/v1/ingestion/jobs/{job_id}
```

Retrieves the current status of an ingestion job.

#### List Ingestion Jobs
```
GET /api/v1/ingestion/jobs
```

Retrieves a list of recent ingestion jobs.

#### Trigger Full Re-ingestion
```
POST /api/v1/ingestion/reingest
```

Triggers a full re-ingestion of all textbook content.

## Architecture

### Core Components

- **ContentExtractor**: Extracts clean text from HTML pages using BeautifulSoup
- **TextChunker**: Splits content into manageable chunks with overlap
- **EmbeddingGenerator**: Creates vector embeddings using Cohere API
- **VectorStore**: Stores embeddings in Qdrant Cloud with metadata
- **IngestionWorkflow**: Orchestrates the entire ingestion pipeline
- **DuplicateDetector**: Identifies and handles duplicate content
- **MetricsService**: Collects performance metrics

### Data Models

- **DocumentChunk**: Represents a segment of extracted content with embedding
- **IngestionJob**: Tracks the progress and status of ingestion jobs
- **SourceMetadata**: Stores information about content origin

## Development

### Running Tests

Unit tests:
```bash
cd backend
python -m pytest tests/unit/
```

Integration tests:
```bash
cd backend
python -m pytest tests/integration/
```

### Project Structure

```
backend/
├── src/
│   ├── models/          # Data models
│   ├── services/        # Core services
│   ├── utils/           # Utility functions
│   ├── config/          # Configuration
│   └── main.py          # Main application entry point
├── tests/
│   ├── unit/            # Unit tests
│   └── integration/     # Integration tests
├── docs/                # Documentation
├── pyproject.toml       # Project dependencies
└── .env.example         # Environment variables template
```

## API Authentication

All API endpoints require API key authentication via the `X-API-Key` header:

```
X-API-Key: your-api-key-here
```

## Rate Limiting

API endpoints are rate-limited to prevent overuse of external services:
- 100 requests per minute per API key
- 10 concurrent ingestion jobs per account

## Performance Monitoring

The system collects various metrics:
- Content extraction success/failure rates
- Chunking duration and chunk counts
- Embedding generation duration
- Vector storage duration
- Ingestion pipeline duration
- URL processing duration

Metrics can be accessed via the metrics service.

## Error Handling

The system handles various edge cases:
- Inaccessible URLs with retry logic
- Large documents with configurable chunking
- Service unavailability with graceful degradation
- Duplicate content detection and filtering
- Network issues with timeouts and retries
- Invalid content formats with error recovery
- API limits with rate limiting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

[Specify license here]