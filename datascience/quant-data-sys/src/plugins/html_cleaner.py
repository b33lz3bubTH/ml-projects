import asyncio
import re
from bs4 import BeautifulSoup, Comment
from pathlib import Path
from typing import List, Set, Optional
from urllib.parse import urlparse, urljoin

class HtmlCleaner:
    def __init__(self, html_source: str):
        """
        html_source can be:
        - raw html string
        - path to html file
        """
        self.html = html_source
        self.soup = BeautifulSoup(self.html, "lxml")

    # ------------------------
    # PIPELINE STEPS
    # ------------------------

    async def clean(self):
        """Basic normalization"""
        return self

    async def remove_head(self):
        if self.soup.head:
            self.soup.head.decompose()
        return self

    async def remove_scripts(self):
        for tag in self.soup.find_all("script"):
            if tag.get("type") == "application/ld+json":
                continue
            tag.decompose()
        return self

    async def remove_css(self):
        # remove <style>
        for tag in self.soup.find_all("style"):
            tag.decompose()

        # remove inline style attrs
        for tag in self.soup.find_all(True):
            if tag.has_attr("style"):
                del tag["style"]

        return self

    async def remove_svg(self):
        for tag in self.soup.find_all("svg"):
            tag.decompose()
        return self

    async def keep_only_body(self):
        body = self.soup.body
        if body:
            self.soup = BeautifulSoup(str(body), "lxml")
        return self

    async def save(self, filename="out.html"):
        Path(filename).write_text(
            str(self.soup),
            encoding="utf-8"
        )
        return self
    
    async def remove_all_classes_and_ids(self):
        for tag in self.soup.find_all(True):
            tag.attrs.pop("class", None)
            tag.attrs.pop("id", None)
        return self
    
    async def remove_iframes(self):
        for tag in self.soup.find_all("iframe"):
            tag.decompose()
        return self

    async def remove_empty_tags(self):
        removable = [
            "div", "span", "section", "article",
            "p", "aside", "header", "footer"
        ]

        for tag in self.soup.find_all(removable):
            if not tag.get_text(strip=True) and not tag.find(True):
                tag.decompose()

        return self

    async def aggressive_cleanup(self):
        for tag in self.soup.find_all(True):

            # remove empty attrs
            tag.attrs = {k: v for k, v in tag.attrs.items() if v}

            # remove whitespace-only text nodes
            if tag.string and not tag.string.strip():
                tag.string.extract()

        return self

    async def remove_junk_text_blocks(self):
        JUNK_WORDS = {
            "advertisement",
            "sponsored",
            "promoted",
            "related articles",
            "recommended",
            "you may like"
            "Newsletters"
        }

        for tag in self.soup.find_all(True):
            txt = tag.get_text(strip=True).lower()
            if txt in JUNK_WORDS:
                tag.decompose()

        return self

    async def collapse_wrappers(self):
        changed = True

        while changed:
            changed = False

            for tag in self.soup.find_all("div"):
                children = [c for c in tag.children if getattr(c, "name", None)]

                if len(children) == 1:
                    tag.replace_with(children[0])
                    changed = True

        return self
    
    async def remove_layout_tags(self):
        for tag in self.soup.find_all(
            ["nav", "aside", "footer", "header", "menu"]
        ):
            tag.decompose()

        return self

    async def deep_prune_empty(self):
        removed = True
        while removed:
            removed = False
            for tag in self.soup.find_all(["div","span","section"]):
                if not tag.get_text(strip=True) and not tag.find(True):
                    tag.decompose()
                    removed = True
        return self

    async def extract_meta_tags(self) -> dict:
        meta_data = {}

        for tag in self.soup.find_all("meta"):
            key = (
                tag.get("property")
                or tag.get("name")
                or tag.get("itemprop")
            )

            value = tag.get("content")

            if key and value:
                meta_data[key.strip()] = value.strip()

        return meta_data

    async def extract_image_urls(self) -> set:
        urls = set[str]()

        ATTRS = [
            "src",
            "data-src",
            "data-lazy",
            "data-original",
            "data-srcset"
        ]

        for img in self.soup.find_all("img"):
            for attr in ATTRS:
                val = img.get(attr)
                if val:
                    urls.add(val.strip())

        return urls



    # ------------------------
    # EXTRACTION
    # ------------------------

    async def extract_all_json_ld(self) -> List[str]:
        results = []
        for tag in self.soup.find_all("script", type="application/ld+json"):
            if tag.string:
                results.append(tag.string.strip())
        return results

    @staticmethod
    def _is_probable_article_slug(
        url_path: str,
        min_slug_length: int = 30,
        min_hyphen_count: int = 3,
        min_path_depth: int = 1,
        min_total_path_length: int = 50,
        exclude_paths: Optional[Set[str]] = None,
        require_lowercase: bool = True,
        min_hyphen_ratio: float = 0.05
    ) -> bool:
        """Check if URL path looks like an article slug using configurable heuristics"""
        if not url_path:
            return False
        
        if exclude_paths is None:
            exclude_paths = set()
        
        normalized_path = url_path.strip("/")
        if not normalized_path:
            return False
        
        parts = [p for p in normalized_path.split("/") if p]
        
        if len(parts) < min_path_depth:
            return False
        
        if any(part.lower() in exclude_paths for part in parts):
            return False
        
        slug = parts[-1]
        total_path_length = len(normalized_path)
        
        if total_path_length < min_total_path_length:
            return False
        
        if len(slug) < min_slug_length:
            return False
        
        hyphen_count = slug.count("-")
        if hyphen_count < min_hyphen_count:
            return False
        
        hyphen_ratio = hyphen_count / len(slug) if len(slug) > 0 else 0
        if hyphen_ratio < min_hyphen_ratio:
            return False
        
        if require_lowercase and not slug.islower():
            return False
        
        return True
    
    async def extract_article_links(self, base_url: str = None) -> Set[str]:
        """Extract article links from the page (ID-based detection)"""
        ARTICLE_ID_RE = re.compile(r"-\d+$")
        links = set()
        
        if base_url:
            parsed = urlparse(base_url)
            base_domain = parsed.netloc
        else:
            base_domain = None
        
        for a in self.soup.find_all("a"):
            href = a.get("href")
            
            if not href:
                continue
            
            # absolute
            if href.startswith("/"):
                if base_domain:
                    href = f"https://{base_domain}{href}"
                else:
                    continue
            
            # must belong to site
            if base_domain and not href.startswith(f"https://{base_domain}"):
                continue
            
            href = href.split("?")[0]  # remove tracking params
            
            # length heuristic
            if len(href) < 80:
                continue
            
            # must end with article id
            if not ARTICLE_ID_RE.search(href):
                continue
            
            links.add(href)
        
        return links
    
    async def extract_slug_article_links(
        self,
        base_url: str,
        min_slug_length: int = 30,
        min_hyphen_count: int = 3,
        min_path_depth: int = 1,
        min_total_path_length: int = 50,
        exclude_paths: Optional[Set[str]] = None,
        require_lowercase: bool = True,
        min_hyphen_ratio: float = 0.05
    ) -> Set[str]:
        """Extract article links using configurable slug-based detection"""
        links = set()
        
        if not base_url:
            return links
        
        if exclude_paths is None:
            exclude_paths = set()
        
        parsed = urlparse(base_url)
        base_domain = parsed.netloc
        base_scheme = parsed.scheme or "https"
        base_netloc = f"{base_scheme}://{base_domain}"
        
        for a in self.soup.find_all("a"):
            href = a.get("href")
            
            if not href:
                continue
            
            href = href.split("?")[0].split("#")[0]  # remove tracking params and fragments
            
            if href.startswith("/"):
                full_url = urljoin(base_netloc, href)
                path = href
            elif href.startswith(f"{base_scheme}://{base_domain}"):
                full_url = href
                parsed_href = urlparse(href)
                path = parsed_href.path
            else:
                continue
            
            if not self._is_probable_article_slug(
                path,
                min_slug_length=min_slug_length,
                min_hyphen_count=min_hyphen_count,
                min_path_depth=min_path_depth,
                min_total_path_length=min_total_path_length,
                exclude_paths=exclude_paths,
                require_lowercase=require_lowercase,
                min_hyphen_ratio=min_hyphen_ratio
            ):
                continue
            
            links.add(full_url)
        
        return links
    
    async def extract_all_resolved_links(
        self,
        base_url: str,
        min_length: int = 25
    ) -> Set[str]:
        """Extract all resolved links with length over min_length characters
        
        This function finds all <a> tags, resolves relative URLs to absolute,
        and returns links that exceed the minimum character length.
        Useful for discovering article links and navigation.
        """
        links = set[str]()
        
        if not base_url:
            return links
        
        parsed = urlparse(base_url)
        base_domain = parsed.netloc
        base_scheme = parsed.scheme or "https"
        base_netloc = f"{base_scheme}://{base_domain}"
        
        for a in self.soup.find_all("a"):
            href = a.get("href")

            print(f"[RESOLVED SE PEHELE] href: {href}")
            
            if not href:
                continue
            
            href = href.split("?")[0].split("#")[0]  # remove tracking params and fragments
            
            if href.startswith("/"):
                full_url = urljoin(base_netloc, href)
            elif href.startswith(f"{base_scheme}://{base_domain}"):
                full_url = href
            elif href.startswith("http://") or href.startswith("https://"):
                continue
            else:
                full_url = urljoin(base_netloc, href)
            
            if len(full_url) > min_length:
                links.add(full_url)
        
        return links

    # ------------------------
    # FINAL OUTPUT
    # ------------------------

    async def get_html(self) -> str:
        return str(self.soup)

