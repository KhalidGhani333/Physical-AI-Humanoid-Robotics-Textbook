import hashlib
from typing import List, Dict
from ..models.document_chunk import DocumentChunk
from ..models.source_metadata import SourceMetadata
import logging


class DuplicateDetector:
    """
    Service for detecting and handling duplicate content
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # In-memory storage for content hashes (in production, use a persistent store)
        self.content_hashes: Dict[str, str] = {}  # hash -> document_id mapping

    def calculate_content_hash(self, content: str) -> str:
        """
        Calculate SHA256 hash of content for duplicate detection

        Args:
            content: The content to hash

        Returns:
            SHA256 hash of the content
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def is_duplicate(self, content: str) -> bool:
        """
        Check if the content is a duplicate

        Args:
            content: The content to check

        Returns:
            True if duplicate, False otherwise
        """
        content_hash = self.calculate_content_hash(content)
        return content_hash in self.content_hashes

    def is_duplicate_chunk(self, chunk: DocumentChunk) -> bool:
        """
        Check if a document chunk is a duplicate

        Args:
            chunk: The document chunk to check

        Returns:
            True if duplicate, False otherwise
        """
        if chunk.content:
            content_hash = self.calculate_content_hash(chunk.content)
            return content_hash in self.content_hashes
        return False

    def add_content(self, content: str, document_id: str) -> str:
        """
        Add content to the duplicate detection system

        Args:
            content: The content to add
            document_id: The ID of the document

        Returns:
            The content hash
        """
        content_hash = self.calculate_content_hash(content)
        self.content_hashes[content_hash] = document_id
        return content_hash

    def add_chunk(self, chunk: DocumentChunk) -> str:
        """
        Add a document chunk to the duplicate detection system

        Args:
            chunk: The document chunk to add

        Returns:
            The content hash
        """
        if chunk.content:
            content_hash = self.calculate_content_hash(chunk.content)
            self.content_hashes[content_hash] = chunk.document_id
            return content_hash
        return ""

    def add_chunks(self, chunks: List[DocumentChunk]) -> int:
        """
        Add multiple document chunks to the duplicate detection system

        Args:
            chunks: List of document chunks to add

        Returns:
            Number of unique chunks added
        """
        unique_added = 0
        for chunk in chunks:
            if not self.is_duplicate_chunk(chunk):
                self.add_chunk(chunk)
                unique_added += 1
        return unique_added

    def remove_content(self, content: str) -> bool:
        """
        Remove content from the duplicate detection system

        Args:
            content: The content to remove

        Returns:
            True if removed, False if not found
        """
        content_hash = self.calculate_content_hash(content)
        if content_hash in self.content_hashes:
            del self.content_hashes[content_hash]
            return True
        return False

    def get_duplicates(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        Get duplicate chunks from a list

        Args:
            chunks: List of document chunks to check

        Returns:
            List of duplicate chunks
        """
        duplicates = []
        for chunk in chunks:
            if self.is_duplicate_chunk(chunk):
                duplicates.append(chunk)
        return duplicates

    def clear(self):
        """
        Clear all stored content hashes
        """
        self.content_hashes.clear()