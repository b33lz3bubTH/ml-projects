import re
import os
from pathlib import Path
import sys
content = open("ndtv-test1.html")

# Resolve project root (quant-data-sys)
ROOT_DIR = Path(__file__).resolve().parents[1]

# Add root to python path
sys.path.append(str(ROOT_DIR))

# Now imports work
from src.plugins.html_cleaner import HtmlCleaner
import asyncio


async def main():
    cleaner = HtmlCleaner(content.read())

    meta = await cleaner.extract_meta_tags()
    
    cleaner = await cleaner.clean()
    cleaner = await cleaner.remove_scripts()
    cleaner = await cleaner.remove_css()
    cleaner = await cleaner.remove_iframes()
    cleaner = await cleaner.remove_svg()
    cleaner = await cleaner.remove_junk_text_blocks()
    cleaner = await cleaner.remove_all_classes_and_ids()
    cleaner = await cleaner.remove_empty_tags()
    cleaner = await cleaner.aggressive_cleanup()
    cleaner = await cleaner.keep_only_body()

    cleaner = await cleaner.remove_layout_tags()
    cleaner = await cleaner.collapse_wrappers()
    cleaner = await cleaner.deep_prune_empty()

    images = await cleaner.extract_image_urls()
    
    await cleaner.save("out.html")

    jsonld_blocks = await cleaner.extract_all_json_ld()

    print(f"JSON-LD blocks found: {len(jsonld_blocks)}")
    print(f"Meta tags: {meta}")
    print(f"Images: {images}")



asyncio.run(main())
