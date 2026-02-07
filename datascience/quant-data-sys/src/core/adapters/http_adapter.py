from abc import ABC, abstractmethod
from src.dto.http_dto import HttpRequestDTO, HttpResponseDTO
from typing import Optional


class IHttpAdapter(ABC):
    """HTTP adapter interface"""
    
    @abstractmethod
    async def fetch(self, request: HttpRequestDTO) -> HttpResponseDTO:
        """Fetch URL"""
        pass


class HttpAdapter:
    """Adapter pattern for HTTP clients"""
    
    def __init__(self, http_client):
        self.http_client = http_client
    
    async def fetch(self, request: HttpRequestDTO) -> HttpResponseDTO:
        """Adapt HTTP client interface"""
        if hasattr(self.http_client, 'fetch'):
            if hasattr(self.http_client.fetch, '__call__'):
                return await self.http_client.fetch(request)
        raise NotImplementedError("HTTP client does not support fetch method")
