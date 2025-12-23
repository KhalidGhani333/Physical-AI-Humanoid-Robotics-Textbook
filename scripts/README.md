# Textbook Content Ingestion Script

This script automatically ingests all the textbook content from the `website/docs` directory into the RAG system so the chatbot can access it.

## Prerequisites

- Backend server must be running on the API endpoint (default: http://localhost:8000)
- All required API keys must be configured in the backend
- Database and vector store must be properly initialized

## Setup

1. Install dependencies:
   ```bash
   cd scripts
   npm install
   ```

## Usage

Run the ingestion script:
```bash
npm run ingest
```

Or with a custom API URL:
```bash
API_BASE_URL=http://your-server:8000 npm run ingest
```

## What it does

- Scans the `website/docs` directory for all markdown files
- Reads each markdown file's content
- Sends the content to the backend's ingestion API (`/api/v1/ingest`)
- Each file is ingested as a separate document with metadata

## Configuration

- `API_BASE_URL`: The URL of the backend server (default: http://localhost:8000)
- Documents are ingested with IDs prefixed with `textbook-` followed by the file path

## Notes

- Make sure the backend server is running before executing the script
- Each markdown file will be treated as a separate document in the RAG system
- The script includes error handling to continue processing even if some files fail