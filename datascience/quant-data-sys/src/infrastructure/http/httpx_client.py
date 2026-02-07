from typing import Optional
import httpx
import logging
from src.dto.http_dto import HttpRequestDTO, HttpResponseDTO
from src.core.exceptions import HttpClientException
from src.core.retry.retry_handler import RetryHandler

logger = logging.getLogger(__name__)


class HttpxClient:
    """HTTP client using httpx"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    ]
    
    def __init__(
        self,
        timeout: int = 30,
        user_agent_index: int = 0,
        retry_handler: Optional[RetryHandler] = None
    ):
        self.timeout = timeout
        self.user_agent = self.USER_AGENTS[user_agent_index] if self.USER_AGENTS else "Mozilla/5.0"
        self.retry_handler = retry_handler
        self._default_headers = {
            "accept": "*/*",
            "accept-language": "en-GB,en;q=0.6",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "sec-gpc": "1",
            "user-agent": self.user_agent
        }
    
    async def fetch(self, request: HttpRequestDTO) -> HttpResponseDTO:
        """Fetch URL using httpx"""
        if self.retry_handler:
            return await self.retry_handler.handle(
                self._fetch_internal,
                request
            )
        return await self._fetch_internal(request)
    
    async def _fetch_internal(self, request: HttpRequestDTO) -> HttpResponseDTO:
        """Internal fetch implementation"""
        logger.info(f"[HTTPX MODE] Fetching URL: {request.url}")
        
        headers = self._default_headers.copy()
        if request.referer:
            headers["referer"] = request.referer
        if request.headers:
            headers.update(request.headers)
        
        timeout = request.timeout or self.timeout
        
        try:
            async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
                response = await client.get(request.url)
                
                if response.status_code >= 400:
                    raise HttpClientException(
                        f"HTTP {response.status_code} error",
                        retry_after=2.0 if response.status_code < 500 else 10.0
                    )
                
                content_length = len(response.text)
                final_url = str(response.url)
                
                if content_length < 500 and final_url != request.url:
                    logger.warning(f"[HTTPX MODE] Small content ({content_length} chars) after redirect, likely redirect page. Using browser instead.")
                    raise HttpClientException(
                        f"Redirect detected with small content ({content_length} chars), should use browser",
                        retry_after=0.1
                    )
                
                if content_length < 500:
                    logger.warning(f"[HTTPX MODE] Very small content ({content_length} chars), might be incomplete. Consider using browser.")
                
                logger.info(f"[HTTPX MODE] Successfully fetched {content_length} chars from {final_url}")
                
                return HttpResponseDTO(
                    content=response.text,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    url=final_url
                )
        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise HttpClientException(f"HTTP request failed: {e}", retry_after=5.0)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HttpClientException(f"Request failed: {e}", retry_after=5.0)
