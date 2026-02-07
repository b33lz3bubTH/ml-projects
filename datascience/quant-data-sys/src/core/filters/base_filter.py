from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class BaseLinkFilter(ABC):
    """Base class for link filters"""
    
    @abstractmethod
    def should_exclude_url(self, url: str) -> bool:
        """
        Check if URL should be excluded before scraping.
        
        Args:
            url: The URL to check
            
        Returns:
            True if URL should be excluded, False otherwise
        """
        pass
    
    @abstractmethod
    def should_exclude_content(self, url: str, html: str) -> bool:
        """
        Check if scraped content should be excluded.
        
        Args:
            url: The URL that was scraped
            html: The HTML content
            
        Returns:
            True if content should be excluded, False otherwise
        """
        pass
    
    def get_name(self) -> str:
        """Get filter name for logging"""
        return self.__class__.__name__
