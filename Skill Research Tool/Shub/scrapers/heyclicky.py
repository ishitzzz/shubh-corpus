"""heyclicky.com — sitemap + subpage crawl."""
from urllib.parse import urlparse
from .base import fetch, soup, clean_text, record
import logging
log = logging.getLogger("heyclicky")

def scrape(base: str = "https://heyclicky.com/", max_pages: int = 30) -> list[dict]:
    urls = [base]
    for sm in ["https://heyclicky.com/sitemap.xml", base + "sitemap.xml"]:
        r = fetch(sm)
        if r and "<url" in r.text:
            s = soup(r.text)
            for loc in s.find_all("loc"):
                u = loc.get_text(strip=True)
                if u and u not in urls:
                    urls.append(u)
            break
    # always include likely subpages
    for p in ["about", "changelog", "vision", "blog", "pricing"]:
        u = base.rstrip("/") + "/" + p
        if u not in urls:
            urls.append(u)
    out = []
    for url in urls[:max_pages]:
        r = fetch(url)
        if not r or r.status_code != 200:
            continue
        s = soup(r.text)
        title = s.title.get_text(strip=True) if s.title else ""
        text = clean_text(s.find("main") or s.find("article") or s.find("body"))
        if len(text) < 50:
            continue
        out.append(record("heyclicky", url, title, text, meta={"chars": len(text)}))
        log.info(f"{url} -> {len(text)} chars")
    return out
