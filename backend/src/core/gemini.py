import asyncio
import logging
from typing import List, Dict, Any, Optional
from src.config import settings
import google.generativeai as genai
from src.core.retrieval import RetrievalService
import json

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        # Configure the Gemini API only if API key is available
        self.model = None
        if settings.GEMINI_API_KEY:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                # Store model names for fallback during generation
                # Using models that are commonly available in the Google Gemini API
                self.model_names = [
                    'gemini-1.5-flash-001',
                    'gemini-1.5-flash',
                    'gemini-1.0-pro-001',
                    'gemini-1.0-pro'
                ]
                logger.info("Gemini API configured successfully")
            except Exception as e:
                logger.error(f"Failed to configure Gemini API: {str(e)}")
                self.model = None
        else:
            logger.warning("GEMINI_API_KEY not found in settings")
            self.model_names = []

        # Initialize retrieval service for RAG functionality
        self.retrieval_service = RetrievalService()

    async def generate_response(self, query: str, context: List[Dict[str, Any]],
                               conversation_history: Optional[List[Dict[str, Any]]] = None,
                               mode: str = "full_content") -> Dict[str, Any]:
        """
        Generate a response using Gemini with RAG context
        """
        logger.info(f"Generating response for query: '{query[:50]}...' with mode: {mode}")

        # Check if API key is available
        if not settings.GEMINI_API_KEY or not self.model_names:
            logger.warning("Gemini API not configured - returning helpful message")
            response_text = (
                "The AI model is not configured. Please set up your GEMINI_API_KEY in the environment variables. "
                "For now, I can tell you that this system is designed to answer questions about Physical AI & Humanoid Robotics. "
                f"Query: {query}"
            )
            sources = []
            for item in context:
                source = {
                    "document_id": item.get("document_id", ""),
                    "content_snippet": item.get("content", "")[:200] + "..." if len(item.get("content", "")) > 200 else item.get("content", ""),
                    "score": item.get("score", 0),
                    "source_url": item.get("source_url", "")
                }
                sources.append(source)

            result = {
                "response": response_text,
                "sources": sources,
                "query": query,
                "mode": mode
            }

            logger.info("Returned helpful message due to missing API configuration")
            return result

        try:
            # Build the prompt with context
            prompt = self._build_rag_prompt(query, context, conversation_history, mode)

            # Try to generate content, with fallback to different models if needed
            response = await self._generate_with_model_fallback(prompt)

            # Extract the text response
            if response.candidates and response.candidates[0].content.parts:
                response_text = response.candidates[0].content.parts[0].text
            else:
                response_text = "I couldn't generate a response based on the provided information."

            # Extract sources from context
            sources = []
            for item in context:
                source = {
                    "document_id": item.get("document_id", ""),
                    "content_snippet": item.get("content", "")[:200] + "..." if len(item.get("content", "")) > 200 else item.get("content", ""),
                    "score": item.get("score", 0),
                    "source_url": item.get("source_url", "")
                }
                sources.append(source)

            result = {
                "response": response_text,
                "sources": sources,
                "query": query,
                "mode": mode
            }

            logger.info("Successfully generated response with Gemini")
            return result

        except Exception as e:
            logger.error(f"Error generating response with Gemini: {str(e)}")
            # Provide more specific error messages based on the type of error
            error_msg = str(e)
            if "API key" in error_msg or "Authentication" in error_msg or "403" in error_msg:
                response_text = "Authentication error: Please check your API key configuration."
            elif "quota" in error_msg or "billing" in error_msg:
                response_text = "Quota exceeded: Please check your API billing configuration."
            elif "model" in error_msg or "404" in error_msg:
                response_text = "AI model unavailable: The system tried multiple models but none are accessible. Please check your API key and model access permissions."
            elif "timeout" in error_msg or "504" in error_msg:
                response_text = "Request timed out: The server took too long to respond. Please try again."
            else:
                response_text = "I encountered an error while processing your request. Please try again later."

            return {
                "response": response_text,
                "sources": [],
                "query": query,
                "mode": mode,
                "error": str(e)
            }

    async def _generate_with_model_fallback(self, prompt: str):
        """
        Try to generate content using different models as fallback
        """
        last_error = None

        for model_name in self.model_names:
            try:
                logger.info(f"Trying to generate with model: {model_name}")
                model = genai.GenerativeModel(model_name)

                response = await model.generate_content_async(
                    prompt,
                    generation_config={
                        "temperature": 0.7,
                        "max_output_tokens": 2000,
                        "candidate_count": 1
                    },
                    # Add safety settings to avoid content filtering issues
                    safety_settings={
                        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                    }
                )

                logger.info(f"Successfully generated response with model: {model_name}")
                return response

            except Exception as e:
                logger.warning(f"Model {model_name} failed: {str(e)}")
                last_error = e
                continue

        # If all models failed, raise the last error
        if last_error:
            raise last_error
        else:
            raise Exception("No available Gemini model could generate content. Please check your API key and model access.")

    def _build_rag_prompt(self, query: str, context: List[Dict[str, Any]],
                         conversation_history: Optional[List[Dict[str, Any]]] = None,
                         mode: str = "full_content") -> str:
        """
        Build a prompt for Gemini that includes the query, context, and conversation history
        """
        # Start with system instructions
        if mode == "selected_text_only":
            system_prompt = (
                "You are an AI assistant that answers questions based ONLY on the provided text context. "
                "You must not use any external knowledge or information beyond what is provided in the context. "
                "If the answer cannot be found in the provided context, clearly state that the information is not available in the provided text. "
                "Always cite the sources of your information from the provided context."
            )
        else:
            system_prompt = (
                "You are an AI assistant that answers questions based on the provided text context. "
                "Use the context to inform your answers, but you may use general knowledge when the context is insufficient. "
                "Always cite the sources of your information from the provided context when available."
            )

        # Build context section
        context_section = "## Provided Context:\n"
        if context:
            for i, ctx in enumerate(context, 1):
                context_section += f"### Source {i}:\n"
                context_section += f"Document ID: {ctx.get('document_id', 'N/A')}\n"
                context_section += f"Content: {ctx.get('content', '')}\n"
                context_section += f"Source URL: {ctx.get('source_url', 'N/A')}\n\n"
        else:
            context_section += "No relevant context found.\n"

        # Build conversation history section if available
        history_section = ""
        if conversation_history:
            history_section = "## Previous Conversation:\n"
            for msg in conversation_history[-5:]:  # Include last 5 messages
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                history_section += f"{role.capitalize()}: {content}\n"

        # Build the full prompt
        prompt = (
            f"{system_prompt}\n\n"
            f"{history_section}\n"
            f"{context_section}\n"
            f"## User Query:\n"
            f"{query}\n\n"
            f"## Instructions:\n"
            f"Please provide a comprehensive answer to the user's query based on the provided context. "
            f"If citing information from the context, reference the appropriate source. "
            f"If the query cannot be answered from the provided context, clearly state this limitation."
        )

        return prompt

    async def validate_response_grounding(self, response: str, context: List[Dict[str, Any]]) -> bool:
        """
        Validate that the response is grounded in the provided context
        This is a basic implementation - in production, you might want more sophisticated validation
        """
        # Simple validation: check if key terms from context appear in response
        response_lower = response.lower()

        context_terms = set()
        for ctx in context:
            content = ctx.get("content", "").lower()
            # Extract some key terms (in a real implementation, you'd use more sophisticated NLP)
            words = content.split()[:20]  # Take first 20 words as representative terms
            context_terms.update(words)

        # Check if at least some context terms appear in the response
        matching_terms = [term for term in context_terms if term in response_lower and len(term) > 3]

        # If at least 30% of the context terms appear in the response, consider it grounded
        if len(context) > 0:
            grounding_score = len(matching_terms) / len(context_terms) if context_terms else 0
            return grounding_score >= 0.1  # At least 10% overlap
        else:
            # If no context provided, we can't validate grounding
            return True

    async def generate_citations(self, response: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate proper citations for the response based on the sources used
        """
        # This is a simplified citation generator
        # In a real implementation, you might use more sophisticated NLP to identify which sources
        # were actually used in the response
        return sources