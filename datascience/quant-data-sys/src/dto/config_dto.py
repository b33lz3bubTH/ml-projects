from dataclasses import dataclass
from typing import Optional
import os


# http://localhost:9222/json/version


@dataclass
class DatabaseConfigDTO:
    """Database configuration DTO"""
    host: str
    port: int
    database: str
    user: str
    password: str
    pool_size: int = 10
    max_overflow: int = 20
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfigDTO':
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "prnreels"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20"))
        )


@dataclass
class RetryConfigDTO:
    """Retry configuration DTO"""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    cooldown_seconds: float = 5.0


@dataclass
class QueueConfigDTO:
    """Queue configuration DTO"""
    max_workers: int = 5
    max_queue_size: int = 1000


@dataclass
class AppConfigDTO:
    """Application configuration DTO"""
    playwright_websocket_url: Optional[str] = None
    http_timeout: int = 30
    user_agent_index: int = 0
    database: DatabaseConfigDTO = None
    retry: RetryConfigDTO = None
    queue: QueueConfigDTO = None
    
    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseConfigDTO.from_env()
        if self.retry is None:
            self.retry = RetryConfigDTO()
        if self.queue is None:
            self.queue = QueueConfigDTO()
    
    @classmethod
    def from_env(cls) -> 'AppConfigDTO':
        return cls(
            playwright_websocket_url=os.getenv("PLAYWRIGHT_WEBSOCKET_URL", "ws://localhost:9222/devtools/browser/bc068279-c36c-4ae2-9074-b52aa6227d8e"),
            http_timeout=int(os.getenv("HTTP_TIMEOUT", "30")),
            user_agent_index=int(os.getenv("USER_AGENT_INDEX", "0")),
            database=DatabaseConfigDTO.from_env(),
            retry=RetryConfigDTO(
                max_retries=int(os.getenv("RETRY_MAX_RETRIES", "3")),
                initial_delay=float(os.getenv("RETRY_INITIAL_DELAY", "1.0")),
                cooldown_seconds=float(os.getenv("RETRY_COOLDOWN", "8.7"))
            ),
            queue=QueueConfigDTO(
                max_workers=int(os.getenv("QUEUE_MAX_WORKERS", "5")),
                max_queue_size=int(os.getenv("QUEUE_MAX_SIZE", "1000"))
            )
        )
