# Implementation Plan: Shub Corpus Scraper (Cold-Email Writer)

## What this is
A reusable scrape-and-index pipeline for any writer, built by cloning the Farza setup. This artifact is the plan + lessons-learned document — NOT the code (code is already in `Shub/`).

## Farza run: what actually happened (real outcomes, not assumptions)

### Setup sequence (what worked, in order)
1. Scaffolded from scratch: `scrapers/`, `runner.py`, `indexer.py`, `config/sources.yaml`, `requirements.txt` — ~30 min.
2. Installed deps in one pip command (`pip install httpx beautifulsoup4 lxml feedparser pyyaml yt-dlp`).
3. Ran `runner.py --source farza_com` → first source live in seconds (2 pages, 2210+6677 chars).
4. Ran `runner.py --source substack --limit 60` → 23 posts scraped via RSS feed + archive API in ~60s.
5. heyclicky (sitemap + subpages) → 9 pages in seconds. GDoc → 4,936 chars (export?format=txt worked). Buildspace letter → 8,570 chars via buildspace.so/letter.
6. YouTube (yt-dlp --flat-playlist) → 3 videos (titles+descs).
7. X → **0 posts** until Agent-Reach + twitter-cli + cookies were wired up (see below).
8. `indexer.py` → `data/corpus.jsonl` (697 docs, ~419k chars).

### X-specific: the actual blocker chain
- **snscrape is dead post-2024** — don't even try it. Wasted a lane on first attempt.
- **Agent-Reach is NOT a scraper** — it's a capability-layer installer/router. Real reads go through `twitter-cli` (or OpenCLI / bird legacy). `agent-reach doctor` only checks presence, never validates live creds.
- **Auth is the hard gate**: `twitter-cli` needs x.com cookies from Cookie-Editor (`auth_token` + `ct0`). No zero-config path. Must use a burner/side account (ban risk on main).
- **Volume cap is upstream, not our code**: `twitter user-posts FarzaTV` cursor exhausts at ~741 raw/session. `twitter search "from:FarzaTV"` 404s upstream (queryId rotation). So even with perfect auth, hard ceiling is ~741 raw per session.
- **429 walls** ≈60 req/window — absorbed via backoff (10s→300s cap) but cap each window at ~650 kept. 9+ events absorbed in the Farza run.
- **Stealth worked**: GraphQL pages of 40, 3–8s randomized sleep + client ~2.5s jitter, cursor resume via `/tmp/x_scrape_checkpoint.json`, incremental `--out` writes. X did not detect it.
- **Text-only filter**: classify() dropped 58 RT, 9 replies, 6 media-only, 1 emoji-only; kept 260 posts with attached media (text extracted, `has_media=true`). Never downloaded media bytes.
- **Final**: 659 indexed X originals (2019–2026, median 161 chars) out of 741 raw.

### Other blockers hit
- Instagram: login-walled, stub only. X/Twitter same class of problem.
- GDoc: needs "Anyone with link can view" else 403 — export?format=txt worked because doc was public.
- Substack archive API (`/api/v1/archive?sort=new&offset={o}&limit=50`) worked reliably; RSS gave latest ~20.

## Shub run: optimized playbook (apply these, skip the mistakes)

### Pre-flight checklist (do BEFORE touching code)
- [ ] Get Shub's Twitter/X handle → feed to `twitter user {handle} --yaml` to verify creds + pull bio FIRST. If this fails, stop; fix auth before anything else. Saves a full lane.
- [ ] Get Shub's website URL → fetch root with httpx HEAD to confirm 200 + check for `/feed`, `/rss`, `/sitemap.xml`, `/blog`, `/essays` subpaths. Map subpaths before writing scrapers.
- [ ] Confirm whether the website has an RSS/feed (most writers do). If yes, start there — it's 10x faster than HTML crawling individual posts.
- [ ] Check if blog is on a CMS (WordPress, Ghost, Substack-hosted) — CMS usually has `/wp-json/wp/v2/posts` or Ghost API, far easier than HTML parsing.
- [ ] Check website's `/about`, `/essays`, `/writings` nav links — these are usually the essay index pages.

### Execution order (parallel where possible)
1. **X scrape** (longest, needs your cookies) — start this FIRST and let it run in background:
   - `twitter user-posts {handle} --max 20-50 --full-text --yaml -o /tmp/shub_p{n}.yaml` with cursor resume
   - 3–8s jittered sleeps, checkpoint at `/tmp/shub_x_checkpoint.json`
   - Text-only filter (drop RT/reply/media-only/emoji-only; keep text from media-attached posts)
   - Target: as many as the cursor yields (usually 700–1500 raw per session, then bottom-out)
   - If search works: `twitter search "from:{handle} -filter:replies -filter:retweets"` as backfill
2. **Website scrape** (parallel to X, fast):
   - RSS/feed first (if exists) → all posts in one call
   - Sitemap crawl for pages (`/about`, `/essays`, `/writings`, `/blog`)
   - Follow nav links, extract essay bodies with `clean_text()`
   - Per-page meta: `{source_page, section, topic}` tags in `meta` field
3. **Any other sources** (YouTube, Instagram, GitHub, newsletter) — add only if user provides them; don't guess.
4. **`indexer.py`** → `Shub/data/corpus.jsonl` + `Shub/data/index.json`

### What the index MUST include (lesson from Farza: missing this was painful)
Every record gets a `meta` block with:
- `source_page`: exact URL where this text was found
- `section`: which section of the page (e.g. "about", "essay-3", "changelog-v1.0.49")
- `topic`: short tag (e.g. "career-philosophy", "product-vision", "personal-update", "technical-deep-dive")
- `date_found`: when scraped
- `has_media`: bool
- For X: `likes`, `rts`, `is_reply`, `is_retweet`
This lets you query "show me all his essays about X written on page Y" — essential for learning how he writes on specific topics.

### Stealth & rate-limit rules (reuse from Farza, proven)
- GraphQL pages of 40 for X
- Sleep 3–8s randomized + client built-in jitter
- Cursor resume; checkpoint to /tmp (NOT repo)
- Backoff 10s→300s cap; stop after 5 consecutive errors
- Never print tokens; env-vars only; never write to files
- Text-only filter: drop media-only, keep text from media-attached posts

### Scaffold time estimate
- `Shub/` already exists with scrapers copied from Farza — **~10 min** to adapt `sources.yaml` + write 1–2 new scrapers for his website (likely just RSS + one HTML-crawl scraper).
- X scraper (`scrapers/x_twitter_cli.py`) is already in `Shub/scrapers/` — reuse directly, just swap handle.
- **Total to first-scrape: ~30–60 min** after you give handle + URL (vs ~4 hours for Farza).

### Known unknowns (will resolve once you give handle + URL)
- Does he have an RSS feed? (check root + /feed + /rss)
- Is his website on a CMS with a public API?
- Is his X timeline accessible at ~741 raw/session ceiling, or lower?
- Are essays behind a login / paywall?
- Does he have a Substack, Ghost, or newsletter archive separate from website?

### What I still need from you to proceed
1. **His Twitter/X handle** (e.g. @shub) — I verify creds first, then run the stealth scrape.
2. **His website URL** — I HEAD-fetch, map subpaths, check for RSS/CMS API, then crawl.
3. (Optional) Any other known sources: YouTube, Instagram, Substack, GitHub, newsletter.

Once you give me those two, I execute the plan and you get `Shub/data/corpus.jsonl` indexed in under an hour.
