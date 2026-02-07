import re
from typing import List, Optional
from src.core.filters.base_filter import BaseLinkFilter
import logging

logger = logging.getLogger(__name__)


class PatternLinkFilter(BaseLinkFilter):
    """Filter links based on URL patterns and content patterns"""
    
    def __init__(
        self,
        url_patterns: Optional[List[str]] = None,
        content_patterns: Optional[List[str]] = None,
        case_sensitive: bool = False
    ):
        """
        Initialize pattern filter.
        
        Args:
            url_patterns: List of regex patterns to match against URLs
            content_patterns: List of regex patterns to match against HTML content
            case_sensitive: Whether pattern matching is case sensitive
        """
        self.url_patterns = url_patterns or []
        self.content_patterns = content_patterns or []
        self.case_sensitive = case_sensitive
        
        flags = 0 if case_sensitive else re.IGNORECASE
        
        self._compiled_url_patterns = [
            re.compile(pattern, flags) for pattern in self.url_patterns
        ]
        self._compiled_content_patterns = [
            re.compile(pattern, flags) for pattern in self.content_patterns
        ]
    
    def should_exclude_url(self, url: str) -> bool:
        """Check if URL matches any exclusion pattern"""
        for pattern in self._compiled_url_patterns:
            if pattern.search(url):
                logger.debug(f"[FILTER] URL excluded by pattern: {url}")
                return True
        return False
    
    def should_exclude_content(self, url: str, html: str) -> bool:
        """Check if content matches any exclusion pattern"""
        for pattern in self._compiled_content_patterns:
            if pattern.search(html):
                logger.debug(f"[FILTER] Content excluded by pattern: {url}")
                return True
        return False
