"""Google Doc vision note — public export endpoints."""
from .base import fetch, soup, clean_text, record
import logging
log = logging.getLogger("gdoc")
DOC_ID = "1sfsGQurJ444vXKXcqcHg32SBRYz3LVrvOt4Hwig-ai8"

def scrape() -> list[dict]:
    urls = [
        f"https://docs.google.com/document/d/{DOC_ID}/export?format=txt",
        f"https://docs.google.com/document/d/{DOC_ID}/mobilebasic",
        f"https://docs.google.com/document/d/{DOC_ID}/pub?embedded=true",
    ]
    for url in urls:
        r = fetch(url)
        if not r:
            continue
        ctype = r.headers.get("content-type", "")
        if "text/plain" in ctype or url.endswith("format=txt"):
            text = r.text.strip()
        else:
            text = clean_text(soup(r.text).find("body"))
        if len(text) > 200:
            log.info(f"gdoc via {url} -> {len(text)} chars")
            return [record("gdoc_vision", url, "HeyClicky vision note (Farza)", text, meta={"doc_id": DOC_ID})]
    log.warning("gdoc: doc not public or export blocked; needs sharing set to 'Anyone with link'")
    return [record("gdoc_vision", urls[0], "HeyClicky vision note (Farza)", "", meta={"status": "blocked", "doc_id": DOC_ID})]
