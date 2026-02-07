from typing import AsyncGenerator
from src.infrastructure.database.session import DatabaseManager
from src.infrastructure.http.http_client_factory import HttpClientFactory
from src.services.scraper_service import ScraperService
from src.services.queue_service import ScraperQueueService
from src.dto.config_dto import AppConfigDTO

_config: AppConfigDTO = None
_db_manager: DatabaseManager = None
_scraper_service: ScraperService = None
_queue_service: ScraperQueueService = None


def get_config() -> AppConfigDTO:
    """Get application config (singleton)"""
    global _config
    if _config is None:
        _config = AppConfigDTO.from_env()
    return _config


def get_db_manager() -> DatabaseManager:
    """Get database manager (singleton)"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.initialize(get_config().database)
    return _db_manager


async def get_db_session():
    """Get database session"""
    async for session in get_db_manager().get_session():
        yield session


def get_scraper_service() -> ScraperService:
    """Get scraper service (singleton)"""
    global _scraper_service
    if _scraper_service is None:
        config = get_config()
        http_client = HttpClientFactory.create_with_fallback(config)
        _scraper_service = ScraperService(http_client)
    return _scraper_service


def get_queue_service() -> ScraperQueueService:
    """Get queue service (singleton)"""
    global _queue_service
    if _queue_service is None:
        config = get_config()
        scraper_service = get_scraper_service()
        _queue_service = ScraperQueueService(
            scraper_service,
            max_workers=config.queue.max_workers
        )
    return _queue_service
