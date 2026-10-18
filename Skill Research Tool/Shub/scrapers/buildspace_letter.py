"""Buildspace closing letter — live + Wayback fallbacks."""
from .base import fetch, soup, clean_text, record
import logging
log = logging.getLogger("buildspace_letter")
CANDIDATES = [
    "https://buildspace.so/a-letter-to-you",
    "https://buildspace.so/letter",
    "https://web.archive.org/web/2024/https://buildspace.so/a-letter-to-you",
    "https://web.archive.org/web/2024/https://buildspace.so/updates/a-letter-to-you",
]

def scrape() -> list[dict]:
    for url in CANDIDATES:
        r = fetch(url)
        if not r:
            continue
        s = soup(r.text)
        text = clean_text(s.find("article") or s.find("main") or s.find("body"))
        if len(text) > 500:
            title = s.title.get_text(strip=True) if s.title else "Buildspace closing letter"
            log.info(f"letter via {url} -> {len(text)} chars")
            return [record("buildspace_letter", url, title, text)]
    log.warning("letter not found at known URLs; check X announcement post for exact link")
    return []
