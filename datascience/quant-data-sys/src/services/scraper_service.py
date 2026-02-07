from typing import Optional
import logging
from src.dto.scraper_dto import ScrapeRequest, ScrapeResult
from src.infrastructure.http.http_client_factory import FallbackHttpClient
from src.plugins.scrapers.factory import ScraperFactory, register_scrapers
from src.core.exceptions import BaseAppException
from src.core.debug.debug_saver import DebugSaver

logger = logging.getLogger(__name__)


class ScraperService:
    """Service for scraping operations - uses factory to get appropriate scraper"""
    
    def __init__(self, http_client: FallbackHttpClient):
        self.http_client = http_client
        register_scrapers()
        logger.info(f"ScraperService initialized. Registered domains: {ScraperFactory.get_registered_domains()}")
    
    async def scrape(self, request: ScrapeRequest) -> ScrapeResult:
        """Scrape URL using appropriate scraper (site-specific or generic)"""
        logger.info(f"Starting scrape for URL: {request.url}")
        
        try:
            scraper = ScraperFactory.get_scraper(request.url, self.http_client)
            result = await scraper.scrape()
            scraper_name = scraper.__class__.__name__
            logger.info(f"Scrape completed successfully using {scraper_name}")
            
            html_path, json_path, filename_base = DebugSaver.save_debug_files(result, scraper_name)
            if html_path and json_path:
                logger.info(f"[DEBUG] Debug files saved - HTML: {html_path}, JSON: {json_path}")
                result.debug_html_path = html_path
                result.debug_json_path = json_path
                result.debug_ref = filename_base
            
            return result
        except Exception as e:
            logger.error(f"Scrape failed: {e}", exc_info=True)
            raise BaseAppException(f"Scrape operation failed: {e}") from e
