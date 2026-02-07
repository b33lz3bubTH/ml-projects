import asyncio
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

from src.dto.scraper_dto import ScrapeRequest
from src.dto.config_dto import AppConfigDTO
from src.infrastructure.http.http_client_factory import HttpClientFactory
from src.services.scraper_service import ScraperService

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

async def main():
    url = "https://www.ndtv.com/india-news/bjps-ritu-tawde-to-be-mumbai-mayor-shiv-senas-sanjay-shankar-ghadi-to-be-deputy-mayor-10963304?pfrom=home-ndtv_topscroll"
    
    logger.info(f"Starting scraper for URL: {url}")
    
    config = AppConfigDTO.from_env()
    http_client = HttpClientFactory.create_with_fallback(config)
    scraper_service = ScraperService(http_client)
    
    request = ScrapeRequest(url=url)
    result = await scraper_service.scrape(request)
    
    logger.info("=" * 80)
    logger.info("SCRAPE RESULTS")
    logger.info("=" * 80)
    logger.info(f"URL: {result.url}")
    logger.info(f"Original HTML length: {len(result.html)} characters")
    logger.info(f"Cleaned HTML length: {len(result.cleaned_html)} characters")
    logger.info(f"Meta tags: {len(result.meta_tags)}")
    logger.info(f"Images: {len(result.images)}")
    logger.info(f"JSON-LD blocks: {len(result.json_ld_blocks)}")
    logger.info(f"Article links: {len(result.article_links)}")
    
    
    await http_client.close()

if __name__ == "__main__":
    asyncio.run(main())
