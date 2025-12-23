"""
Content ingestion service for the RAG Chatbot API
Handles document parsing, chunking, and ingestion into the system
"""
import logging
import hashlib
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from src.services.embedding import embedding_service
from src.services.storage import ContentStorageService, VectorStorageService
from src.models.content import SourceDocument
from src.utils.logging import log_content_operation

logger = logging.getLogger(__name__)


class ContentIngestionService:
    """
    Service for ingesting content from various formats into the RAG system
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.content_storage = ContentStorageService(db_session)
        self.vector_storage = VectorStorageService()
        self.embedding_service = embedding_service

    def _calculate_checksum(self, content: str) -> str:
        """
        Calculate SHA-256 checksum for content deduplication
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks
        """
        chunks = []
        start = 0
        position = 0

        while start < len(text):
            # Determine the end position for this chunk
            end = start + chunk_size

            # If this is not the last chunk, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings near the end of the chunk
                chunk_text = text[start:end]
                last_period = chunk_text.rfind('.')
                last_exclamation = chunk_text.rfind('!')
                last_question = chunk_text.rfind('?')
                last_space = chunk_text.rfind(' ', int(chunk_size * 0.8), len(chunk_text))

                # Choose the best break point
                break_points = [bp for bp in [last_period, last_exclamation, last_question, last_space] if bp != -1]
                if break_points:
                    optimal_end = max(break_points) + 1  # Include the punctuation
                    end = start + optimal_end

            # Get the actual chunk
            chunk_text = text[start:end]

            # Add to chunks with metadata
            chunks.append({
                'content': chunk_text,
                'position': position,
                'start_offset': start,
                'end_offset': end
            })

            # Move to the next chunk with overlap
            start = end - overlap
            position += 1

            # Prevent infinite loops if overlap is too large
            if start >= end:
                start = end

        return chunks

    async def _process_and_store_chunk(self,
                                     content: str,
                                     source_document_id: UUID,
                                     position: int,
                                     page_number: Optional[int] = None,
                                     section_title: Optional[str] = None) -> Optional[str]:
        """
        Process a single chunk: generate embedding and store in both vector and content storage
        """
        try:
            # Calculate checksum for deduplication
            checksum = self._calculate_checksum(content)

            # Generate embedding
            embedding = await self.embedding_service.generate_embedding(content)

            # Generate a unique ID for the chunk
            import uuid
            chunk_id = str(uuid.uuid4())

            # Store in vector database (Qdrant)
            success = await self.vector_storage.store_embedding(
                chunk_id=chunk_id,
                embedding=embedding,
                content=content,
                metadata={
                    "source_document_id": str(source_document_id),
                    "position": position,
                    "checksum": checksum,
                    "page_number": page_number,
                    "section_title": section_title
                }
            )

            if not success:
                logger.error(f"Failed to store embedding for chunk {chunk_id}")
                return None

            # Store in content database (PostgreSQL)
            chunk = self.content_storage.create_content_chunk(
                content=content,
                source_document_id=source_document_id,
                embedding_vector_id=chunk_id,  # Reference to Qdrant ID
                position=position,
                metadata={
                    "checksum": checksum,
                    "page_number": page_number,
                    "section_title": section_title
                },
                page_number=page_number,
                section_title=section_title
            )

            logger.info(f"Successfully processed and stored chunk {chunk_id}")
            return chunk_id

        except Exception as e:
            logger.error(f"Failed to process chunk at position {position}: {e}")
            return None

    async def ingest_content(self,
                           title: str,
                           source_type: str,
                           source_path: str,
                           content: str,
                           metadata: Optional[Dict[str, Any]] = None,
                           chunk_size: int = 1000,
                           chunk_overlap: int = 200) -> Dict[str, Any]:
        """
        Main method to ingest content into the system
        """
        try:
            # Preprocess content based on source type
            if source_type.lower() == "markdown":
                processed_content = await self.parse_markdown(content)
            elif source_type.lower() == "html":
                processed_content = await self.parse_html(content)
            elif source_type.lower() == "pdf":
                processed_content = await self.parse_pdf_text(content)
            else:
                # For other types, use the content as is
                processed_content = content

            # Create source document record
            source_document = self.content_storage.create_source_document(
                title=title,
                source_type=source_type,
                source_path=source_path,
                metadata=metadata
            )

            # Log the start of the ingestion process
            log_content_operation(
                logger,
                operation="ingest_start",
                document_id=str(source_document.id),
                metadata={"title": title, "source_type": source_type}
            )

            # Chunk the processed content
            chunks = self._chunk_text(processed_content, chunk_size, chunk_overlap)
            total_chunks = len(chunks)
            processed_chunks = 0

            logger.info(f"Starting ingestion of {total_chunks} chunks for document {source_document.id}")

            # Process each chunk
            chunk_ids = []
            for i, chunk_data in enumerate(chunks):
                chunk_id = await self._process_and_store_chunk(
                    content=chunk_data['content'],
                    source_document_id=source_document.id,
                    position=chunk_data['position'],
                    # Add any additional metadata based on your requirements
                )

                if chunk_id:
                    chunk_ids.append(chunk_id)
                    processed_chunks += 1

                # Log progress periodically
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{total_chunks} chunks for document {source_document.id}")

            # Update document status and chunk count
            updated_document = self.content_storage.update_document_status(
                document_id=source_document.id,
                status="ingested" if processed_chunks == total_chunks else "partial",
                chunk_count=processed_chunks
            )

            # Log completion
            log_content_operation(
                logger,
                operation="ingest_complete",
                document_id=str(source_document.id),
                metadata={
                    "total_chunks": total_chunks,
                    "processed_chunks": processed_chunks,
                    "status": updated_document.status
                }
            )

            return {
                "document_id": str(source_document.id),
                "status": updated_document.status,
                "chunk_count": processed_chunks,
                "total_chunks": total_chunks,
                "success": True
            }

        except Exception as e:
            logger.error(f"Failed to ingest content: {e}")
            # Update document status to error
            if 'source_document' in locals():
                self.content_storage.update_document_status(
                    document_id=source_document.id,
                    status="error"
                )
            raise

    async def parse_markdown(self, content: str) -> str:
        """
        Parse and clean markdown content
        """
        import re

        # Remove markdown formatting while preserving content
        # Remove headers but keep the text
        content = re.sub(r'^#+\s+', '', content, flags=re.MULTILINE)

        # Remove emphasis markers but keep the text
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Bold
        content = re.sub(r'\*(.*?)\*', r'\1', content)      # Italic
        content = re.sub(r'__(.*?)__', r'\1', content)      # Bold
        content = re.sub(r'_(.*?)_', r'\1', content)        # Italic

        # Remove links but keep the link text: [text](url) -> text
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)

        # Remove images but keep the alt text: ![alt](url) -> alt
        content = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', content)

        # Remove code blocks but keep the content
        content = re.sub(r'```.*?\n(.*?)```', r'\1', content, flags=re.DOTALL)
        content = re.sub(r'`(.*?)`', r'\1', content)  # Inline code

        # Remove blockquotes
        content = re.sub(r'^>\s+', '', content, flags=re.MULTILINE)

        # Clean up extra whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)  # Multiple newlines to double
        content = content.strip()

        return content

    async def parse_html(self, content: str) -> str:
        """
        Parse and clean HTML content
        """
        from html import unescape
        import re

        # Remove HTML tags but preserve text content
        # This is a simple regex approach - for production use, consider using BeautifulSoup
        clean_content = re.sub(r'<[^>]+>', ' ', content)

        # Unescape HTML entities
        clean_content = unescape(clean_content)

        # Clean up extra whitespace
        clean_content = re.sub(r'\s+', ' ', clean_content)  # Multiple spaces/whitespace to single space
        clean_content = clean_content.strip()

        return clean_content

    async def parse_pdf_text(self, content: str) -> str:
        """
        Parse text extracted from PDF
        """
        import re

        # Clean up common PDF extraction artifacts
        # Fix hyphenated words that were split across lines
        content = re.sub(r'-\n', '', content)  # Remove hyphens at line breaks
        content = re.sub(r'(?<!\n)\n(?!\n)', ' ', content)  # Single newlines to spaces, preserve paragraph breaks

        # Remove extra whitespace
        content = re.sub(r'[ \t]+', ' ', content)  # Multiple spaces/tabs to single space
        content = re.sub(r'\n +', '\n', content)   # Spaces at start of lines
        content = re.sub(r' +\n', '\n', content)   # Spaces at end of lines

        # Clean up the text
        content = content.strip()

        return content


# Global instance will be created when needed with proper DB session