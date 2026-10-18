"""X/Twitter @FarzaTV timeline scrape via twitter-cli GraphQL client (cookie auth).

STEALTH TEXT-ONLY harvester:
- Pages of ~40 GraphQL rows with 3-8s randomized sleeps between requests.
- Cursor checkpoint to /tmp/x_scrape_checkpoint.json (outside repo) so reruns resume.
- Exponential backoff on 429/401/403; persistent failure -> STOP gracefully,
  keeping everything collected so far. Never hammer.
- TEXT-ONLY: retweets/replies dropped; media bytes never downloaded; records
  keep text + meta (likes/rts/replies/views/lang/has_media) only.

Credentials ONLY from env TWITTER_AUTH_TOKEN / TWITTER_CT0.
Never logged, printed, or written to any file.

Usage:
    TWITTER_AUTH_TOKEN=... TWITTER_CT0=... python3 -m scrapers.x_twitter_cli
    TWITTER_AUTH_TOKEN=... TWITTER_CT0=... python3 -m scrapers.x_twitter_cli --target 3500 --handle FarzaTV
"""
import argparse
import json
import logging
import os
import random
import re
import sys
import time
from pathlib import Path

log = logging.getLogger("x_twitter_cli")

CHECKPOINT = Path("/tmp/x_scrape_checkpoint.json")
PAGE_SIZE = 40
TARGET_DEFAULT = 3500
MAX_CONSECUTIVE_ERRORS = 5
BACKOFF_BASE = 10.0  # seconds, doubled per consecutive error + jitter

_URL_RE = re.compile(r"https?://\S+")
_WORD_RE = re.compile(r"[A-Za-z0-9\u00c0-\u024f\u0370-\u03ff\u0400-\u04ff\u4e00-\u9fff]")


def _creds():
    token = os.environ.get("TWITTER_AUTH_TOKEN", "")
    ct0 = os.environ.get("TWITTER_CT0", "")
    if not token or not ct0:
        raise SystemExit("missing TWITTER_AUTH_TOKEN / TWITTER_CT0 env vars (never pass via files)")
    return token, ct0


def meaningful_text(text: str) -> str:
    """Strip bare URLs; return remaining text (may be empty)."""
    stripped = _URL_RE.sub("", text or "")
    return "\n".join(ln.strip() for ln in stripped.split("\n") if ln.strip()).strip()


def is_keeper(text: str) -> bool:
    """Real words present (not empty / emoji-only / punctuation-only)?"""
    body = meaningful_text(text)
    return len(_WORD_RE.findall(body)) >= 3


def classify(tweet, handle: str) -> str:
    """Return 'keep' or a drop reason. Never logs credential-adjacent data beyond ids."""
    author = (getattr(getattr(tweet, "author", None), "screen_name", "") or "").lower()
    if getattr(tweet, "is_retweet", False) or getattr(tweet, "retweeted_by", None):
        return "retweet"
    if author and author != handle.lower():
        return "foreign-author"
    text = getattr(tweet, "text", "") or ""
    if text.lstrip().startswith("@"):
        return "reply"
    if not is_keeper(text):
        if getattr(tweet, "media", None):
            return "media-only"
        return "empty-or-emoji-only"
    return "keep"


def to_record(tweet, iso_date: str) -> dict:
    tid = getattr(tweet, "id", "")
    m = getattr(tweet, "metrics", None)
    return {
        "source": "x",
        "url": f"https://x.com/{getattr(getattr(tweet, 'author', None), 'screen_name', 'FarzaTV')}/status/{tid}",
        "title": "",
        "text": getattr(tweet, "text", "") or "",
        "date": iso_date,
        "meta": {
            "id": tid,
            "likes": getattr(m, "likes", 0),
            "rts": getattr(m, "retweets", 0),
            "replies": getattr(m, "replies", 0),
            "quotes": getattr(m, "quotes", 0),
            "views": getattr(m, "views", 0),
            "lang": getattr(tweet, "lang", ""),
            "has_media": bool(getattr(tweet, "media", None)),
        },
    }


def load_checkpoint() -> dict:
    try:
        return json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_checkpoint(state: dict) -> None:
    CHECKPOINT.write_text(json.dumps(state), encoding="utf-8")


def scrape(handle: str = "FarzaTV", target: int = TARGET_DEFAULT,
           resume: bool = True, max_pages: int = 150, out_path: str = "") -> dict:
    from twitter_cli.client import TwitterClient
    from twitter_cli.graphql import FEATURES
    from twitter_cli.parser import _deep_get, parse_timeline_response
    from twitter_cli.timeutil import format_iso8601

    token, ct0 = _creds()
    client = TwitterClient(token, ct0)

    profile = client.fetch_user(handle)
    user_id = profile.id
    log.info("resolved @%s id=%s followers=%d tweets=%d", handle, user_id,
             profile.followers_count, profile.tweets_count)

    def get_instructions(data):
        return _deep_get(data, "data", "user", "result",
                         "timeline_v2", "timeline", "instructions")

    extra = {"userId": user_id, "withQuickPromoteEligibilityTweetFields": True,
             "withVoice": True, "withV2Timeline": True}

    state = load_checkpoint() if resume else {}
    cursor = state.get("cursor")
    seen: set = set(state.get("seen_ids", []))
    kept: list = []
    # Rehydrate kept ids only (texts rebuilt from raw cache? no - refetch not needed;
    # caller merges with existing x.jsonl by URL, so we only need new pages).
    stats = {"raw": state.get("raw", 0), "kept": state.get("kept", 0),
             "dropped": state.get("dropped", {}), "pages": state.get("pages", 0),
             "rate_limit_events": state.get("rate_limit_events", 0)}
    if cursor:
        log.info("resuming from checkpoint: pages=%d raw=%d kept=%d",
                 stats["pages"], stats["raw"], stats["kept"])

    consecutive_errors = 0
    page = stats["pages"]
    seen_cursors: set = set(state.get("seen_cursors", []))
    if cursor:
        seen_cursors.add(cursor)
    dead_pages = 0  # consecutive pages yielding zero new raw tweets
    out_fh = None
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        out_fh = open(out_path, "a" if resume else "w", encoding="utf-8")
    try:
        while stats["kept"] < target and page < max_pages:
            variables = {"count": PAGE_SIZE, "includePromotedContent": False,
                         "latestControlAvailable": True, "requestContext": "launch"}
            variables.update(extra)
            if cursor:
                variables["cursor"] = cursor
            try:
                data = client._graphql_get("UserTweets", variables, FEATURES)
            except Exception as exc:  # noqa: BLE001 - must survive all upstream errors
                msg = str(exc)[:200]
                code = getattr(exc, "status_code", None)
                stats["rate_limit_events"] += 1 if (code == 429 or "429" in msg or "88" in msg) else 0
                consecutive_errors += 1
                wait = min(BACKOFF_BASE * (2 ** (consecutive_errors - 1)), 300) + random.uniform(0, 3)
                log.warning("page %d error (%s). backing off %.0fs [%d/%d]",
                            page + 1, msg, wait, consecutive_errors, MAX_CONSECUTIVE_ERRORS)
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS or code in (401, 403):
                    log.warning("persistent failure; stopping gracefully with %d kept", stats["kept"])
                    break
                time.sleep(wait)
                continue
            consecutive_errors = 0
            tweets, next_cursor = parse_timeline_response(data, get_instructions)
            new_raw = 0
            for tw in tweets:
                if not getattr(tw, "id", None) or tw.id in seen:
                    continue
                seen.add(tw.id)
                stats["raw"] += 1
                new_raw += 1
                verdict = classify(tw, handle)
                if verdict != "keep":
                    stats["dropped"][verdict] = stats["dropped"].get(verdict, 0) + 1
                    continue
                try:
                    iso = format_iso8601(tw.created_at)
                except Exception:  # noqa: BLE001
                    iso = tw.created_at or ""
                rec = to_record(tw, iso)
                kept.append(rec)
                if out_fh:
                    out_fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    out_fh.flush()
                stats["kept"] += 1
                if stats["kept"] >= target:
                    break
            dead_pages = dead_pages + 1 if new_raw == 0 else 0
            page += 1
            stats["pages"] = page
            if not next_cursor or next_cursor == cursor or next_cursor in seen_cursors:
                log.info("cursor exhausted/stall/cycle after page %d", page)
                cursor = next_cursor
                break
            if dead_pages >= 10:
                log.info("dead zone: 10 pages with zero new tweets; stopping at page %d", page)
                cursor = next_cursor
                break
            cursor = next_cursor
            seen_cursors.add(cursor)
            save_checkpoint({"cursor": cursor, "seen_ids": sorted(seen)[-6000:],
                             "seen_cursors": sorted(seen_cursors)[-600:], **stats})
            log.info("page %d: raw=%d kept=%d", page, stats["raw"], stats["kept"])
            if stats["kept"] >= target:
                break
            time.sleep(random.uniform(3, 8))
    finally:
        if out_fh:
            out_fh.close()

    save_checkpoint({"cursor": cursor, "seen_ids": sorted(seen)[-6000:],
                     "seen_cursors": sorted(seen_cursors)[-600:], **stats})
    return {"handle": handle, "bio": profile.bio, "profile_url": f"https://x.com/{handle}",
            "records": kept, "stats": stats,
            "done": stats["kept"] >= target or not cursor}


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", default="FarzaTV")
    ap.add_argument("--target", type=int, default=TARGET_DEFAULT)
    ap.add_argument("--max-pages", type=int, default=150)
    ap.add_argument("--no-resume", action="store_true")
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)
    result = scrape(args.handle, args.target, resume=not args.no_resume,
                    max_pages=args.max_pages, out_path=args.out)
    print(json.dumps({k: v for k, v in result.items() if k != "records"},
                     ensure_ascii=False, indent=2))
    print(f"NEW_RECORDS={len(result['records'])}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
