from typing import Optional
import logging
import asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext
from src.dto.http_dto import HttpRequestDTO, HttpResponseDTO, BrowserConfigDTO
from src.core.exceptions import BrowserConnectionException, HttpClientException
from src.core.retry.retry_handler import RetryHandler

logger = logging.getLogger(__name__)


class BrowserClient:
    """Browser client using websocket connection"""
    
    def __init__(
        self,
        config: BrowserConfigDTO,
        retry_handler: Optional[RetryHandler] = None
    ):
        self.config = config
        self.retry_handler = retry_handler
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._playwright = None
    
    async def _connect(self):
        """Connect to browser via websocket"""
        if self._browser is not None:
            return
        
        try:
            logger.info(f"[BROWSER MODE] Connecting to browser via websocket: {self.config.websocket_url}")
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.connect_over_cdp(
                self.config.websocket_url
            )
            logger.info("[BROWSER MODE] Successfully connected to browser via websocket")
        except Exception as e:
            logger.error(f"[BROWSER MODE] Failed to connect to browser: {e}")
            raise BrowserConnectionException(
                f"Browser connection failed: {e}",
                retry_after=5.0
            )
    
    async def _ensure_context(self):
        """Ensure browser context exists"""
        await self._connect()
        
        if self._context is None:
            headers = self.config.extra_headers or {}
            self._context = await self._browser.new_context(
                user_agent=self.config.user_agent,
                viewport={
                    "width": self.config.viewport_width,
                    "height": self.config.viewport_height
                },
                extra_http_headers=headers
            )
            logger.debug("Browser context created")
    
    async def fetch(self, request: HttpRequestDTO) -> HttpResponseDTO:
        """Fetch URL using browser"""
        if self.retry_handler:
            return await self.retry_handler.handle(
                self._fetch_internal,
                request
            )
        return await self._fetch_internal(request)
    
    async def _fetch_internal(self, request: HttpRequestDTO) -> HttpResponseDTO:
        """Internal fetch implementation"""
        logger.info(f"[BROWSER MODE] Fetching URL: {request.url}")
        await self._ensure_context()
        
        page = await self._context.new_page()
        try:
            if request.referer:
                await page.set_extra_http_headers({"referer": request.referer})
            
            if request.headers:
                await page.set_extra_http_headers(request.headers)
            
            timeout = request.timeout or self.config.timeout
            
            logger.debug(f"[BROWSER MODE] Navigating to URL with timeout: {timeout}ms")
            response = await page.goto(
                request.url,
                wait_until="domcontentloaded",
                timeout=timeout
            )
            
            if not response:
                raise HttpClientException("No response received from browser")
            
            status_code = response.status
            if status_code >= 400:
                raise HttpClientException(
                    f"HTTP {status_code} error",
                    retry_after=2.0 if status_code < 500 else 10.0
                )
            
            if self.config.wait_for_dom:
                logger.debug("[BROWSER MODE] Waiting for page to be fully loaded...")
                try:
                    await page.wait_for_load_state("load", timeout=min(timeout, 30000))
                except Exception as e:
                    logger.warning(f"[BROWSER MODE] Load state wait timed out: {e}")
                
                logger.debug("[BROWSER MODE] Waiting for DOM to be complete...")
                try:
                    await page.wait_for_function(
                        "document.readyState === 'complete'",
                        timeout=min(timeout // 2, 10000)
                    )
                except Exception:
                    logger.debug("[BROWSER MODE] DOM ready state check timed out, continuing...")
            
            if self.config.wait_for_network_idle:
                logger.debug("[BROWSER MODE] Waiting for network to be idle...")
                try:
                    await page.wait_for_load_state("networkidle", timeout=min(timeout, 30000))
                except Exception as e:
                    logger.warning(f"[BROWSER MODE] Network idle wait timed out: {e}")
            
            if self.config.additional_wait_seconds > 0:
                logger.debug(f"[BROWSER MODE] Waiting additional {self.config.additional_wait_seconds}s for dynamic content...")
                await asyncio.sleep(self.config.additional_wait_seconds)
            
            logger.debug("[BROWSER MODE] Scrolling to trigger lazy-loaded content...")
            try:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(0.5)
                await page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.debug(f"[BROWSER MODE] Scroll failed: {e}")
            
            content = await page.content()
            response_headers = await response.all_headers()
            
            logger.info(f"[BROWSER MODE] Successfully fetched {len(content)} chars from {request.url}")
            
            return HttpResponseDTO(
                content=content,
                status_code=status_code,
                headers=response_headers,
                url=response.url
            )
        except Exception as e:
            if isinstance(e, (HttpClientException, BrowserConnectionException)):
                raise
            logger.error(f"Browser fetch error: {e}")
            raise HttpClientException(f"Browser fetch failed: {e}", retry_after=5.0)
        finally:
            await page.close()
    
    async def close(self):
        """Close browser connections"""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.debug("Browser client closed")
