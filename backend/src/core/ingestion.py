import asyncio
import logging
from typing import List, Dict, Any, Optional
from src.database.database import qdrant_client, SessionLocal
from src.models.content import ContentChunk
from src.config import settings
import cohere
from qdrant_client.http import models
import re
import uuid

logger = logging.getLogger(__name__)

class ContentIngestionService:
    def __init__(self):
        self.cohere_client = None
        if settings.COHERE_API_KEY:
            try:
                self.cohere_client = cohere.Client(settings.COHERE_API_KEY)
                logger.info("Cohere client initialized for ingestion service")
            except Exception as e:
                logger.error(f"Failed to initialize Cohere client for ingestion: {str(e)}")
                self.cohere_client = None
        else:
            logger.warning("COHERE_API_KEY not set - ingestion will have limited functionality")

        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP

    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into chunks of specified size with overlap
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # If this isn't the last chunk, try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings near the chunk boundary
                search_start = max(start, end - 200)  # Look back up to 200 chars
                sentence_end = -1

                for punct in ['.', '!', '?', '\n']:
                    last_punct = text.rfind(punct, search_start, end)
                    if last_punct > sentence_end:
                        sentence_end = last_punct + 1

                if sentence_end > start:
                    end = sentence_end
                else:
                    # If no sentence boundary found, just break at chunk_size
                    end = start + self.chunk_size

            chunk_text = text[start:end].strip()
            if chunk_text:  # Only add non-empty chunks
                chunks.append({
                    'text': chunk_text,
                    'start_pos': start,
                    'end_pos': end
                })

            # Move start position with overlap
            start = end - self.chunk_overlap if end < len(text) else end

            # Handle case where we're near the end
            if start >= len(text):
                break

        return chunks

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Cohere
        """
        if not self.cohere_client:
            logger.error("Cohere client not available - cannot generate embeddings for ingestion")
            # Return None to indicate that embeddings can't be generated
            # In a real implementation, you might want to use a different embedding method
            # or return empty results gracefully
            return None

        try:
            response = self.cohere_client.embed(
                texts=texts,
                model='embed-english-v3.0',  # Using Cohere's English embedding model
                input_type="search_document"  # Specify the input type for better embeddings
            )
            return [embedding for embedding in response.embeddings]
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            # Return None to indicate failure
            return None

    async def store_content_chunks(self, document_id: str, content: str,
                                   source_url: Optional[str] = None,
                                   metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Process content, create chunks, generate embeddings, and store in databases
        """
        # Chunk the content
        text_chunks = self.chunk_text(content)
        logger.info(f"Chunked content into {len(text_chunks)} chunks")

        if not text_chunks:
            logger.warning(f"No content chunks generated for document {document_id}")
            return 0

        # Prepare for embedding generation
        texts_for_embedding = [chunk['text'] for chunk in text_chunks]

        # Generate embeddings
        embeddings = await self.generate_embeddings(texts_for_embedding)

        if embeddings is None:
            logger.warning("Could not generate embeddings - skipping document ingestion")
            return 0

        if len(embeddings) != len(text_chunks):
            logger.error(f"Mismatch between chunks ({len(text_chunks)}) and embeddings ({len(embeddings)})")
            return 0

        logger.info(f"Generated embeddings for {len(embeddings)} chunks")

        # Store in databases
        db = SessionLocal()
        try:
            chunks_processed = 0

            for i, (chunk_data, embedding) in enumerate(zip(text_chunks, embeddings)):
                # Generate a unique ID for the vector in Qdrant
                vector_id = str(uuid.uuid4())

                # Store in Qdrant
                qdrant_client.upsert(
                    collection_name="content_chunks",
                    points=[
                        models.PointStruct(
                            id=vector_id,
                            vector={"content": embedding},
                            payload={
                                "document_id": document_id,
                                "chunk_index": i,
                                "content": chunk_data['text'],
                                "source_url": source_url,
                                "metadata": metadata or {}
                            }
                        )
                    ]
                )

                # Store metadata in PostgreSQL
                db_chunk = ContentChunk(
                    document_id=document_id,
                    chunk_index=i,
                    content=chunk_data['text'],
                    embedding_vector_id=vector_id,
                    source_url=source_url,
                    metadata_json=str(metadata) if metadata else None
                )

                db.add(db_chunk)
                chunks_processed += 1

            db.commit()
            logger.info(f"Successfully stored {chunks_processed} chunks for document {document_id}")
            return chunks_processed

        except Exception as e:
            db.rollback()
            logger.error(f"Error storing content chunks for document {document_id}: {str(e)}")
            raise e
        finally:
            db.close()

    async def process_document(self, content: str, document_id: str,
                              source_url: Optional[str] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a complete document: chunk, embed, and store
        """
        logger.info(f"Starting ingestion process for document: {document_id}")

        try:
            chunks_processed = await self.store_content_chunks(
                document_id=document_id,
                content=content,
                source_url=source_url,
                metadata=metadata
            )

            result = {
                "success": True,
                "document_id": document_id,
                "chunks_processed": chunks_processed,
                "message": f"Successfully processed {chunks_processed} content chunks"
            }

            logger.info(f"Completed ingestion for document {document_id}: {chunks_processed} chunks processed")
            return result

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            return {
                "success": False,
                "document_id": document_id,
                "chunks_processed": 0,
                "message": f"Error processing document: {str(e)}"
            }