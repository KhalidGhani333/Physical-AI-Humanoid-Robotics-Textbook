#!/usr/bin/env python3
"""
Script to check the embedding dimensions being used
"""
import os
from dotenv import load_dotenv
load_dotenv()

import cohere
import sys

# Initialize Cohere client
cohere_client = cohere.Client(os.getenv('COHERE_API_KEY'))

# Test different models and input types to check dimensions
test_text = "Introduction of Physical AI Humanoid Robotics"

models_to_test = [
    ('embed-english-light-v3.0', 'search_document'),
    ('embed-english-light-v3.0', 'search_query'),
]

# models_to_test = [
#     ('embed-english-light-v3.0', 'search_document'),
#     ('embed-english-light-v3.0', 'search_query'),
#     ('embed-multilingual-v2.0', 'search_document'),
#     ('embed-multilingual-v2.0', 'search_query'),
# ]



print("Testing embedding dimensions for different models and input types:")
print("=" * 70)

for model, input_type in models_to_test:
    try:
        response = cohere_client.embed(
            texts=[test_text],
            model=model,
            input_type=input_type
        )
        embedding = response.embeddings[0]
        print(f"Model: {model}, Input Type: {input_type}")
        print(f"  Dimensions: {len(embedding)}")
        print()
    except Exception as e:
        print(f"Error with {model}, {input_type}: {str(e)}")
        print()

print("The collection expects 768 dimensions, so we should use:")
print("- embed-english-v3.0 with input_type='search_document' (768 dims)")
print("- OR recreate the collection with the correct dimension for the existing embeddings")