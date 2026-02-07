from src.plugins.scrapers.generic import GenericScraper
from src.plugins.html_cleaner import HtmlCleaner
from src.dto.scraper_dto import ScrapeResult
from src.infrastructure.http.http_client_factory import FallbackHttpClient
from src.dto.http_dto import HttpRequestDTO
import logging

logger = logging.getLogger(__name__)


class NdtvScraper(GenericScraper):
    """NDTV-specific scraper - extends generic scraper with custom logic"""
    
    def __init__(self, url: str, http_client: FallbackHttpClient):
        super().__init__(url, http_client)
        logger.debug(f"[NDTV SCRAPER] Initialized for URL: {url}")
    
    async def _run_cleaning_pipeline(self, cleaner: HtmlCleaner) -> HtmlCleaner:
        """Override cleaning pipeline with NDTV-specific steps and logging"""
        logger.debug("[NDTV SCRAPER] Starting HTML cleaning pipeline")
        
        cleaner = await cleaner.clean()
        logger.debug("[NDTV SCRAPER] Step: clean() completed")
        
        cleaner = await cleaner.remove_scripts()
        logger.debug("[NDTV SCRAPER] Step: remove_scripts() completed")
        
        cleaner = await cleaner.remove_css()
        logger.debug("[NDTV SCRAPER] Step: remove_css() completed")
        
        cleaner = await cleaner.remove_iframes()
        logger.debug("[NDTV SCRAPER] Step: remove_iframes() completed")
        
        cleaner = await cleaner.remove_svg()
        logger.debug("[NDTV SCRAPER] Step: remove_svg() completed")
        
        cleaner = await cleaner.remove_junk_text_blocks()
        logger.debug("[NDTV SCRAPER] Step: remove_junk_text_blocks() completed")
        
        cleaner = await cleaner.remove_all_classes_and_ids()
        logger.debug("[NDTV SCRAPER] Step: remove_all_classes_and_ids() completed")
        
        cleaner = await cleaner.remove_empty_tags()
        logger.debug("[NDTV SCRAPER] Step: remove_empty_tags() completed")
        
        cleaner = await cleaner.aggressive_cleanup()
        logger.debug("[NDTV SCRAPER] Step: aggressive_cleanup() completed")
        
        cleaner = await cleaner.keep_only_body()
        logger.debug("[NDTV SCRAPER] Step: keep_only_body() completed")
        
        cleaner = await cleaner.remove_layout_tags()
        logger.debug("[NDTV SCRAPER] Step: remove_layout_tags() completed")
        
        cleaner = await cleaner.collapse_wrappers()
        logger.debug("[NDTV SCRAPER] Step: collapse_wrappers() completed")
        
        cleaner = await cleaner.deep_prune_empty()
        logger.debug("[NDTV SCRAPER] Step: deep_prune_empty() completed")
        
        logger.info("[NDTV SCRAPER] HTML cleaning pipeline completed")
        return cleaner
    
    async def scrape(self) -> ScrapeResult:
        """NDTV-specific scraping - can override extraction logic if needed"""
        logger.info(f"[NDTV SCRAPER] Starting scrape for URL: {self.url}")
        
        http_request = HttpRequestDTO(url=self.url)
        http_response = await self.http_client.fetch(http_request)
        html = http_response.content
        logger.debug(f"[NDTV SCRAPER] HTML fetched, length: {len(html)} characters")
        
        cleaner = HtmlCleaner(html)
        
        meta = await cleaner.extract_meta_tags()
        logger.info(f"[NDTV SCRAPER] Extracted {len(meta)} meta tags")
        
        images = await cleaner.extract_image_urls()
        logger.info(f"[NDTV SCRAPER] Extracted {len(images)} image URLs")
        
        jsonld_blocks = await cleaner.extract_all_json_ld()
        logger.info(f"[NDTV SCRAPER] Extracted {len(jsonld_blocks)} JSON-LD blocks")
        
        article_links = await cleaner.extract_article_links(base_url=self.url)
        logger.info(f"[NDTV SCRAPER] Extracted {len(article_links)} article links")
        
        all_resolved_links = await cleaner.extract_all_resolved_links(base_url=self.url, min_length=25)
        logger.debug(f"[NDTV SCRAPER] Extracted {len(all_resolved_links)} resolved links (length > 25)")
        
        article_links = article_links.union(all_resolved_links)
        logger.info(f"[NDTV SCRAPER] Total article links after merging: {len(article_links)}")
        
        cleaner = await self._run_cleaning_pipeline(cleaner)
        cleaned_html = await cleaner.get_html()
        logger.debug(f"[NDTV SCRAPER] Cleaned HTML length: {len(cleaned_html)} characters")
        
        logger.info("[NDTV SCRAPER] Scrape process completed successfully")
        return ScrapeResult(
            url=self.url,
            html=html,
            cleaned_html=cleaned_html,
            meta_tags=meta,
            images=images,
            json_ld_blocks=jsonld_blocks,
            article_links=article_links
        )


