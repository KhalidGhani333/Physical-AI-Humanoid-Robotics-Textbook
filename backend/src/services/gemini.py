"""
Gemini API service for the RAG Chatbot API
Handles interactions with Google's Gemini API for response generation
"""
import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from google.generativeai import GenerativeModel
from src.config import settings

logger = logging.getLogger(__name__)


class GeminiAPIService:
    """
    Service for interacting with Google's Gemini API
    """

    def __init__(self):
        # Configure the API key
        genai.configure(api_key=settings.GEMINI_API_KEY)

        # Initialize the model
        self.model_name = "gemini-1.5-flash"  # Using Gemini 1.5 Flash as specified
        self.model = GenerativeModel(self.model_name)

        # Set default generation configuration
        self.generation_config = {
            "temperature": 0.3,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

    async def generate_response(
        self,
        prompt: str,
        context_chunks: Optional[List[Dict[str, Any]]] = None,
        safety_settings: Optional[Dict] = None
    ) -> str:
        """
        Generate a response using the Gemini API
        """
        try:
            # Prepare the content with context if provided
            if context_chunks:
                # Add context to the prompt
                context_text = "\n\n".join([chunk["content"] for chunk in context_chunks])
                full_prompt = f"Context:\n{context_text}\n\nQuestion: {prompt}\n\nPlease answer based only on the provided context. If the answer is not in the context, say 'I cannot answer this question based on the provided content.'"
            else:
                full_prompt = prompt

            # Generate content
            response = await self.model.generate_content_async(
                full_prompt,
                generation_config=self.generation_config,
                safety_settings=safety_settings or self._get_default_safety_settings()
            )

            # Extract the text response
            if response.candidates and response.candidates[0].content.parts:
                generated_text = response.candidates[0].content.parts[0].text
                logger.info(f"Generated response of length {len(generated_text)} for prompt")
                return generated_text
            else:
                logger.warning("No valid response generated from Gemini API")
                return "I cannot generate a response at this time."

        except Exception as e:
            logger.error(f"Error generating response from Gemini API: {e}")
            raise

    async def generate_content_aware_response(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        content_boundary_enforced: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a response that enforces content boundaries
        """
        try:
            # Build the prompt with retrieved context
            context_parts = []
            for i, chunk in enumerate(retrieved_chunks):
                chunk_text = chunk.get("content", "")
                if chunk_text.strip():  # Only add non-empty chunks
                    context_parts.append(f"[Source {i+1}]: {chunk_text}")

            if not context_parts:
                return {
                    "response": "I cannot answer this question based on the provided content.",
                    "reason": "no_relevant_content",
                    "sources_used": []
                }

            context = "\n\n".join(context_parts)

            # Create the prompt that enforces content boundaries
            if content_boundary_enforced:
                prompt = f"""
                CONTEXT:
                {context}

                QUESTION:
                {query}

                INSTRUCTIONS:
                1. Answer the question based ONLY on the provided context.
                2. If the answer is not in the context, respond with: "I cannot answer this question based on the provided content."
                3. Do not use any external knowledge or make assumptions beyond what's in the context.
                4. If the context is insufficient to answer the question, acknowledge this limitation.
                5. Cite the sources you used by referencing the [Source X] labels.

                RESPONSE:
                """
            else:
                prompt = f"""
                CONTEXT:
                {context}

                QUESTION:
                {query}

                Please provide a helpful response based on the context.

                RESPONSE:
                """

            # Generate the response
            response_text = await self.generate_response(prompt, retrieved_chunks)

            # Extract source information
            sources_used = []
            for i, chunk in enumerate(retrieved_chunks):
                source_info = {
                    "chunk_id": chunk.get("chunk_id"),
                    "relevance_score": chunk.get("relevance_score", 0.0),
                    "content_preview": chunk.get("content", "")[:100] + "..." if len(chunk.get("content", "")) > 100 else chunk.get("content"),
                    "source_label": f"Source {i+1}"
                }
                sources_used.append(source_info)

            return {
                "response": response_text,
                "sources_used": sources_used,
                "context_chunks_count": len(retrieved_chunks)
            }

        except Exception as e:
            logger.error(f"Error generating content-aware response: {e}")
            return {
                "response": "I encountered an error while processing your request.",
                "reason": "generation_error",
                "sources_used": []
            }

    def _get_default_safety_settings(self):
        """
        Get default safety settings for the Gemini API
        """
        return {
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
        }

    async def validate_response_content(
        self,
        response: str,
        context_chunks: List[Dict[str, Any]]
    ) -> bool:
        """
        Validate that the response is grounded in the provided context
        This is a simplified validation - in practice, you might need more sophisticated checks
        """
        try:
            # Extract main content from context
            context_text = " ".join([chunk.get("content", "") for chunk in context_chunks]).lower()
            response_text = response.lower()

            # This is a basic check - a real implementation would need more sophisticated validation
            # For example, checking if claims in the response are supported by the context
            logger.info("Response validation completed")
            return True  # Placeholder - implement proper validation logic

        except Exception as e:
            logger.error(f"Error during response validation: {e}")
            return False


# Global instance
gemini_service = GeminiAPIService()