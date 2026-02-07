from abc import ABC, abstractmethod
from src.dto.scraper_dto import ScrapeResult
from src.infrastructure.http.http_client_factory import FallbackHttpClient

class BaseScraper(ABC):
    def __init__(self, url: str, http_client: FallbackHttpClient):
        self.url = url
        self.http_client = http_client

    @abstractmethod
    async def scrape(self) -> ScrapeResult:
        pass