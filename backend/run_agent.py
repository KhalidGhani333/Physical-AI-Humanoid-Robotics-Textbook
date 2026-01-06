#!/usr/bin/env python3
"""
Wrapper script to run the RAG agent with proper imports
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path to handle relative imports in service modules
backend_path = Path(__file__).parent
src_path = backend_path / "src"
sys.path.insert(0, str(src_path))

# Import the required modules using absolute imports that will work with the package structure
from config.settings import settings
from services.vector_store import VectorStore
from services.embedding_generator import EmbeddingGenerator
from services.retrieval_service import RetrievalService

# Now run the agent code with the modules already available in the namespace
# We'll execute the agent code in a way that the imports will work
import importlib.util

# Load the agent module
agent_spec = importlib.util.spec_from_file_location("agent", backend_path / "agent.py")
agent_module = importlib.util.module_from_spec(agent_spec)

# Add the imported modules to the agent module's namespace so they can be used
agent_module.settings = settings
agent_module.VectorStore = VectorStore
agent_module.EmbeddingGenerator = EmbeddingGenerator
agent_module.RetrievalService = RetrievalService

# Execute the agent module
agent_spec.loader.exec_module(agent_module)

# Run the main function if it exists
if hasattr(agent_module, 'main'):
    agent_module.main()