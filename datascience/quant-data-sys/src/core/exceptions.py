from typing import Optional


class BaseAppException(Exception):
    """Base exception for all application exceptions"""
    pass


class RetryableException(BaseAppException):
    """Exception that can be retried"""
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


class HttpClientException(RetryableException):
    """HTTP client related exceptions"""
    pass


class BrowserConnectionException(RetryableException):
    """Browser connection related exceptions"""
    pass


class QueueException(BaseAppException):
    """Queue related exceptions"""
    pass


class DatabaseException(BaseAppException):
    """Database related exceptions"""
    pass
