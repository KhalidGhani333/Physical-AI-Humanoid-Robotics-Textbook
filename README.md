# Physical AI & Humanoid Robotics Textbook with Smart Chatbot

This project contains a comprehensive textbook on Physical AI and Humanoid Robotics with an integrated smart chatbot that acts as a teacher, providing answers to questions about the textbook content.

## Features

- **Complete textbook content**: Multiple chapters covering Physical AI and Humanoid Robotics fundamentals
- **Smart chatbot**: AI-powered assistant that can answer questions about the textbook content
- **Interactive learning**: Students can ask questions and get detailed, contextual answers
- **Teacher-like functionality**: The chatbot acts as a tutor, providing explanations and clarifications

## Project Structure

- `website/` - Docusaurus-based website with textbook content and chatbot UI
- `backend/` - FastAPI backend with RAG (Retrieval-Augmented Generation) system
- `scripts/` - Utility scripts including content ingestion tools

## Getting Started

### Prerequisites

- Node.js (for the frontend)
- Python 3.8+ (for the backend)
- Access to Google Gemini API
- Access to Cohere API
- PostgreSQL database
- Qdrant vector database

### Setup

1. **Backend Setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   # Set up your .env file with API keys
   python src/main.py
   ```

2. **Frontend Setup**:
   ```bash
   cd website
   npm install
   npm start
   ```

3. **Ingest Textbook Content**:
   ```bash
   cd scripts
   npm install
   npm run ingest
   ```

### Environment Variables

Create `.env` files in both the backend and website directories:

**Backend (.env)**:
```env
GEMINI_API_KEY=your_gemini_api_key  # Required for AI responses
COHERE_API_KEY=your_cohere_api_key  # Required for embeddings
DATABASE_URL=your_postgresql_connection_string
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
```

**API Key Information**:
- **GEMINI_API_KEY**: Get from Google AI Studio (https://aistudio.google.com/)
- **COHERE_API_KEY**: Get from Cohere (https://cohere.com/)

The chatbot will work with limited functionality if these keys are not provided, but full AI capabilities require both keys.

**Frontend (.env)**:
```env
REACT_APP_API_BASE_URL=http://localhost:8000
```

## Using the Chatbot

Once the system is set up and the textbook content is ingested:

1. Navigate to the website
2. Use the chatbot widget (bottom-right corner) to ask questions about the textbook
3. The chatbot will search the textbook content and provide detailed, contextual answers
4. You can also select text on the page and ask questions about that specific content

## Content Ingestion

The system includes an automatic content ingestion script that will:
- Scan the `website/docs` directory for all markdown files
- Chunk and embed the content using Cohere's embedding models
- Store the embeddings in Qdrant for fast retrieval
- Maintain metadata for proper source attribution

Run the ingestion script with:
```bash
cd scripts
npm run ingest
```

## Architecture

- **Frontend**: React-based chat widget integrated into Docusaurus
- **Backend**: FastAPI server with RAG pipeline
- **AI Models**: Google Gemini for generation, Cohere for embeddings
- **Storage**: PostgreSQL for metadata, Qdrant for vector embeddings

## Troubleshooting

See the SETUP.md file for detailed troubleshooting information.

## License

[Add your license information here]