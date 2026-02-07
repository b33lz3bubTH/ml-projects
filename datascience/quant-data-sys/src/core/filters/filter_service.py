from typing import List, Optional
from src.core.filters.base_filter import BaseLinkFilter
import logging

logger = logging.getLogger(__name__)


class LinkFilterService:
    """Service for managing and applying link filters"""
    
    def __init__(self, filters: Optional[List[BaseLinkFilter]] = None):
        """
        Initialize filter service.
        
        Args:
            filters: List of filter instances to apply
        """
        self.filters: List[BaseLinkFilter] = filters or []
    
    def add_filter(self, filter_instance: BaseLinkFilter):
        """Add a filter to the service"""
        self.filters.append(filter_instance)
        logger.info(f"[FILTER] Added filter: {filter_instance.get_name()}")
    
    def should_exclude_url(self, url: str) -> bool:
        """
        Check if URL should be excluded by any filter.
        
        Args:
            url: The URL to check
            
        Returns:
            True if any filter excludes the URL, False otherwise
        """
        for filter_instance in self.filters:
            if filter_instance.should_exclude_url(url):
                logger.debug(f"[FILTER] URL excluded by {filter_instance.get_name()}: {url}")
                return True
        return False
    
    def should_exclude_content(self, url: str, html: str) -> bool:
        """
        Check if content should be excluded by any filter.
        
        Args:
            url: The URL that was scraped
            html: The HTML content
            
        Returns:
            True if any filter excludes the content, False otherwise
        """
        for filter_instance in self.filters:
            if filter_instance.should_exclude_content(url, html):
                logger.debug(f"[FILTER] Content excluded by {filter_instance.get_name()}: {url}")
                return True
        return False
