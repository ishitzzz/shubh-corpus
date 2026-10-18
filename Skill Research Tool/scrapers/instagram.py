"""Instagram @farza954 — login-walled; best-effort stub."""
from .base import record
import logging
log = logging.getLogger("instagram")

def scrape(handle: str = "farza954") -> list[dict]:
    log.warning("instagram: login-walled, skipping auto-scrape. If needed, manually paste captions into data/ig_manual.jsonl.")
    return [record("instagram", f"https://www.instagram.com/{handle}/", f"@{handle} captions (manual step needed)", "",
                   meta={"status": "needs-manual"})]
