from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class QueueItemStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class QueueTaskDTO:
    """Queue task DTO"""
    task_id: str
    data: Any
    priority: int = 0
    status: QueueItemStatus = QueueItemStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
