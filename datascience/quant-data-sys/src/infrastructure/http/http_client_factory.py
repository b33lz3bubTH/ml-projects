from typing import Optional, TYPE_CHECKING
import logging
from src.dto.config_dto import AppConfigDTO
from src.dto.http_dto import BrowserConfigDTO
from src.infrastructure.http.httpx_client import HttpxClient
from src.infrastructure.http.browser_client import BrowserClient
from src.core.retry.retry_handler import RetryManager, RetryHandler

if TYPE_CHECKING:
    from src.dto.http_dto import HttpRequestDTO, HttpResponseDTO

logger = logging.getLogger(__name__)


class HttpClientFactory:
    """Factory for creating HTTP clients"""
    
    @staticmethod
    def create_httpx_client(
        config: AppConfigDTO,
        retry_handler: Optional[RetryHandler] = None
    ) -> HttpxClient:
        """Create httpx client"""
        if retry_handler is None:
            retry_handler = RetryManager.create_default_chain(
                max_retries=config.retry.max_retries,
                initial_delay=config.retry.initial_delay,
                cooldown_seconds=config.retry.cooldown_seconds
            )
        
        return HttpxClient(
            timeout=config.http_timeout,
            user_agent_index=config.user_agent_index,
            retry_handler=retry_handler
        )
    
    @staticmethod
    def create_browser_client(
        config: AppConfigDTO,
        retry_handler: Optional[RetryHandler] = None
    ) -> Optional[BrowserClient]:
        """Create browser client if websocket URL is configured"""
        if not config.playwright_websocket_url:
            logger.info("Browser client not created - websocket URL not configured")
            return None
        
        logger.info(f"Creating browser client with websocket: {config.playwright_websocket_url}")
        
        if retry_handler is None:
            retry_handler = RetryManager.create_default_chain(
                max_retries=config.retry.max_retries,
                initial_delay=config.retry.initial_delay,
                cooldown_seconds=config.retry.cooldown_seconds
            )
        
        browser_config = BrowserConfigDTO(
            websocket_url=config.playwright_websocket_url,
            user_agent=HttpxClient.USER_AGENTS[config.user_agent_index] if HttpxClient.USER_AGENTS else "Mozilla/5.0",
            timeout=config.http_timeout * 1000,
            wait_for_dom=True,
            wait_for_network_idle=True,
            additional_wait_seconds=2.0
        )
        
        return BrowserClient(browser_config, retry_handler)
    
    @staticmethod
    def create_with_fallback(
        config: AppConfigDTO,
        retry_handler: Optional[RetryHandler] = None
    ) -> 'FallbackHttpClient':
        """Create HTTP client with fallback strategy"""
        httpx_client = HttpClientFactory.create_httpx_client(config, retry_handler)
        browser_client = HttpClientFactory.create_browser_client(config, retry_handler)
        
        return FallbackHttpClient(httpx_client, browser_client)


class FallbackHttpClient:
    """HTTP client with fallback from httpx to browser"""
    
    def __init__(
        self,
        primary_client: HttpxClient,
        fallback_client: Optional[BrowserClient]
    ):
        self.primary_client = primary_client
        self.fallback_client = fallback_client
        logger.info(f"FallbackHttpClient initialized - Browser fallback: {'ENABLED' if fallback_client else 'DISABLED'}")
    
    async def fetch(self, request: 'HttpRequestDTO') -> 'HttpResponseDTO':  # type: ignore
        """Fetch with fallback"""
        try:
            logger.info("[FALLBACK CLIENT] Attempting with HTTPX (primary)...")
            return await self.primary_client.fetch(request)
        except Exception as e:
            logger.warning(f"[FALLBACK CLIENT] Primary client (HTTPX) failed: {e}")
            logger.info("[FALLBACK CLIENT] Falling back to BROWSER mode...")
            
            if not self.fallback_client:
                logger.error("[FALLBACK CLIENT] Browser fallback not available (websocket URL not configured)")
                raise RuntimeError("Primary client failed and no fallback available") from e
            
            try:
                return await self.fallback_client.fetch(request)
            except Exception as fallback_error:
                logger.error(f"[FALLBACK CLIENT] Browser fallback also failed: {fallback_error}")
                raise RuntimeError("Both clients failed") from fallback_error
    
    async def close(self):
        """Close all clients"""
        if self.fallback_client:
            await self.fallback_client.close()
