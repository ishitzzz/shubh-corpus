"""farza.com — static personal site + linked pages."""
from urllib.parse import urljoin, urlparse
from .base import fetch, soup, clean_text, record
import logging
log = logging.getLogger("farza_com")

def scrape(base_url: str = "https://farza.com/", max_pages: int = 20) -> list[dict]:
    out, seen, queue = [], set(), [base_url]
    domain = urlparse(base_url).netloc
    while queue and len(seen) < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        r = fetch(url)
        if not r:
            continue
        s = soup(r.text)
        title = s.title.get_text(strip=True) if s.title else ""
        main = s.find("main") or s.find("article") or s.find("body")
        text = clean_text(main)
        out.append(record("farza_com", url, title, text, meta={"chars": len(text)}))
        log.info(f"{url} -> {len(text)} chars")
        for a in s.find_all("a", href=True):
            href = a.get("href", "")
            if not isinstance(href, str) or not href:
                continue
            link = urljoin(url, href).split("#")[0]
            if urlparse(link).netloc == domain and link not in seen and len(seen) + len(queue) < max_pages:
                if link.startswith("http"):
                    queue.append(link)
    return out
