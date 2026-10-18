"""Shared fetch / parse / save helpers. Stdlib + httpx + bs4 only."""
import json, time, logging
from pathlib import Path
import httpx
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) farza-corpus-bot/1.0"
TIMEOUT = 30

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

def fetch(url: str, timeout: int = TIMEOUT, retries: int = 3, delay: float = 1.0) -> httpx.Response | None:
    for i in range(retries):
        try:
            r = httpx.get(url, headers={"User-Agent": UA}, timeout=timeout, follow_redirects=True)
            if r.status_code == 200:
                return r
            logging.warning(f"fetch {url} -> {r.status_code}")
        except Exception as e:
            logging.warning(f"fetch {url} attempt {i+1} failed: {e}")
        time.sleep(delay * (i + 1))
    return None

def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")

def clean_text(el) -> str:
    """Extract readable text, preserve line breaks for short-paragraph style."""
    if el is None:
        return ""
    for tag in el.find_all(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = el.get_text(separator="\n", strip=True)
    # collapse 3+ newlines, strip media-only lines
    lines = []
    for ln in text.split("\n"):
        ln = ln.strip()
        if not ln:
            continue
        if ln.startswith(("http://", "https://")) and len(ln.split()) <= 2:
            continue  # pure media link, drop
        lines.append(ln)
    return "\n".join(lines)

def save_jsonl(path: str | Path, records: list[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    logging.info(f"wrote {len(records)} records -> {path}")

def record(source: str, url: str, title: str = "", text: str = "", date: str = "", meta: dict | None = None) -> dict:
    return {"source": source, "url": url, "title": title or "", "text": text or "", "date": date or "", "meta": meta or {}}
