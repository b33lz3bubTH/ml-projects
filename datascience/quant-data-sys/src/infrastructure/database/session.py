from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
from src.dto.config_dto import DatabaseConfigDTO
from src.core.exceptions import DatabaseException
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Singleton database manager"""
    _instance = None
    _engine = None
    _session_factory = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self, config: DatabaseConfigDTO):
        """Initialize database connection"""
        if self._engine is not None:
            return
        
        database_url = (
            f"postgresql+asyncpg://{config.user}:{config.password}@"
            f"{config.host}:{config.port}/{config.database}"
        )
        
        self._engine = create_async_engine(
            database_url,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            echo=False
        )
        
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("Database initialized")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        if self._session_factory is None:
            raise DatabaseException("Database not initialized")
        
        async with self._session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    async def close(self):
        """Close database connections"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connections closed")
    
    @property
    def engine(self):
        return self._engine
