from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.session import DatabaseManager
from src.infrastructure.http.http_client_factory import HttpClientFactory
from src.services.scraper_service import ScraperService
from src.services.spider_service import SpiderService
from src.dto.config_dto import AppConfigDTO

_config: AppConfigDTO = None
_db_manager: DatabaseManager = None
_scraper_service: ScraperService = None
_spider_service: SpiderService = None


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


def get_spider_service() -> SpiderService:
    """Get spider service - uses session factory"""
    config = get_config()
    scraper_service = get_scraper_service()
    db_manager = get_db_manager()
    
    if db_manager.session_factory is None:
        raise RuntimeError("Database not initialized")
    
    return SpiderService(
        scraper_service,
        db_manager.session_factory,
        max_workers=3,
        max_queue_size=876,
        cooldown_seconds=config.retry.cooldown_seconds
    )
