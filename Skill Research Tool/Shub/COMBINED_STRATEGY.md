# Shub Corpus Scraper — Combined Strategy & Execution Plan

## Person profile (from website, context for everything)
Shubh — 18 years old, dropped out of Imperial College London, moved to Bangalore, raised $5M for a venture fund. Writes blog, daily entries, and essays at shubhxho.com. X: @shubhgupta.

## Repo analysis summary

### crawl4ai (83.9k ⭐) — BEST for website text extraction
- Async Python + Playwright browser + LLM extraction pipeline
- `crwl <url> -o markdown` CLI; Python API with `LLMExtractionStrategy` + Pydantic schema
- Can extract title/date/topic as structured JSON in one call (needs OpenAI API key)
- **Verdict**: Use for extracting each essay/blog post with date + topic metadata. `crwl -q "Extract title, date written, topic" --deep-crawl bfs --max-pages 50`
- Weak: needs LLM API key for structured extraction; slower than pure HTTP

### user-scanner (4.9k ⭐) — OSINT identity, NOT a content scraper
- 880+ platforms, email + username intelligence
- Returns avatars, bios, follower counts, exposed emails, breach intel
- **Verdict**: Use ONLY for identity enrichment (find his name, location, college, social accounts). NOT for extracting essay text.
- Fit: identity layer only

### spiderfoot — OSINT deep identity correlation
- 200+ modules, DNS/subdomain/email/phone/social, correlation engine
- Slow, needs API keys for commercial sources
- **Verdict**: Deep identity enrichment from a single seed (email → name → location → social accounts). Use as the identity deep-dive layer.

### sherlock — fast username existence check
- 500+ platforms, yes/no existence check, fast, no API keys
- Returns profile URLs only, no content
- **Verdict**: First pass — confirm which platforms @shubhgupta exists on. Feed those URLs into deeper scrapers.

### social-analyzer — broad profile metadata
- 1000+ sites, quality scoring (0–100), metadata extraction (emails, links), screenshots
- NodeJS + Python CLI + Web App
- **Verdict**: Extract structured profile metadata (bio, links, emails, follower counts) from @shubhgupta across platforms. Best single-tool profile enrichment.

### Agent-Reach + twitter-cli (from Farza run) — X scraping
- twitter-cli + Cookie-Editor auth (same cookies reused)
- `twitter user-posts shubhgupta --max 50 --full-text --yaml` with cursor resume
- ~741 raw/session cap, 40-page GraphQL, 3–8s stealth sleep
- Text-only filter (drop RT/reply/media-only)
- **Verdict**: Reuse `scrapers/x_twitter_cli.py` from Farza/Shub, swap handle to shubhgupta

## Recommended execution pipeline

### Phase 1 — Identity & Profile Enrichment (OSINT)
Goal: Who is Shubh? Where from? College? What platforms exist? Connections?
1. `sherlock shubhgupta` → list all platforms where handle exists
2. `social-analyzer --username shubhgupta --metadata` → structured profile metadata (bio, links, emails)
3. `user-scanner -u shubhgupta --cross-scan` → avatar, bios, follower counts, exposed emails
4. `spiderfoot -t shubhgupta` OR `spiderfoot -e shubhgupta@gmail.com` (if email found) → deep identity correlation (name, location, college, phone)
Output: `Shub/data/raw/identity_osint.json` — who he is, where from, college (Imperial College London confirmed), social graph

### Phase 2 — X/Twitter scrape (stealth, text-only, full reply context)
Goal: All @shubhgupta posts WITH full context of who he's replying to and what the conversation is about
1. Verify creds: `twitter user shubhgupta --yaml` → save bio as first record
2. Paginate original posts: `twitter user-posts shubhgupta --max 50 --full-text --yaml -o /tmp/shub_p{n}.yaml` with cursor resume
3. STEALTH: 40-page GraphQL, 3–8s sleep + client jitter, checkpoint `/tmp/shub_x_checkpoint.json`
4. For each post: extract reply context — if `in_reply_to_status_id`, fetch that tweet's text + author to capture "what is he replying to, who, what context"
5. Text-only filter: drop RT/reply as original posts; KEEP text from posts with attached media
6. Write: `Shub/data/raw/x_raw.jsonl` with schema {source:"x", url, text, date, meta:{likes, rts, is_reply, reply_to_text, reply_to_author, has_media}}
Target: ~741 raw/session, then bottom-out; more via new session/cursor

### Phase 3 — Website full crawl (RSS + sitemap + crawl4ai)
Goal: All essays/blog/daily posts with full page context (date, topic, what it's about, why)
1. RSS feed (fastest path): fetch `https://shubhxho.com/feed.xml` → all posts in one call with titles + dates + excerpts
2. Sitemap: parse `https://shubhxho.com/sitemap.xml` → all page URLs
3. For each essay/blog post URL: use crawl4ai `crwl <url> -q "Extract title, date written, topic, full body text" --deep-crawl bfs` → structured JSON with title, date, topic, full Markdown text
4. Also crawl non-post pages: /about, /writing/*, /daily/*, /blog/* — extract section + topic + full text
5. For pages without RSS (static pages), use existing scrapers/base.py fetch+soup as fallback
Output: `Shub/data/raw/website_raw.jsonl` with schema {source:"shubh_website", url, title, text, date, meta:{section, topic, crawl_method}}

### Phase 4 — Index with full context
1. `indexer.py` (adapted to merge X + website + identity into `Shub/data/corpus.jsonl`)
2. Each record gets full `meta` block: source_page, section, topic, date, reply_context (for X), identity_context (for OSINT), crawl_method
3. `Shub/data/index.json` — total counts per source + topics breakdown

## Best method combinations for the whole pipeline

| Layer | Tool | Why |
|---|---|---|
| Username existence | sherlock | Fast 500+ platform check, no keys |
| Profile metadata | social-analyzer | 1000+ sites, quality score, emails/links |
| Deep identity | spiderfoot | 200+ modules, correlation engine, from email/name |
| Identity (alt) | user-scanner | 880+ platforms, avatar/bio/breach intel |
| X posts + reply context | twitter-cli (Agent-Reach) | Stealth, cookies, cursor resume, full reply chain |
| Website RSS/blog | crawl4ai (`crwl -q`) | LLM extraction: title + date + topic + full text in one call |
| Website fallback | scrapers/base.py (httpx+soup) | Pure HTTP, no API key, works on any site |
| Identity deep-dive | user-scanner + spiderfoot combo | Cross-scan exposed handles from profiles |

## Scrapers needed (new for Shub, beyond what exists)
1. `scrapers/x_twitter_cli.py` — REUSE from Farza, swap handle to shubhgupta + add reply_context extraction
2. `scrapers/shubh_website.py` — NEW: RSS feed parser (feedparser) + sitemap crawler + crawl4ai integration for structured extraction (date/topic)
3. `scrapers/identity_osint.py` — NEW: orchestrates sherlock + social-analyzer + spiderfoot + user-scanner calls, merges into identity JSON
4. `scrapers/base.py` — REUSE (unchanged)
5. `runner.py`, `indexer.py`, `config/sources.yaml` — ADAPT from Farza (swap source names, add identity/source metadata)

## Stealth & rate-limit rules (proven from Farza)
- X: 40-page GraphQL, 3–8s sleep + client jitter, cursor resume at `/tmp/shub_x_checkpoint.json`
- Backoff 10s→300s cap, stop after 5 consecutive errors
- Never print tokens; env-vars only; never write to files
- Text-only filter: keep text from media-attached posts, drop media-only

## What I still need from you
1. **OpenAI API key** (optional but needed for crawl4ai structured extraction — if you want date/topic auto-extraction from essays; otherwise I'll extract manually)
2. **Permission to install**: `twitter-cli` (reuse existing cookies), `crawl4ai`, `sherlock`, `social-analyzer`, `spiderfoot`, `user-scanner`
3. **Any other platforms** he's active on (YouTube, GitHub, LinkedIn?) — I'll check with sherlock

Once approved, I execute Phase 1 → 2 → 3 → 4 and deliver `Shub/data/corpus.jsonl` indexed with full context.
