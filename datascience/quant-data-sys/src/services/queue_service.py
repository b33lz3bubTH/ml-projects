from typing import Callable, Awaitable, TypeVar, Generic, Optional
import logging
from src.core.queue.async_queue import AsyncQueue
from src.dto.queue_dto import QueueTaskDTO, QueueItemStatus
from src.dto.scraper_dto import ScrapeRequest, ScrapeResult
from src.services.scraper_service import ScraperService
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


class QueueService(Generic[T, R]):
    """Service for managing async queues"""
    
    def __init__(
        self,
        worker_func: Callable[[T], Awaitable[R]],
        max_workers: int = 5,
        max_queue_size: int = 1000
    ):
        self.queue = AsyncQueue(worker_func, max_workers, max_queue_size)
        self.tasks: dict[str, QueueTaskDTO] = {}
    
    async def start(self):
        """Start queue workers"""
        await self.queue.start()
    
    async def stop(self):
        """Stop queue workers"""
        await self.queue.stop()
    
    async def enqueue_task(
        self,
        data: T,
        priority: int = 0
    ) -> str:
        """Enqueue task and return task ID"""
        task_id = str(uuid.uuid4())
        task = QueueTaskDTO(
            task_id=task_id,
            data=data,
            priority=priority,
            status=QueueItemStatus.PENDING
        )
        self.tasks[task_id] = task
        await self.queue.enqueue(data, priority)
        logger.info(f"Task {task_id} enqueued")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[QueueTaskDTO]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    async def wait_complete(self):
        """Wait for all tasks to complete"""
        await self.queue.wait_complete()


class ScraperQueueService:
    """Specialized queue service for scraping"""
    
    def __init__(self, scraper_service: ScraperService, max_workers: int = 5):
        self.scraper_service = scraper_service
        self.queue_service = QueueService(
            worker_func=self._process_scrape,
            max_workers=max_workers
        )
    
    async def _process_scrape(self, request: ScrapeRequest) -> ScrapeResult:
        """Process scrape request"""
        return await self.scraper_service.scrape(request)
    
    async def start(self):
        """Start queue"""
        await self.queue_service.start()
    
    async def stop(self):
        """Stop queue"""
        await self.queue_service.stop()
    
    async def enqueue_scrape(
        self,
        url: str,
        priority: int = 0
    ) -> str:
        """Enqueue scrape task"""
        request = ScrapeRequest(url=url)
        return await self.queue_service.enqueue_task(request, priority)
    
    def get_task(self, task_id: str) -> Optional[QueueTaskDTO]:
        """Get task status"""
        return self.queue_service.get_task(task_id)
    
    async def wait_complete(self):
        """Wait for all tasks"""
        await self.queue_service.wait_complete()
