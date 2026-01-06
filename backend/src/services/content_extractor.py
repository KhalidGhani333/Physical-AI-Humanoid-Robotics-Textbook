from bs4 import BeautifulSoup
from typing import Optional
from ..utils.url_fetcher import URLFetcher
from ..config.settings import settings
import hashlib
import uuid
import logging


class ContentExtractor:
    """
    Service for extracting clean text content from HTML pages
    """

    def __init__(self):
        self.url_fetcher = URLFetcher()
        self.logger = logging.getLogger(__name__)

    def extract_content(self, url: str) -> Optional[str]:
        """
        Extract clean text content from a given URL

        Args:
            url: The URL to extract content from

        Returns:
            Clean text content, or None if extraction fails
        """
        # Fetch the HTML content
        html_content = self.url_fetcher.fetch_content(url)
        if not html_content:
            self.logger.error(f"Failed to fetch content from URL: {url}")
            return None

        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text content
            text = soup.get_text()

            # Clean up text by removing extra whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return text
        except Exception as e:
            self.logger.error(f"Error extracting content from {url}: {str(e)}")
            return None

    def extract_content_with_metadata(self, url: str):
        """
        Extract content and generate source metadata

        Args:
            url: The URL to extract content from

        Returns:
            Tuple of (content, metadata), or (None, None) if extraction fails
        """
        content = self.extract_content(url)
        if not content:
            self.logger.error(f"Failed to extract content with metadata from URL: {url}")
            return None, None

        # Generate document ID based on URL
        document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, url))

        # Create source metadata
        from ..models.source_metadata import SourceMetadata
        metadata = SourceMetadata(
            document_id=document_id,
            source_url=url,
            content_hash=hashlib.sha256(content.encode()).hexdigest(),
            crawl_timestamp=None,  # Will be set by the caller
            status="pending"
        )

        return content, metadata

    def is_url_accessible(self, url: str) -> bool:
        """
        Check if a URL is accessible before attempting to extract content

        Args:
            url: The URL to check

        Returns:
            True if the URL is accessible, False otherwise
        """
        try:
            accessible = self.url_fetcher.check_url_accessibility(url)
            if not accessible:
                self.logger.warning(f"URL is not accessible: {url}")
            return accessible
        except Exception as e:
            self.logger.error(f"Error checking URL accessibility for {url}: {str(e)}")
            return False