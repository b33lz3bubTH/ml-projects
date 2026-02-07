import asyncio
import re
from bs4 import BeautifulSoup, Comment
from pathlib import Path
from typing import List, Set
from urllib.parse import urlparse

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

    async def extract_article_links(self, base_url: str = None) -> Set[str]:
        """Extract article links from the page"""
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

    # ------------------------
    # FINAL OUTPUT
    # ------------------------

    async def get_html(self) -> str:
        return str(self.soup)

