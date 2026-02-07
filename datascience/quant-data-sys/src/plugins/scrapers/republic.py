from src.plugins.scrapers.generic import GenericScraper
from src.plugins.html_cleaner import HtmlCleaner
from src.dto.scraper_dto import ScrapeResult
from src.infrastructure.http.http_client_factory import FallbackHttpClient
from src.dto.http_dto import HttpRequestDTO
import logging

logger = logging.getLogger(__name__)


class RepublicScraper(GenericScraper):
    """Republic-specific scraper - uses slug-based article link extraction"""
    
    def __init__(self, url: str, http_client: FallbackHttpClient):
        super().__init__(url, http_client)
        logger.debug(f"[REPUBLIC SCRAPER] Initialized for URL: {url}")
    
    async def scrape(self) -> ScrapeResult:
        """Republic-specific scraping - uses slug-based article link extraction"""
        logger.info(f"[REPUBLIC SCRAPER] Starting scrape for URL: {self.url}")
        
        http_request = HttpRequestDTO(url=self.url)
        http_response = await self.http_client.fetch(http_request)
        html = http_response.content
        logger.debug(f"[REPUBLIC SCRAPER] HTML fetched, length: {len(html)} characters")
        
        cleaner = HtmlCleaner(html)
        
        meta = await cleaner.extract_meta_tags()
        logger.info(f"[REPUBLIC SCRAPER] Extracted {len(meta)} meta tags")
        
        all_resolved_links = await cleaner.extract_all_resolved_links(base_url=self.url, min_length=25)
        logger.debug(f"[REPUBLIC SCRAPER] Extracted {len(all_resolved_links)} resolved links (length > 25)")
        
        images = await cleaner.extract_image_urls()
        logger.info(f"[REPUBLIC SCRAPER] Extracted {len(images)} image URLs")
        
        jsonld_blocks = await cleaner.extract_all_json_ld()
        logger.info(f"[REPUBLIC SCRAPER] Extracted {len(jsonld_blocks)} JSON-LD blocks")
        
        article_links = await cleaner.extract_slug_article_links(
            base_url=self.url,
            min_slug_length=30,
            min_hyphen_count=3,
            min_path_depth=1,
            min_total_path_length=50,
            exclude_paths={"about", "contact", "privacy", "terms", "login", "signup", "home", "index"},
            require_lowercase=True,
            min_hyphen_ratio=0.05
        )
        logger.info(f"[REPUBLIC SCRAPER] Extracted {len(article_links)} article links using slug-based detection")
        
        
        # article_links = article_links.union(all_resolved_links)
        article_links = [link for link in all_resolved_links if len(link) > 25]
        article_links = set[str](article_links) # this will remove duplicates

        logger.info(f"[REPUBLIC SCRAPER] Total article links after merging: {len(article_links)}")
        
        cleaner = await self._run_cleaning_pipeline(cleaner)
        cleaned_html = await cleaner.get_html()
        logger.debug(f"[REPUBLIC SCRAPER] Cleaned HTML length: {len(cleaned_html)} characters")
        
        logger.info("[REPUBLIC SCRAPER] Scrape process completed successfully")
        return ScrapeResult(
            url=self.url,
            html=html,
            cleaned_html=cleaned_html,
            meta_tags=meta,
            images=images,
            json_ld_blocks=jsonld_blocks,
            article_links=article_links
        )


