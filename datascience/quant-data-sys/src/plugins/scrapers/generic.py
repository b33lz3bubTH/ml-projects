from src.plugins.scrapers.base import BaseScraper
from src.plugins.html_cleaner import HtmlCleaner
from src.dto.scraper_dto import ScrapeResult
from src.infrastructure.http.http_client_factory import FallbackHttpClient
from src.dto.http_dto import HttpRequestDTO
import logging

logger = logging.getLogger(__name__)


class GenericScraper(BaseScraper):
    """Generic scraper for any website"""
    
    def __init__(self, url: str, http_client: FallbackHttpClient):
        super().__init__(url, http_client)
        self.cleaner: HtmlCleaner = None
        logger.debug(f"GenericScraper initialized for URL: {url}")
    
    async def scrape(self) -> ScrapeResult:
        """Generic scraping implementation"""
        logger.info(f"[GENERIC SCRAPER] Starting scrape for URL: {self.url}")
        
        http_request = HttpRequestDTO(url=self.url)
        http_response = await self.http_client.fetch(http_request)
        
        cleaner = HtmlCleaner(http_response.content)
        
        meta = await cleaner.extract_meta_tags()
        images = await cleaner.extract_image_urls()
        jsonld_blocks = await cleaner.extract_all_json_ld()
        article_links = await cleaner.extract_article_links(base_url=self.url)
        
        cleaner = await self._run_cleaning_pipeline(cleaner)
        cleaned_html = await cleaner.get_html()
        
        return ScrapeResult(
            url=self.url,
            html=http_response.content,
            cleaned_html=cleaned_html,
            meta_tags=meta,
            images=images,
            json_ld_blocks=jsonld_blocks,
            article_links=article_links
        )
    
    async def _run_cleaning_pipeline(self, cleaner: HtmlCleaner) -> HtmlCleaner:
        """Run the standard HTML cleaning pipeline - can be overridden by site-specific scrapers"""
        cleaner = await cleaner.clean()
        cleaner = await cleaner.remove_scripts()
        cleaner = await cleaner.remove_css()
        cleaner = await cleaner.remove_iframes()
        cleaner = await cleaner.remove_svg()
        cleaner = await cleaner.remove_junk_text_blocks()
        cleaner = await cleaner.remove_all_classes_and_ids()
        cleaner = await cleaner.remove_empty_tags()
        cleaner = await cleaner.aggressive_cleanup()
        cleaner = await cleaner.keep_only_body()
        cleaner = await cleaner.remove_layout_tags()
        cleaner = await cleaner.collapse_wrappers()
        cleaner = await cleaner.deep_prune_empty()
        return cleaner
