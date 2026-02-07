import json
import uuid
import re
from pathlib import Path
from typing import Dict, Set, List
import logging
from src.dto.scraper_dto import ScrapeResult

logger = logging.getLogger(__name__)


class DebugSaver:
    """Save debug files for scraped content"""
    
    @staticmethod
    def _sanitize_filename(text: str, max_length: int = 100) -> str:
        """Sanitize text for use in filename"""
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        text = text.strip('-')
        if len(text) > max_length:
            text = text[:max_length]
        return text or "untitled"
    
    @staticmethod
    def _extract_title(meta_tags: Dict[str, str], html: str) -> str:
        """Extract title from meta tags or HTML"""
        title = None
        
        if meta_tags:
            title = (
                meta_tags.get("og:title") or
                meta_tags.get("twitter:title") or
                meta_tags.get("title") or
                meta_tags.get("article:title")
            )
        
        if not title and html:
            from bs4 import BeautifulSoup
            try:
                soup = BeautifulSoup(html, "lxml")
                title_tag = soup.find("title")
                if title_tag:
                    title = title_tag.get_text(strip=True)
            except Exception:
                pass
        
        return title or "untitled"
    
    @staticmethod
    async def save_debug_files(
        result: ScrapeResult,
        scraper_name: str
    ) -> tuple[str, str]:
        """Save HTML and JSON debug files to /tmp/<scraper_name>/
        
        Returns:
            tuple: (html_file_path, json_file_path)
        """
        try:
            title = DebugSaver._extract_title(result.meta_tags, result.html)
            sanitized_title = DebugSaver._sanitize_filename(title)
            file_uuid = str(uuid.uuid4())[:8]
            
            base_dir = Path("/tmp") / scraper_name.lower()
            base_dir.mkdir(parents=True, exist_ok=True)
            
            filename_base = f"{sanitized_title}_{file_uuid}"
            
            html_file = base_dir / f"{filename_base}.html"
            json_file = base_dir / f"{filename_base}.json"
            
            html_file.write_text(result.html, encoding="utf-8")
            logger.info(f"[DEBUG] Saved HTML to: {html_file}")
            
            debug_data = {
                "url": result.url,
                "title": title,
                "meta_tags": result.meta_tags,
                "images": list(result.images),
                "json_ld_blocks": result.json_ld_blocks,
                "article_links": list(result.article_links),
                "html_length": len(result.html),
                "cleaned_html_length": len(result.cleaned_html),
                "cleaned_html": result.cleaned_html
            }
            
            json_file.write_text(
                json.dumps(debug_data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            logger.info(f"[DEBUG] Saved JSON to: {json_file}")
            
            return (str(html_file), str(json_file)))
        except Exception as e:
            logger.error(f"[DEBUG] Failed to save debug files: {e}", exc_info=True)
            return (None, None)
