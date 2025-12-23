# Chatbot Setup Guide

## Backend Setup

1. **Install Python dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   - Copy `.env.example` to `.env`
   - Add your API keys:
     - `GEMINI_API_KEY`: Your Google Gemini API key
     - `COHERE_API_KEY`: Your Cohere API key (for embeddings)
     - `DATABASE_URL`: PostgreSQL connection string (or use a local database)
     - `QDRANT_URL` and `QDRANT_API_KEY`: Qdrant vector database credentials

3. **Start the backend server**:
   ```bash
   cd src
   python main.py
   ```
   The backend will start on `http://localhost:8000` by default.

## Frontend Setup

1. **Install Node.js dependencies**:
   ```bash
   cd website
   npm install
   ```

2. **Set up environment variables** (optional):
   - Copy `.env.example` to `.env`
   - Set `REACT_APP_API_BASE_URL` if using a different backend URL

3. **Start the frontend**:
   ```bash
   npm start
   ```

## Required Services

The chatbot requires the following external services:
- **Google Gemini API**: For AI responses (requires access to one of: gemini-1.5-flash-001, gemini-1.5-flash, gemini-1.0-pro-001, or gemini-1.0-pro models) - API key required
- **Cohere API**: For embeddings - API key required
- **PostgreSQL Database**: For storing conversation history
- **Qdrant Vector Database**: For vector storage and retrieval

## API Key Setup

To enable full functionality of the chatbot, you need to set up the following API keys:

1. **Google Gemini API Key**:
   - Go to Google AI Studio (https://aistudio.google.com/)
   - Create an account and get an API key for Gemini
   - Add it to your `.env` file as `GEMINI_API_KEY`

2. **Cohere API Key**:
   - Go to Cohere (https://cohere.com/)
   - Create an account and get an API key
   - Add it to your `.env` file as `COHERE_API_KEY`

Without these API keys, the chatbot will run but will have limited functionality.

## Troubleshooting

- If you see "Connection failed" errors, ensure the backend server is running on port 8000
- If you see API key errors, verify all required API keys are set in the `.env` file
- If you see "Authentication error" messages, verify your GEMINI_API_KEY and COHERE_API_KEY are correct and have proper permissions
- If you see "Quota exceeded" messages, check your API billing configuration
- If you see "Model not found" errors, ensure you have access to at least one of these models: gemini-1.5-flash-001, gemini-1.5-flash, gemini-1.0-pro-001, or gemini-1.0-pro
- If database errors occur, ensure PostgreSQL is running and credentials are correct
- If vector database errors occur, ensure Qdrant is accessible with the provided credentials
- If you see "No relevant context found" errors, ensure content has been ingested into the system via the /api/v1/ingest endpoint

## Content Ingestion

To make the chatbot knowledgeable about your textbook content:

### Automatic Ingestion (Recommended)

1. Ensure your backend server is running
2. Navigate to the scripts directory:
   ```bash
   cd scripts
   npm install
   ```
3. Run the automatic ingestion script:
   ```bash
   npm run ingest
   ```
   This will automatically find all markdown files in the `website/docs` directory and ingest them into the RAG system.

### Manual Ingestion

If you prefer to manually add content, use the ingestion API:

```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your textbook content about Physical AI & Humanoid Robotics...",
    "document_id": "physical-ai-textbook",
    "source_url": "optional-source-url",
    "metadata": {"title": "Physical AI & Humanoid Robotics Textbook", "author": "Your Name"}
  }'
```

The system will chunk and embed your content for retrieval-augmented generation.