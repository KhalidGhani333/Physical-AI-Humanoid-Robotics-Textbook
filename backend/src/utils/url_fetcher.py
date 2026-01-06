import requests
from typing import Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from ..config.settings import settings


class URLFetcher:
    """
    Utility class for fetching content from URLs with proper error handling and retry logic
    """

    def __init__(self):
        # Create a session with retry strategy
        self.session = requests.Session()

        # Define retry strategy
        retry_strategy = Retry(
            total=settings.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        # Mount adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update({
            'User-Agent': 'RAG-Content-Ingestion-Bot/1.0'
        })

    def fetch_content(self, url: str) -> Optional[str]:
        """
        Fetch content from a given URL

        Args:
            url: The URL to fetch content from

        Returns:
            The content of the URL as a string, or None if the request fails
        """
        try:
            response = self.session.get(
                url,
                timeout=settings.request_timeout
            )
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL {url}: {str(e)}")
            return None

    def check_url_accessibility(self, url: str) -> bool:
        """
        Check if a URL is accessible without fetching the full content

        Args:
            url: The URL to check

        Returns:
            True if the URL is accessible, False otherwise
        """
        try:
            response = self.session.head(
                url,
                timeout=settings.request_timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False