from abc import ABC, abstractmethod
from typing import TypeVar, Callable, Awaitable, Optional
import asyncio
import logging
from src.core.exceptions import RetryableException

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryHandler(ABC):
    """Base retry handler using Chain of Responsibility pattern"""
    
    def __init__(self, next_handler: Optional['RetryHandler'] = None):
        self.next_handler = next_handler
    
    @abstractmethod
    async def handle(
        self,
        func: Callable[[], Awaitable[T]],
        *args,
        **kwargs
    ) -> T:
        """Handle retry logic"""
        pass
    
    async def _try_next(
        self,
        func: Callable[[], Awaitable[T]],
        *args,
        **kwargs
    ) -> T:
        """Try next handler in chain"""
        if self.next_handler:
            return await self.next_handler.handle(func, *args, **kwargs)
        raise RuntimeError("No handler could process the request")


class ExponentialBackoffHandler(RetryHandler):
    """Handler with exponential backoff"""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        next_handler: Optional[RetryHandler] = None
    ):
        super().__init__(next_handler)
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
    
    async def handle(
        self,
        func: Callable[[], Awaitable[T]],
        *args,
        **kwargs
    ) -> T:
        delay = self.initial_delay
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except RetryableException as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = min(delay, self.max_delay)
                    if e.retry_after:
                        wait_time = max(wait_time, e.retry_after)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries + 1} failed: {e}. "
                        f"Retrying after {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                    delay *= self.backoff_factor
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed")
            except Exception as e:
                logger.error(f"Non-retryable exception: {e}")
                raise
        
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected retry failure")
    
    async def _try_next(
        self,
        func: Callable[[], Awaitable[T]],
        *args,
        **kwargs
    ) -> T:
        return await super()._try_next(func, *args, **kwargs)


class CooldownHandler(RetryHandler):
    """Handler with cooldown period between retries"""
    
    def __init__(
        self,
        cooldown_seconds: float = 5.0,
        next_handler: Optional[RetryHandler] = None
    ):
        super().__init__(next_handler)
        self.cooldown_seconds = cooldown_seconds
    
    async def handle(
        self,
        func: Callable[[], Awaitable[T]],
        *args,
        **kwargs
    ) -> T:
        try:
            return await self._try_next(func, *args, **kwargs)
        except RetryableException as e:
            logger.info(f"Cooldown period: {self.cooldown_seconds}s")
            await asyncio.sleep(self.cooldown_seconds)
            return await self._try_next(func, *args, **kwargs)


class RetryManager:
    """Factory for creating retry handler chains"""
    
    @staticmethod
    def create_default_chain(
        max_retries: int = 3,
        initial_delay: float = 1.0,
        cooldown_seconds: float = 5.0
    ) -> RetryHandler:
        """Create default retry chain: Cooldown -> ExponentialBackoff"""
        backoff = ExponentialBackoffHandler(
            max_retries=max_retries,
            initial_delay=initial_delay
        )
        cooldown = CooldownHandler(
            cooldown_seconds=cooldown_seconds,
            next_handler=backoff
        )
        return cooldown
