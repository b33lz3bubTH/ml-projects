from dataclasses import dataclass
from datetime import datetime
from typing import List, Set, Dict, Optional

@dataclass
class ScrapeRequest:
    url: str

@dataclass
class MetaTag:
    key: str
    value: str

@dataclass
class ScrapeResult:
    url: str
    html: str
    cleaned_html: str
    meta_tags: Dict[str, str]
    images: Set[str]
    json_ld_blocks: List[str]
    article_links: Set[str]
    job_created_at: Optional[datetime] = None
    job_processed_at: Optional[datetime] = None
    debug_ref: Optional[str] = None
    debug_html_path: Optional[str] = None
    debug_json_path: Optional[str] = None
