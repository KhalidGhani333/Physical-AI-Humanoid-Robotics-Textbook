from typing import List
from datetime import datetime
import uuid
from ..models.ingestion_job import IngestionJob
from ..models.document_chunk import DocumentChunk
from ..services.content_extractor import ContentExtractor
from ..services.text_chunker import TextChunker
from ..services.embedding_generator import EmbeddingGenerator
from ..services.vector_store import VectorStore
from ..services.duplicate_detector import DuplicateDetector
from ..services.metrics_service import metrics_service
from ..config.settings import settings
import logging


class IngestionWorkflow:
    """
    Comprehensive workflow service that orchestrates the entire ingestion pipeline
    """

    def __init__(self, use_mock_vector_store=False):
        self.content_extractor = ContentExtractor()
        self.text_chunker = TextChunker()
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore(use_mock=use_mock_vector_store)
        self.duplicate_detector = DuplicateDetector()
        self.logger = logging.getLogger(__name__)

    def run_ingestion_pipeline(self, urls: List[str], job_id: str = None) -> IngestionJob:
        """
        Run the complete ingestion pipeline from content extraction to vector storage

        Args:
            urls: List of URLs to process
            job_id: Optional job ID, will be generated if not provided

        Returns:
            IngestionJob object with status and results
        """
        if not job_id:
            job_id = str(uuid.uuid4())

        # Start performance monitoring
        metrics_service.start_timer("ingestion_pipeline_total")
        total_urls = len(urls)

        # Create initial job record
        job = IngestionJob(
            job_id=job_id,
            source_urls=urls,
            status="running",
            total=len(urls),
            start_time=datetime.now(),
            progress=0,
            processed_chunks=0
        )

        try:
            # Process each URL
            for i, url in enumerate(urls):
                self.logger.info(f"Processing URL {i+1}/{len(urls)}: {url}")

                # Start timing for this URL
                metrics_service.start_timer(f"process_url_{url.replace('://', '_').replace('/', '_')}")

                # Extract content from URL
                content, metadata = self.content_extractor.extract_content_with_metadata(url)

                if not content or not metadata:
                    self.logger.error(f"Failed to extract content from {url}")
                    job.error_details = f"Failed to extract content from {url}"
                    job.status = "failed"
                    # Record failure metric
                    metrics_service.increment_counter("failed_content_extraction", {"url": url})
                    break

                # Record successful extraction metric
                metrics_service.increment_counter("successful_content_extraction", {"url": url})

                # Check for duplicate content before processing
                if self.duplicate_detector.is_duplicate(content):
                    self.logger.info(f"Duplicate content detected for {url}, skipping processing")
                    # Record duplicate detection metric
                    metrics_service.increment_counter("duplicate_content_detected", {"url": url})
                    job.progress = i + 1  # Update progress but don't process
                    continue

                # Chunk the content
                metrics_service.start_timer("chunking_operation")
                chunks = self.text_chunker.chunk_text(
                    content,
                    metadata.document_id,
                    url
                )
                chunking_time = metrics_service.stop_timer("chunking_operation")

                self.logger.info(f"Created {len(chunks)} chunks from {url}")

                # Record chunking metrics
                metrics_service.record_histogram("chunks_per_document", len(chunks), {"url": url})
                metrics_service.record_histogram("chunking_duration_seconds", chunking_time, {"url": url})

                # Filter out duplicate chunks
                unique_chunks = []
                for chunk in chunks:
                    if not self.duplicate_detector.is_duplicate_chunk(chunk):
                        unique_chunks.append(chunk)
                        # Add the chunk to duplicate detector
                        self.duplicate_detector.add_chunk(chunk)

                if len(unique_chunks) < len(chunks):
                    duplicate_count = len(chunks) - len(unique_chunks)
                    self.logger.info(f"Filtered out {duplicate_count} duplicate chunks")
                    # Record duplicate chunk metrics
                    metrics_service.record_counter("duplicate_chunks_filtered", duplicate_count, {"url": url})

                # Generate embeddings for unique chunks only
                if unique_chunks:
                    metrics_service.start_timer("embedding_generation")
                    success = self.embedding_generator.generate_embeddings_for_chunks(unique_chunks)
                    embedding_time = metrics_service.stop_timer("embedding_generation")

                    if not success:
                        self.logger.error(f"Failed to generate embeddings for {url}")
                        job.error_details = f"Failed to generate embeddings for {url}"
                        job.status = "failed"
                        # Record failure metric
                        metrics_service.increment_counter("failed_embedding_generation", {"url": url})
                        break

                    # Record embedding success metrics
                    metrics_service.record_counter("successful_embedding_generation", len(unique_chunks), {"url": url})
                    metrics_service.record_histogram("embedding_generation_duration_seconds", embedding_time, {"url": url})

                    # Store embeddings in vector store
                    metrics_service.start_timer("vector_storage")
                    stored_count = self.vector_store.store_embeddings_batch(unique_chunks)
                    storage_time = metrics_service.stop_timer("vector_storage")

                    self.logger.info(f"Stored {stored_count} unique chunks in vector store for {url}")

                    # Record storage metrics
                    metrics_service.record_counter("stored_embeddings", stored_count, {"url": url})
                    metrics_service.record_histogram("storage_duration_seconds", storage_time, {"url": url})

                    # Update job processed chunks count
                    job.processed_chunks += stored_count

                # Record URL processing time
                url_time = metrics_service.stop_timer(f"process_url_{url.replace('://', '_').replace('/', '_')}")
                metrics_service.record_histogram("url_processing_duration_seconds", url_time, {"url": url})

                # Update job progress
                job.progress = i + 1

            # Set final status
            if job.status != "failed":
                job.status = "completed"
                job.end_time = datetime.now()

                # Record overall metrics
                total_time = metrics_service.stop_timer("ingestion_pipeline_total")
                metrics_service.record_histogram("ingestion_pipeline_duration_seconds", total_time)
                metrics_service.increment_counter("completed_ingestion_jobs", {"total_urls": str(total_urls)})

                # Log performance summary
                self.logger.info(f"Ingestion pipeline completed in {total_time:.2f} seconds for {total_urls} URLs")

        except Exception as e:
            self.logger.error(f"Ingestion pipeline failed: {str(e)}")
            job.status = "failed"
            job.error_details = str(e)
            job.end_time = datetime.now()

            # Record failure metrics
            total_time = metrics_service.stop_timer("ingestion_pipeline_total")
            metrics_service.increment_counter("failed_ingestion_jobs", {"total_urls": str(total_urls)})
            metrics_service.record_histogram("ingestion_pipeline_duration_seconds", total_time)

        return job

    def run_ingestion_with_config(self, urls: List[str], chunk_size: int = None,
                                  chunk_overlap: int = None, batch_size: int = None) -> IngestionJob:
        """
        Run the ingestion pipeline with custom configuration

        Args:
            urls: List of URLs to process
            chunk_size: Custom chunk size
            chunk_overlap: Custom chunk overlap
            batch_size: Custom batch size (not directly used in this workflow, but could be extended)

        Returns:
            IngestionJob object with status and results
        """
        # Use provided config or fall back to settings
        old_chunk_size = self.text_chunker.chunk_size
        old_chunk_overlap = self.text_chunker.chunk_overlap

        if chunk_size is not None:
            self.text_chunker.chunk_size = chunk_size
        if chunk_overlap is not None:
            self.text_chunker.chunk_overlap = chunk_overlap

        try:
            result = self.run_ingestion_pipeline(urls)
        finally:
            # Restore original settings
            self.text_chunker.chunk_size = old_chunk_size
            self.text_chunker.chunk_overlap = old_chunk_overlap

        return result

    def run_full_ingestion(self, urls: List[str]) -> IngestionJob:
        """
        Run a full ingestion process (extract, chunk, embed, store)

        Args:
            urls: List of URLs to process

        Returns:
            IngestionJob object with status and results
        """
        return self.run_ingestion_pipeline(urls)

    def run_incremental_ingestion(self, urls: List[str], force_update: bool = False) -> IngestionJob:
        """
        Run an incremental ingestion that detects and updates only changed content

        Args:
            urls: List of URLs to process
            force_update: If True, update all content regardless of changes

        Returns:
            IngestionJob object with status and results
        """
        if not urls:
            job_id = str(uuid.uuid4())
            return IngestionJob(
                job_id=job_id,
                source_urls=urls,
                status="completed",
                total=0,
                start_time=datetime.now(),
                progress=0,
                processed_chunks=0
            )

        job_id = str(uuid.uuid4())
        job = IngestionJob(
            job_id=job_id,
            source_urls=urls,
            status="running",
            total=len(urls),
            start_time=datetime.now(),
            progress=0,
            processed_chunks=0
        )

        try:
            for i, url in enumerate(urls):
                self.logger.info(f"Checking for updates on URL {i+1}/{len(urls)}: {url}")

                # Extract content from URL
                content, metadata = self.content_extractor.extract_content_with_metadata(url)

                if not content or not metadata:
                    self.logger.error(f"Failed to extract content from {url}")
                    job.error_details = f"Failed to extract content from {url}"
                    job.status = "failed"
                    break

                # Calculate content hash
                content_hash = self.duplicate_detector.calculate_content_hash(content)

                # Check if content has changed (if not forcing update)
                content_changed = True  # Assume changed unless proven otherwise
                if not force_update:
                    # In a real implementation, we would check against stored hashes
                    # For now, we'll implement a basic check by seeing if we've seen similar content
                    # This is a simplified version - in production, you'd have a persistent store
                    # of previous content hashes for each URL
                    content_changed = not self.duplicate_detector.is_duplicate(content)

                if content_changed or force_update:
                    self.logger.info(f"Content changed or update forced for {url}, processing...")

                    # Process the content (chunk, embed, store)
                    chunks = self.text_chunker.chunk_text(
                        content,
                        metadata.document_id,
                        url
                    )
                    self.logger.info(f"Created {len(chunks)} chunks from {url}")

                    # Filter out duplicate chunks
                    unique_chunks = []
                    for chunk in chunks:
                        if not self.duplicate_detector.is_duplicate_chunk(chunk):
                            unique_chunks.append(chunk)
                            # Add the chunk to duplicate detector
                            self.duplicate_detector.add_chunk(chunk)

                    if len(unique_chunks) < len(chunks):
                        self.logger.info(f"Filtered out {len(chunks) - len(unique_chunks)} duplicate chunks")

                    # Generate embeddings for unique chunks only
                    if unique_chunks:
                        success = self.embedding_generator.generate_embeddings_for_chunks(unique_chunks)
                        if not success:
                            self.logger.error(f"Failed to generate embeddings for {url}")
                            job.error_details = f"Failed to generate embeddings for {url}"
                            job.status = "failed"
                            break

                        # Store embeddings in vector store
                        stored_count = self.vector_store.store_embeddings_batch(unique_chunks)
                        self.logger.info(f"Stored {stored_count} unique chunks in vector store for {url}")

                        # Update job processed chunks count
                        job.processed_chunks += stored_count
                else:
                    self.logger.info(f"No changes detected for {url}, skipping")

                # Update job progress
                job.progress = i + 1

            # Set final status
            if job.status != "failed":
                job.status = "completed"
                job.end_time = datetime.now()

        except Exception as e:
            self.logger.error(f"Incremental ingestion pipeline failed: {str(e)}")
            job.status = "failed"
            job.error_details = str(e)
            job.end_time = datetime.now()

        return job