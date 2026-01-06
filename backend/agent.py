#!/usr/bin/env python3
"""
RAG Agent Implementation

This module implements a Retrieval-Augmented Generation (RAG) agent that:
1. Uses the OpenAI Agents SDK to process queries
2. Integrates with existing Qdrant retrieval pipeline
3. Ensures responses are based solely on retrieved book content
4. Handles follow-up queries with conversation context
"""

import os
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
import time


import sys
from pathlib import Path

# Get the absolute path to the src directory
backend_path = Path(__file__).resolve().parent  # backend directory
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
    from backend.src.services.qdrant_retrieval_tool import qdrant_retrieval_tool
except ImportError:
    try:
        # Try standard imports (when run from backend directory)
        from config.settings import settings
        from services.vector_store import VectorStore
        from services.embedding_generator import EmbeddingGenerator
        from services.retrieval_service import RetrievalService
        from services.qdrant_retrieval_tool import qdrant_retrieval_tool
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

        try:
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

            # Load the qdrant retrieval tool
            qdrant_tool_path = src_path / "services" / "qdrant_retrieval_tool.py"
            qdrant_tool_module = load_module_from_file("qdrant_retrieval_tool", qdrant_tool_path)
            qdrant_retrieval_tool = qdrant_tool_module.qdrant_retrieval_tool

        except Exception as e:
            print(f"Error importing backend services: {e}")
            print("Make sure the required modules exist in src/services and src/config directories")
            sys.exit(1)

# Import OpenAI Agents SDK
try:
    from agents import Agent, Runner
    from agents import set_default_openai_key
except ImportError:
    print("Error: openai-agents package is required. Install it with: pip install openai-agents")
    sys.exit(1)

from dotenv import load_dotenv
from agents import OpenAIChatCompletionsModel
from openai import AsyncOpenAI
import warnings

# Load environment variables
load_dotenv()

# Suppress the OpenAI API key warning
warnings.filterwarnings("ignore", message="OPENAI_API_KEY is not set, skipping trace export")

API_KEY = os.environ.get("OPENROUTER_API_KEY")

client = AsyncOpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1"
    )

third_party_model = OpenAIChatCompletionsModel(
    model="mistralai/devstral-2512:free",
    openai_client=client
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class RAGAgent:
    """
    RAG (Retrieval-Augmented Generation) Agent that combines OpenAI Agents SDK
    with Qdrant-based retrieval to answer questions using book content.
    """

    def __init__(self):
        """Initialize the RAG agent with OpenAI Agents SDK and Qdrant integration."""
        self.logger = logger
        self.retrieval_service = None
        self.agent = None
        self.conversation_history = []

        # Validate required environment variables
        self._validate_environment()

        # Initialize Qdrant retrieval service
        self._initialize_retrieval_service()

        # Create the agent with retrieval tool
        self._create_agent()

        self.logger.info("RAG Agent initialized successfully")

    def _validate_environment(self):
        """Validate required environment variables are set."""
        required_vars = [
            'QDRANT_URL',
            'QDRANT_API_KEY',
            'OPENROUTER_API_KEY'
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                "Please set these variables in your .env file or environment."
            )

        self.logger.info("Environment validation passed")

    def _initialize_retrieval_service(self):
        """Initialize the Qdrant-based retrieval service using existing pipeline."""
        try:
            # Initialize the components
            vector_store = VectorStore()
            embedding_generator = EmbeddingGenerator()

            # Create retrieval service
            self.retrieval_service = RetrievalService(
                vector_store=vector_store,
                embedding_generator=embedding_generator
            )

            # Test the connection
            if vector_store.health_check():
                self.logger.info("Qdrant retrieval service initialized successfully")
            else:
                raise Exception("Could not connect to Qdrant")

        except Exception as e:
            self.logger.error(f"Failed to initialize Qdrant retrieval service: {str(e)}")
            raise

    def _create_agent(self):
        """Create an OpenAI agent with retrieval capabilities using the Agents SDK."""
        try:
            # Create the agent with a system prompt focused on using retrieved content
            self.agent = Agent(
                name="Physical AI and Humanoid Robotics RAG Agent",
                instructions="""
                You are an expert assistant for the Physical AI and Humanoid Robotics textbook.
                Your responses must be based ONLY on the retrieved content provided to you.
                Do not use general knowledge or information outside of the retrieved context.
                When answering questions:
                1. Use only the information from the retrieved context
                2. Quote directly from the context when possible
                3. Acknowledge if the answer is not available in the provided context
                4. Maintain context across follow-up questions
                5. Be precise and accurate based on the provided content
                """,
                model= third_party_model,  # Using a capable model
                tools=[qdrant_retrieval_tool]  # Use the custom Qdrant retrieval tool
            )

            self.logger.info("OpenAI Agent created successfully with Qdrant retrieval tool")
        except Exception as e:
            self.logger.error(f"Failed to create OpenAI agent: {str(e)}")
            raise

    def _format_retrieved_content(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """
        Format retrieved content into a string that can be provided to the agent.

        Args:
            retrieved_chunks: List of retrieved content chunks

        Returns:
            Formatted string of retrieved content
        """
        if not retrieved_chunks or len(retrieved_chunks) == 0:
            return "No relevant content found in the textbook."

        formatted_content = "Retrieved content from Physical AI and Humanoid Robotics textbook:\n\n"

        for i, chunk in enumerate(retrieved_chunks, 1):
            formatted_content += f"--- Content Chunk {i} ---\n"
            formatted_content += f"Source: {chunk.get('source_url', 'Unknown')}\n"
            formatted_content += f"Content: {chunk.get('content', '')}\n"
            formatted_content += f"Relevance Score: {chunk.get('relevance_score', 0.0):.3f}\n\n"

        return formatted_content

    def query(self, user_query: str, top_k: int = 5) -> str:
        """
        Process a user query using RAG approach with OpenAI Agents SDK.

        Args:
            user_query: The user's question or query
            top_k: Number of results to retrieve from Qdrant

        Returns:
            The agent's response based on retrieved content
        """
        start_time = time.time()
        self.logger.info(f"Processing query: '{user_query[:50]}...'")

        try:
            # Run the agent with the user query and the custom retrieval tool
            result = Runner.run_sync(
                self.agent,
                f"User Query: {user_query}\n\nINSTRUCTIONS: Use the qdrant_retrieval_tool to find relevant content from the Physical AI and Humanoid Robotics textbook. Only use the information from the retrieved context to answer the user's query. Do not use any general knowledge or information outside of the provided context. If the answer is not in the context, explicitly state that the information is not available in the provided content. The top_k parameter should be {top_k}.",
            )

            response_content = result.final_output

            # Check if the response indicates a retrieval error
            if "Error retrieving content" in response_content or "unable to retrieve" in response_content.lower():
                response_content = "I apologize, but I am unable to retrieve the relevant content due to a persistent error. As a result, I cannot provide an answer based on the textbook at this time. Please try again later."

            processing_time = time.time() - start_time
            self.logger.info(f"Query processed in {processing_time:.2f} seconds")

            # Store in conversation history
            self.conversation_history.append({
                "query": user_query,
                "response": response_content,
                "processing_time": processing_time,
                "timestamp": time.time()
            })

            return response_content

        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")

            # Return a user-friendly error message instead of raising the exception
            error_response = "I apologize, but I am unable to retrieve the relevant content due to a persistent error. As a result, I cannot provide an answer based on the textbook at this time. Please try again later."

            processing_time = time.time() - start_time
            self.logger.info(f"Query processed in {processing_time:.2f} seconds (with error)")

            # Store error response in conversation history
            self.conversation_history.append({
                "query": user_query,
                "response": error_response,
                "processing_time": processing_time,
                "timestamp": time.time()
            })

            return error_response

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history for the current session."""
        return self.conversation_history

    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
        self.logger.info("Conversation history reset")


def main():
    """Main function for testing the RAG agent."""
    logger.info("Initializing RAG Agent...")

    try:
        # Create the RAG agent
        agent = RAGAgent()

        print("\n" + "="*80)
        print("RAG Agent for Physical AI and Humanoid Robotics")
        print("="*80)
        print("The agent is ready to answer questions using textbook content.")
        print("Type 'quit' or 'exit' to stop.")
        print("="*80)

        while True:
            user_input = input("\nYour question: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            elif not user_input:
                continue

            try:
                # Process the query
                response = agent.query(user_input)
                print(f"\nResponse: {response}")
            except Exception as e:
                print(f"\nError processing query: {str(e)}")
                print("Please try again with a different question.")

    except Exception as e:
        logger.error(f"Error initializing RAG agent: {str(e)}")
        print(f"Failed to initialize RAG agent: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()