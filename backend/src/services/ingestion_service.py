from typing import List, Tuple
from datetime import datetime
import uuid
from ..models.ingestion_job import IngestionJob
from ..models.document_chunk import DocumentChunk
from ..services.content_extractor import ContentExtractor
from ..services.text_chunker import TextChunker
from ..services.vector_store import VectorStore
from ..config.settings import settings
import logging


class IngestionService:
    """
    Main service that orchestrates the entire ingestion workflow
    """

    def __init__(self):
        self.content_extractor = ContentExtractor()
        self.text_chunker = TextChunker()
        self.vector_store = VectorStore()
        self.logger = logging.getLogger(__name__)

    def start_ingestion_job(self, urls: List[str]) -> str:
        """
        Start a new ingestion job for the provided URLs

        Args:
            urls: List of URLs to process

        Returns:
            Job ID for the new ingestion job
        """
        job_id = str(uuid.uuid4())
        job = IngestionJob(
            job_id=job_id,
            source_urls=urls,
            status="running",
            total=len(urls),
            start_time=datetime.now()
        )

        # Process each URL
        processed_chunks = 0
        for i, url in enumerate(urls):
            try:
                # Extract content from the URL
                content, metadata = self.content_extractor.extract_content_with_metadata(url)
                if content and metadata:
                    # Chunk the content
                    chunks = self.text_chunker.chunk_text(
                        content,
                        metadata.document_id,
                        metadata.source_url
                    )

                    # Store chunks in vector store
                    for chunk in chunks:
                        success = self.vector_store.store_embedding(chunk)
                        if success:
                            processed_chunks += 1

                    # Update job progress
                    job.progress = i + 1
                    job.processed_chunks = processed_chunks
                else:
                    self.logger.error(f"Failed to extract content from URL: {url}")
                    job.error_details = f"Failed to extract content from URL: {url}"
                    job.status = "failed"
                    break
            except Exception as e:
                self.logger.error(f"Error processing URL {url}: {str(e)}")
                job.error_details = str(e)
                job.status = "failed"
                break

        # Update job status based on outcome
        if job.status != "failed":
            job.status = "completed"
            job.end_time = datetime.now()

        return job.job_id

    def process_single_url(self, url: str) -> Tuple[List[DocumentChunk], bool]:
        """
        Process a single URL through the full ingestion pipeline

        Args:
            url: The URL to process

        Returns:
            Tuple of (list of document chunks, success status)
        """
        # Extract content from the URL
        content, metadata = self.content_extractor.extract_content_with_metadata(url)
        if not content or not metadata:
            self.logger.error(f"Failed to extract content from URL: {url}")
            return [], False

        # Chunk the content
        chunks = self.text_chunker.chunk_text(
            content,
            metadata.document_id,
            metadata.source_url
        )

        # Store chunks in vector store
        stored_count = 0
        for chunk in chunks:
            success = self.vector_store.store_embedding(chunk)
            if success:
                stored_count += 1

        self.logger.info(f"Successfully processed {stored_count}/{len(chunks)} chunks from {url}")
        return chunks, stored_count == len(chunks)

    def get_ingestion_job(self, job_id: str) -> IngestionJob:
        """
        Retrieve the status of an ingestion job

        Args:
            job_id: The ID of the job to retrieve

        Returns:
            IngestionJob object
        """
        # In a real implementation, this would retrieve from a database
        # For now, we'll return a basic job object
        # This is a simplified version - in a full implementation,
        # job tracking would be persisted in a database
        return IngestionJob(
            job_id=job_id,
            source_urls=[],
            status="completed",
            total=0,
            progress=0,
            start_time=datetime.now(),
            processed_chunks=0
        )