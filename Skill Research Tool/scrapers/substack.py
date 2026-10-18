"""Substack: RSS feed + archive API + full post HTML."""
import httpx, feedparser, time, logging
from .base import fetch, soup, clean_text, record, UA
log = logging.getLogger("substack")
FEED = "https://farza.substack.com/feed"
ARCH = "https://farza.substack.com/api/v1/archive?sort=new&offset={o}&limit=50"

def _post_body(url: str) -> tuple[str, str]:
    r = fetch(url)
    if not r:
        return "", ""
    s = soup(r.text)
    h1 = s.find("h1")
    title = h1.get_text(strip=True) if h1 else (s.title.get_text(strip=True) if s.title else "")
    body = s.find("div", class_="available-content") or s.find("article") or s.find("body")
    return title, clean_text(body)

def scrape(limit: int = 200) -> list[dict]:
    out, seen = [], set()
    # 1) RSS (fast, ~20 latest)
    try:
        d = feedparser.parse(FEED)
        for e in d.entries[:limit]:
            url = e.get("link", "")
            if url and url not in seen:
                seen.add(url)
                t, txt = _post_body(url)
                out.append(record("substack", url, t or e.get("title", ""), txt,
                                 e.get("published", ""), {"via": "rss"}))
                log.info(f"rss {url} -> {len(txt)} chars")
                time.sleep(0.7)
    except Exception as e:
        log.warning(f"rss failed: {e}")
    # 2) Archive API for older posts
    if len(out) < limit:
        off = 0
        with httpx.Client(headers={"User-Agent": UA}, timeout=30, follow_redirects=True) as c:
            while len(out) < limit:
                try:
                    r = c.get(ARCH.format(o=off))
                    if r.status_code != 200:
                        break
                    items = r.json()
                    if not items:
                        break
                    for it in items:
                        slug = it.get("slug") or ""
                        url = f"https://farza.substack.com/p/{slug}" if slug else it.get("canonical_url", "")
                        if not url or url in seen:
                            continue
                        seen.add(url)
                        t, txt = _post_body(url)
                        out.append(record("substack", url, t or it.get("title", ""), txt,
                                         str(it.get("post_date", "")), {"via": "archive", "likes": it.get("reactions", {})}))
                        if len(out) >= limit:
                            break
                        time.sleep(0.7)
                    off += len(items)
                    if len(items) < 50:
                        break
                except Exception as e:
                    log.warning(f"archive offset {off} failed: {e}")
                    break
    return out[:limit]
