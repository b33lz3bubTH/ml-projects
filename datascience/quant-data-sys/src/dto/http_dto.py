from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class HttpRequestDTO:
    """HTTP request DTO"""
    url: str
    referer: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    timeout: Optional[int] = None


@dataclass
class HttpResponseDTO:
    """HTTP response DTO"""
    content: str
    status_code: int
    headers: Dict[str, str]
    url: str


@dataclass
class BrowserConfigDTO:
    """Browser configuration DTO"""
    websocket_url: str
    user_agent: str
    viewport_width: int = 1920
    viewport_height: int = 1080
    timeout: int = 30000
    extra_headers: Optional[Dict[str, str]] = None
    wait_for_dom: bool = True
    wait_for_network_idle: bool = True
    additional_wait_seconds: float = 2.0