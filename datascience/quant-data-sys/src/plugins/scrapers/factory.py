from typing import Optional, Dict, Type
from urllib.parse import urlparse
import logging
from src.plugins.scrapers.base import BaseScraper
from src.plugins.scrapers.generic import GenericScraper
from src.infrastructure.http.http_client_factory import FallbackHttpClient

logger = logging.getLogger(__name__)


class ScraperFactory:
    """Factory for creating site-specific or generic scrapers"""
    
    _scraper_registry: Dict[str, Type[BaseScraper]] = {}
    
    @classmethod
    def register(cls, domain: str, scraper_class: Type[BaseScraper]):
        """Register a site-specific scraper for a domain"""
        cls._scraper_registry[domain.lower()] = scraper_class
        logger.info(f"Registered scraper {scraper_class.__name__} for domain: {domain}")
    
    @classmethod
    def get_scraper(
        cls,
        url: str,
        http_client: FallbackHttpClient
    ) -> BaseScraper:
        """Get appropriate scraper for URL - site-specific or generic"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        scraper_class = None
        
        if domain in cls._scraper_registry:
            scraper_class = cls._scraper_registry[domain]
        else:
            domain_without_www = domain[4:] if domain.startswith("www.") else domain
            scraper_class = cls._scraper_registry.get(domain_without_www)
        
        if scraper_class:
            logger.info(f"[SCRAPER FACTORY] Using site-specific scraper: {scraper_class.__name__} for domain: {domain}")
            return scraper_class(url, http_client)
        else:
            logger.info(f"[SCRAPER FACTORY] Using generic scraper for domain: {domain}")
            return GenericScraper(url, http_client)
    
    @classmethod
    def get_registered_domains(cls) -> list[str]:
        """Get list of domains with registered scrapers"""
        return list(cls._scraper_registry.keys())


def register_scrapers():
    """Register all site-specific scrapers"""
    from src.plugins.scrapers.ndtv import NdtvScraper
    
    ScraperFactory.register("ndtv.com", NdtvScraper)
    ScraperFactory.register("ndtvprofit.com", NdtvScraper)
    ScraperFactory.register("www.ndtv.com", NdtvScraper)
    ScraperFactory.register("www.ndtvprofit.com", NdtvScraper)
