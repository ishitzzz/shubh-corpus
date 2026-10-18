"""YouTube @farzatv — titles + descriptions only via yt-dlp (no transcripts)."""
import json, subprocess, logging
from .base import record
log = logging.getLogger("youtube")

def scrape(channel: str = "https://www.youtube.com/@farzatv", limit: int = 100) -> list[dict]:
    cmd = ["yt-dlp", "--flat-playlist", "--dump-single-json", "--playlist-end", str(limit), channel]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if p.returncode != 0:
            log.warning(f"yt-dlp flat-playlist failed: {p.stderr[:300]}")
            return []
        data = json.loads(p.stdout or "{}")
        out = []
        for e in (data.get("entries") or [])[:limit]:
            vid = e.get("id", "")
            url = e.get("url") or (f"https://www.youtube.com/watch?v={vid}" if vid else "")
            title = e.get("title", "")
            desc = e.get("description", "") or ""
            out.append(record("youtube", url, title, desc, str(e.get("upload_date", "") or e.get("timestamp", "")),
                             {"channel": "@farzatv", "id": vid}))
        # flat mode often lacks descriptions -> fetch per-video desc for first N
        if out and not any(r["text"] for r in out):
            log.info("flat mode has no descriptions; run with --write-info-json for full desc")
        log.info(f"youtube -> {len(out)} videos")
        return out
    except FileNotFoundError:
        log.warning("yt-dlp not installed; pip install yt-dlp")
        return []
    except Exception as e:
        log.warning(f"youtube failed: {e}")
        return []
