import asyncio
from typing import Generic, TypeVar, Callable, Awaitable, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from src.core.exceptions import QueueException

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class QueueItem(Generic[T]):
    """Queue item with metadata"""
    data: T
    priority: int = 0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class AsyncQueue(Generic[T, R]):
    """Async queue for parallel processing"""
    
    def __init__(
        self,
        worker_func: Callable[[T], Awaitable[R]],
        max_workers: int = 5,
        max_queue_size: int = 1000
    ):
        self.worker_func = worker_func
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self.workers: list[asyncio.Task] = []
        self.running = False
        self._lock = asyncio.Lock()
    
    async def start(self):
        """Start worker pool"""
        async with self._lock:
            if self.running:
                return
            
            self.running = True
            self.workers = [
                asyncio.create_task(self._worker(f"worker-{i}"))
                for i in range(self.max_workers)
            ]
            logger.info(f"Started {self.max_workers} queue workers")
    
    async def stop(self):
        """Stop worker pool gracefully"""
        async with self._lock:
            if not self.running:
                return
            
            self.running = False
            
            for _ in range(self.max_workers):
                await self.queue.put((999999, QueueItem(None)))
            
            await asyncio.gather(*self.workers, return_exceptions=True)
            self.workers = []
            logger.info("Queue workers stopped")
    
    async def enqueue(self, item: T, priority: int = 0) -> None:
        """Add item to queue"""
        if not self.running:
            await self.start()
        
        if self.queue.full():
            raise QueueException("Queue is full")
        
        queue_item = QueueItem(data=item, priority=priority)
        await self.queue.put((priority, queue_item))
        logger.debug(f"Enqueued item with priority {priority}")
    
    async def _worker(self, worker_id: str):
        """Worker coroutine"""
        logger.debug(f"Worker {worker_id} started")
        
        while self.running:
            try:
                priority, queue_item = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )
                
                if queue_item.data is None:
                    break
                
                try:
                    result = await self.worker_func(queue_item.data)
                    logger.debug(f"Worker {worker_id} processed item")
                except Exception as e:
                    logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
                
                self.queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} unexpected error: {e}", exc_info=True)
        
        logger.debug(f"Worker {worker_id} stopped")
    
    async def wait_complete(self):
        """Wait for all queued items to be processed"""
        await self.queue.join()
        logger.info("All queue items processed")
