"""Custom Qdrant Retrieval Tool for OpenAI Agents SDK."""

from typing import Annotated, List, Dict, Any
from pydantic import BaseModel, Field
from agents import function_tool
import sys
from pathlib import Path

# Get the absolute path to the src directory
backend_path = Path(__file__).resolve().parent.parent  # backend directory
src_path = backend_path / "src"  # backend/src directory

# Add the src directory to Python path as fallback
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import modules - try absolute imports first (when package is installed), fallback to direct file loading
try:
    # Try to import using absolute Python import mechanism (works when package is installed)
    from backend.src.config.settings import settings
    from backend.src.services.vector_store import VectorStore
    from backend.src.services.embedding_generator import EmbeddingGenerator
    from backend.src.services.retrieval_service import RetrievalService
except ImportError:
    try:
        # Try standard imports (when run from backend directory)
        from config.settings import settings
        from services.vector_store import VectorStore
        from services.embedding_generator import EmbeddingGenerator
        from services.retrieval_service import RetrievalService
    except ImportError:
        # Fallback to importlib if standard imports fail
        import importlib.util

        def load_module_from_file(module_name, file_path):
            """Load a module from a file path using importlib."""
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            # Execute the module in an isolated context
            spec.loader.exec_module(module)
            return module

        # Load the settings module first since other modules may depend on it
        settings_path = src_path / "config" / "settings.py"
        settings_module = load_module_from_file("settings", settings_path)
        settings = settings_module.settings

        # Load the services modules
        vector_store_path = src_path / "services" / "vector_store.py"
        vector_store_module = load_module_from_file("vector_store", vector_store_path)
        VectorStore = vector_store_module.VectorStore

        embedding_gen_path = src_path / "services" / "embedding_generator.py"
        embedding_gen_module = load_module_from_file("embedding_generator", embedding_gen_path)
        EmbeddingGenerator = embedding_gen_module.EmbeddingGenerator

        retrieval_service_path = src_path / "services" / "retrieval_service.py"
        retrieval_service_module = load_module_from_file("retrieval_service", retrieval_service_path)
        RetrievalService = retrieval_service_module.RetrievalService


class QdrantRetrievalToolOutput(BaseModel):
    """Output schema for the Qdrant retrieval tool."""
    retrieved_chunks: List[Dict[str, Any]] = Field(
        description="List of retrieved content chunks with metadata"
    )
    num_results: int = Field(description="Number of results retrieved")
    query: str = Field(description="The original query")


@function_tool
def qdrant_retrieval_tool(
    query: Annotated[str, Field(description="The search query for retrieving relevant content")],
    top_k: Annotated[int, Field(description="Number of results to retrieve", default=5)] = 5
) -> QdrantRetrievalToolOutput:
    """
    Retrieve relevant content from Qdrant vector store based on the provided query.

    Args:
        query: The search query string
        top_k: Number of top results to return (default 5)

    Returns:
        QdrantRetrievalToolOutput: Contains retrieved chunks, count, and original query
    """
    try:
        # Initialize the components
        vector_store = VectorStore()
        embedding_generator = EmbeddingGenerator()

        # Create retrieval service
        retrieval_service = RetrievalService(
            vector_store=vector_store,
            embedding_generator=embedding_generator
        )

        # Get relevant chunks using the existing retrieval service
        retrieved_chunks = retrieval_service.get_relevant_chunks(
            query=query,
            top_k=top_k
        )

        return QdrantRetrievalToolOutput(
            retrieved_chunks=retrieved_chunks,
            num_results=len(retrieved_chunks),
            query=query
        )
    except Exception as e:
        # Handle any errors, especially Cohere rate limit errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in qdrant_retrieval_tool: {str(e)}")

        # Return empty results with error message
        return QdrantRetrievalToolOutput(
            retrieved_chunks=[{
                "id": "error",
                "content": f"Error retrieving content: {str(e)}",
                "source_url": "error",
                "chunk_index": 0,
                "document_id": "error",
                "relevance_score": 0.0
            }],
            num_results=0,
            query=query
        )