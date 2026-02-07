from typing import Callable, Awaitable, TypeVar, Optional
import logging
import time
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class MonitoringSidecar:
    """Sidecar pattern for monitoring operations"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.metrics: list[dict] = []
    
    def monitor(self, operation_name: str):
        """Decorator for monitoring async operations"""
        def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                if not self.enabled:
                    return await func(*args, **kwargs)
                
                start_time = time.time()
                start_dt = datetime.utcnow()
                
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    metric = {
                        "operation": operation_name,
                        "status": "success",
                        "duration": duration,
                        "timestamp": start_dt.isoformat()
                    }
                    self.metrics.append(metric)
                    logger.debug(f"Operation {operation_name} completed in {duration:.2f}s")
                    
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    
                    metric = {
                        "operation": operation_name,
                        "status": "error",
                        "duration": duration,
                        "error": str(e),
                        "timestamp": start_dt.isoformat()
                    }
                    self.metrics.append(metric)
                    logger.error(f"Operation {operation_name} failed after {duration:.2f}s: {e}")
                    raise
            
            return wrapper
        return decorator
    
    def get_metrics(self) -> list[dict]:
        """Get collected metrics"""
        return self.metrics.copy()
    
    def clear_metrics(self):
        """Clear collected metrics"""
        self.metrics.clear()
