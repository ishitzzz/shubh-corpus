"""X/Twitter @FarzaTV — best-effort. X is login/rate-limit walled.

Priority order:
1. snscrape (no key): `snscrape twitter-user FarzaTV` — often blocked in 2025-26, but try first.
2. X API v2 (needs bearer): from:FarzaTV -filter:replies.
3. Manual export fallback: user pastes URLs via data/x_manual.jsonl.

This module tries (1), else writes a stub + instructions.
"""
import json, subprocess, logging
from pathlib import Path
from .base import record
log = logging.getLogger("x")

def _via_snscrape(handle: str = "FarzaTV", limit: int = 1000) -> list[dict]:
    cmd = ["snscrape", "--jsonl", "--max-results", str(limit), f"twitter-user {handle}"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except FileNotFoundError:
        log.warning("snscrape not installed")
        return []
    out = []
    for line in (p.stdout or "").splitlines():
        try:
            t = json.loads(line)
        except Exception:
            continue
        # skip replies/RTs for pure voice
        if t.get("inReplyToTweetId") or (t.get("retweetedTweet") or t.get("quotedTweet") and t.get("content", "").startswith("RT ")):
            continue
        out.append(record("x", t.get("url", ""), "", t.get("rawContent", "") or t.get("content", ""),
                          str(t.get("date", "")), {"likes": t.get("likeCount", 0), "rts": t.get("retweetCount", 0)}))
    return out

def scrape(handle: str = "FarzaTV", limit: int = 1000) -> list[dict]:
    out = _via_snscrape(handle, limit)
    if out:
        log.info(f"x via snscrape -> {len(out)} posts")
        return out
    # manual fallback
    manual = Path("data/x_manual.jsonl")
    if manual.exists():
        rows = [json.loads(l) for l in manual.read_text(encoding="utf-8").splitlines() if l.strip()]
        log.info(f"x via manual -> {len(rows)} posts")
        return rows
    log.warning("x: snscrape blocked/missing and no data/x_manual.jsonl. "
                "Options: X API v2 (from:FarzaTV -filter:replies), Nitter instance, or paste top posts into data/x_manual.jsonl "
                "as {\"source\":\"x\",\"url\":...,\"title\":\"\",\"text\":...,\"date\":...}. Bio: include https://x.com/FarzaTV profile text.")
    return [record("x", f"https://x.com/{handle}", f"@{handle} bio (manual step needed)", "",
                   meta={"status": "needs-manual-or-api", "query": f"from:{handle} -filter:replies"})]
