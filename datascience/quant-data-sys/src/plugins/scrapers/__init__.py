from src.plugins.scrapers.base import BaseScraper
from src.plugins.scrapers.generic import GenericScraper
from src.plugins.scrapers.factory import ScraperFactory, register_scrapers

__all__ = [
    "BaseScraper",
    "GenericScraper",
    "ScraperFactory",
    "register_scrapers"
]
