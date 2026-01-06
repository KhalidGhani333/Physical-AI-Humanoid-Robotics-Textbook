import re
from typing import List
from ..models.document_chunk import DocumentChunk
from ..config.settings import settings
import uuid


class TextChunker:
    """
    Service for deterministically chunking text content into manageable pieces
    """

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    def chunk_text(self, text: str, document_id: str, source_url: str) -> List[DocumentChunk]:
        """
        Chunk the provided text into smaller pieces with overlap

        Args:
            text: The text to chunk
            document_id: The ID of the document being chunked
            source_url: The URL where the text originated

        Returns:
            List of DocumentChunk objects
        """
        if not text:
            return []

        # Split text into sentences to maintain semantic boundaries
        sentences = self._split_into_sentences(text)

        chunks = []
        current_chunk = ""
        chunk_index = 0

        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk + sentence) > self.chunk_size and current_chunk:
                # Save the current chunk
                chunk = self._create_document_chunk(
                    current_chunk.strip(),
                    document_id,
                    source_url,
                    chunk_index
                )
                chunks.append(chunk)

                # Start a new chunk, including overlap if available
                if self.chunk_overlap > 0:
                    # Get the end portion of the current chunk for overlap
                    overlap_text = self._get_overlap_text(current_chunk, self.chunk_overlap)
                    current_chunk = overlap_text + " " + sentence
                else:
                    current_chunk = sentence
                chunk_index += 1
            else:
                current_chunk += " " + sentence

        # Add the final chunk if it has content
        if current_chunk.strip():
            chunk = self._create_document_chunk(
                current_chunk.strip(),
                document_id,
                source_url,
                chunk_index
            )
            chunks.append(chunk)

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences while preserving sentence boundaries
        """
        # Use regex to split on sentence boundaries while keeping the punctuation
        sentence_pattern = r'[.!?]+\s+|[\n\r]+|(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(sentence_pattern, text)

        # Filter out empty strings and strip whitespace
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """
        Get the ending portion of text for overlap purposes
        """
        words = text.split()
        if len(words) <= overlap_size:
            return text

        # Get the last 'overlap_size' words
        overlap_words = words[-overlap_size:]
        return " ".join(overlap_words)

    def _create_document_chunk(self, content: str, document_id: str, source_url: str, chunk_index: int) -> DocumentChunk:
        """
        Create a DocumentChunk object with the provided parameters
        """
        chunk_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{document_id}_{chunk_index}_{content[:50]}"))

        return DocumentChunk(
            id=chunk_id,
            document_id=document_id,
            source_url=source_url,
            chunk_index=chunk_index,
            content=content
        )