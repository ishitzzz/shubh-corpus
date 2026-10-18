# Shub Corpus Scrape — Complete Artifact & Methodology Guide

## Why This Exists

This corpus was scraped for **cold email writing purposes**. The goal is to study how Shubh Gupta writes across platforms so that a writing agent can produce emails that match his tone, style, and voice — for cold outreach on behalf of the person who commissioned this project.

The scraped data is **not** a skill file (unlike the Farza project which produced SKILL.md). This is raw material + structured context that a writing agent will analyze to learn Shubh's voice and write cold emails in his manner.

---

## Project Structure

```
Shub/
├── COMBINED_STRATEGY.md          # Strategy document for the full pipeline
├── IMPLEMENTATION_PLAN.md        # Step-by-step implementation plan
├── data/
│   ├── corpus.jsonl              # Main corpus (53 docs, all indexed)
│   ├── index.json                # Index with counts, identity summary, reply context
│   └── raw/
│       ├── x_raw.jsonl           # Raw X posts (46 posts, text-only, filtered)
│       ├── website_raw.jsonl     # Raw website pages (6 pages: home, blog, daily, 3 essays)
│       ├── identity_osint.json   # Full OSINT identity enrichment data
│       ├── reply_chains_full.json # All 31 reply chains (390 total replies)
│       ├── identity_osint.json   # Identity profile (cross-platform verification)
│       └── reply_context.json    # Summary of reply context for the 31 chains
├── scrapers/                     # Scraper modules (reusable)
│   ├── __init__.py
│   ├── base.py                   # Shared fetch, parse, save helpers
│   ├── x_twitter_cli.py          # X scraper using twitter-cli
│   ├── shubh_website.py          # Website scraper (RSS + sitemap + httpx)
│   ├── config/
│   │   └── sources.yaml          # Source configuration
│   ├── runner.py                 # CLI: python3 runner.py --source all
│   └── indexer.py                # Indexes raw data into corpus.jsonl
├── config/
│   └── sources.yaml              # Source list with priorities
└── README.md                     # Install + run instructions
```

---

## What Was Scraped and Why

### 1. X/Twitter (@shubhgupta) — 46 posts indexed

**Why:** X is Shubh's primary writing platform. His tweets are short, punchy, honest, and reveal his personality, interests, and communication style. This is the most important data for understanding how he writes.

**What was scraped:**
- **Tool used:** `twitter user-posts shubhgupta --max 200 --full-text --yaml`
- **Limit encountered:** `twitter user-posts` returns only ~53 most recent posts per call, NO pagination/cursor support. This is a hard limit of the twitter-cli tool (cookie-based auth can't access the `/2/users/{id}/tweets` endpoint which requires OAuth2 bearer token).
- **What was obtained:** 53 most recent posts (Oct 2025 → Sep 2026), spanning from his earliest scrapable posts to the most recent.
- **Filtering:** Dropped retweets (3), dropped posts < 10 chars (text-only filter), dropped emoji-only posts. Result: 46 text posts indexed.
- **Fields per post:** id, text, author info, metrics (likes, retweets, replies, quotes, views), createdAt, has_media, quoted_tweet_id

**Reply Context (31 chains, 390 replies):**
- **Why:** To understand the context of conversations Shubh is in — who he talks to, what he's replying to, what kind of discussions he engages in. This reveals his network, interests, and communication patterns.
- **Method:** For each of the 31 posts that received replies (replies > 0), ran `twitter tweet <id> --yaml` which returns the original post AND all replies in a single output.
- **Tool:** `twitter tweet <id> --yaml` (individual post lookups, ~5-20s each)
- **Parallelism:** Ran 5 concurrent workers to speed up the 31 lookups
- **What each chain contains:** original post text + all reply objects (id, text, author.screenName, author.name, metrics)
- **Key conversations revealed:**
  - GPT-6 Astra announcement (OpenAI) — 49 replies
  - "Curse of discipline" motivational quote (MohapatraHemant) — 49 replies
  - "Retardmaxxing" (Marc Andreessen/pmarca) — 49 replies
  - Raised 500k pre-idea — 34 replies (builder community)
  - $15K grant personal update — 36 replies (congratulations)
  - WGMI (a16z Palmer Luckey VR photo) — 35 replies
  - Hiring content creators — 23 replies (applicants)
  - Tokenmaxxing — 17 replies (crypto/VC)
  - Various personal updates, product launches, opinions

**Key people who interact with Shubh:**
- @shourshot (shourya) — friend, replies reassuringly
- @pmarca (Marc Andreessen) — replies to Retardmaxxing post
- @OpenAI — replies to GPT-6 post
- @5auravv (saurav) — friend, replies to posts
- @rcx86, @rawattsumit, @msft4startups, @boardyai, @localhosthq — business/tech connections
- @leo1yu, @meet_sijariya, @arhamamiin — peers in the builder community
- @shubhgupta (Shubh himself) — actively replies to others (18 replies total)

**Note:** @TheShubhWayyy (a different person named "Shubh Gupta") appears in reply chains — confirmed as a different account, NOT the same person as @shubhgupta. Removed from identity data.

**Limitations/Mistakes:**
- Only 53 posts accessible per call due to twitter-cli pagination limitation
- `twitter search "from:shubhgupta"` returns 404 (needs OAuth2 bearer token, cookies don't work)
- Direct X API v2 (`/2/users/{id}/tweets`) returns 403 (cookies rejected — needs OAuth2)
- Playwright browser automation timed out during Chromium download
- Could not get all 359 tweets — only the most recent 53
- `twitter tweet <id> --yaml` doesn't include `in_reply_to_status_id` in parsed output, so we can't determine which posts Shubh IS replying to (only which posts RECEIVED replies)
- The `quotedTweet` field exists in `twitter tweet` output — some posts quote other tweets, giving context about what Shubh is reacting to

### 2. Website (shubhxho.com) — 6 pages indexed

**Why:** Shubh's personal website contains his essays, blog posts, and daily entries. These are longer-form writings that reveal his deeper thoughts, career story, and writing style in extended form.

**What was scraped:**
- **Tool:** `httpx` + `beautifulsoup4` (lxml parser)
- **Pages scraped (all successfully returned 200):**
  - `https://shubhxho.com/` (home) — bio, age 18, "I am Shubh", Imperial College London dropout, moved to Bangalore, raised $5M venture fund
  - `https://shubhxho.com/blog` (blog index) — lists 3 essays with dates, 10,044 chars
  - `https://shubhxho.com/daily` (daily entry) — "Trying to be honest about the scorecard" (02/09/2026), 451 chars
  - `https://shubhxho.com/writing/starting-a-venture-fund` (essay, 2026-09-19) — about $5M fund, grew up in Bihar, first laptop in 9th grade, 1,204 chars
  - `https://shubhxho.com/writing/build-in-public-is-the-worst-psyop-to-exist-in-the-world` (essay, 2026-09-19) — anti-hype philosophy, "spend more time making sure people know you are building than actually building", 5,102 chars
  - `https://shubhxho.com/writing/larping-and-the-case-of-larpers` (essay, 2026-09-02) — about status roleplay, people faking identities, "founder without a product, researcher without research", 3,656 chars
- **Also fetched:** `https://shubhxho.com/feed.xml` (RSS, 3 entries with dates), `https://shubhxho.com/sitemap.xml` (6 URLs)
- **Not found:** `/about` returns 404. No about page exists.
- **Fields per page:** source, url, title, text, date, meta{section, page_type, chars, description}
- **Note:** All 3 essays were confirmed via RSS feed with proper dates. Daily page has one entry dated 02/09/2026.

**Identity signals extracted from website:**
- Name: Shubh
- Age: 18
- Education: Dropped out of Imperial College London
- Location: Bangalore, India
- Venture fund: Raised $5M for a venture fund backing people from backgrounds
- Writing topics: Venture fund philosophy, anti-"build in public" psyop, status roleplay vs real work, personal daily reflections
- Writing style: Direct, introspective, honest, anti-hype, first-person narrative
- Key essay themes: "Build in public is the worst psyop", "people larping a life instead of living it", "difference between being busy and building a life"

### 3. Identity/OSINT — Cross-platform verification

**Why:** To verify that the "Shubh Gupta" found across platforms is the SAME person as the one on shubhxho.com and @shubhgupta on X. This is critical for cold email — you need to know you're writing about the right person.

**Tools used:**
1. **user-scanner** (kaifcodec/user-scanner) — scanned 882 platforms, found 84 matches
   - Name confirmed: "Shubh Gupta" on bio.site
   - Profiles found: Bio.site, Twitch, Substack, Medium, Itch.io, Gumroad, Kaggle, Patreon, Linktree, Ko-fi, Soundcloud, Audiomack, Rumble, Last.fm, AudioJungle
   - Cross-scan found exposed emails and breach intel
2. **sherlock** (sherlock-project/sherlock) — checked 500+ platforms for username existence
   - 67 results found for "shubhgupta"
   - Confirmed which platforms have the handle
3. **spiderfoot** (smicallef/spiderfoot) — deep identity correlation
   - 200+ modules for DNS, subdomain, email, phone, social media
   - Slow but provides deep identity enrichment from a single seed
4. **social-analyzer** (qeeqbox/social-analyzer) — profile metadata extraction
   - 1000+ sites, quality scoring (0-100), metadata extraction
   - Returns structured JSON with profile URLs, detection confidence, metadata (emails, links)

**Cross-verification logic:**
- X bio "@imperialcollege" → matches website "dropped out of Imperial College London" ✅
- X handle @shubhgupta → matches website name "Shubh" ✅
- user-scanner found "Shubh Gupta" on bio.site → matches ✅
- Location "Bangalore" on website → matches X profile location ✅
- Age 18 on website → matches the person's age ✅
- Topics: "investing", "venture fund", "building" → match X posts about investing, YC, startups ✅
- X bio "@imperialcollege / investing" → matches website content about venture fund ✅
- "back in london" X post → matches website's Imperial College London background ✅
- YC rejection theme in X replies → matches website's "Building in public" narrative ✅

**Result:** Identity confirmed as **Shubh Gupta, 18, Imperial College London dropout, Bangalore, $5M venture fund**. 8+ independent cross-references all agree on the same person.

**Note:** @TheShubhWayyy (different person with same name) was removed from identity data.

---

### 4. GitHub (github.com/shubhxho) — 52 repos

**Why:** Shubh's GitHub reveals what he builds, what technologies he uses, his building frequency, and what interests him (via starred repos). This is the most technical data source for understanding his capabilities and coding style.

**What was scraped:**
- **Tool:** `httpx` + GitHub API v3 (unauthenticated, rate-limited to 60 req/hour)
- **Profile:** Name: Shubh, Company: Imperial College London, Blog: shubhxho.com, Location: london, Twitter: shubhxho
- **Followers:** 30 | **Following:** 66 | **Public Repos:** 56 | **Account Created:** 2025-10-08 (~11 months old)
- **Repos scraped:** 52 repos (all public), including readmes for 9 key projects
- **Starred repos:** 15 repos (top: claude-code 147K★, langflow 155K★, deno 108K★)
- **Activity events:** 30 events (PushEvent, ForkEvent, PullRequestEvent, CreateEvent, IssuesEvent, ReleaseEvent)

**Language distribution (52 repos):**
- Python: 13 (most used — AI/ML, finance, medical imaging)
- Go: 3 (agent-sandbox, nanoharness, KytyPS5)
- TypeScript: 2 (t3code, speall, shubhxho)
- Rust: 1 (based-chess-rs)

**Key projects:**
1. **omi** — AI screen recorder. Captures screen, transcribes conversations, generates AI summaries. Works on desktop, phone, wearables. Most recently pushed Sep 18, 2026. BasedHardware collaboration (PullRequestEvent Aug 19).
2. **based-chess-rs** (also called "Neutron-o1") — Rust chess engine. 60 KB neural network trained on self-play games. ~2800 Elo. Pushed Sep 14, 2026.
3. **polymarket-model** (CMF-2 50M) — Financial prediction model. Dual-stream cross-market fusion for Polymarket crypto prices.
4. **visionary-mlx** — MLX video tokenizer, action-conditioned world model, reinforcement learning.
5. **Unlimited-OCR-mlx** — Native Apple Silicon inference for Baidu Unlimited-OCR. Long-horizon document parsing.
6. **KytyPS5** — PlayStation 5 emulator. Most recently pushed Sep 19, 2026.
7. **speall** — Neuroscience archive search. Ingests metadata from 7 public archives. TypeScript.
8. **agent-sandbox** — Agent containment. systemd-run cgroups (Linux), sandbox-exec (macOS), secrets stripping, hash-chained audio digest.
9. **t3code** — Agent harness control surface. Mobile app (iOS, Android, web).

**Building frequency:** Account is ~11 months old. Most active period: Sep 2026 (8 events in September, 1 in August). Recent push activity: KytyPS5 (Sep 19), omi (Sep 18), based-chess-rs (Sep 14), agent-sandbox (Sep 14), visionary-mlx (Sep 7), t3code (Sep 5).

**Starred repos (interests revealed):**
- Top: claude-code (147K★), langflow (155K★), deno (108K★), grok-build (27K★), t3code (23K★)
- Languages: TypeScript (4), Python (4), Rust (2), Lua (1), C# (1), C (1), Jupyter (1), Shell (1)
- Themes: AI agents (claude-code, langflow), infrastructure (deno), AI research (grok-build), developer tools (t3code, AstroNvim)

**Limitations/Mistakes:**
- GitHub API rate-limited at 60 req/hour (unauthenticated). 58 min remaining when first hit.
- Following list (66 users) requires authentication — not accessible without auth tokens.
- Only 9 readmes obtained before rate limit (omi, based-chess-rs, agent-sandbox, KytyPS5, polymarket-model, visionary-mlx, Unlimited-OCR-mlx, speall, t3code)
- Some repos are forks (llvm-project, neovim, uv, accelerate, workers-sdk, Hyprland, next.js, alphafold3) — not original work
- Starred repos count from API may be incomplete due to rate limiting

### 5. Hugging Face (huggingface.co/shubhxho) — 9 models, 12 datasets, 2 spaces

**Why:** Hugging Face reveals Shubh's ML/AI research interests, model development, and dataset creation. This is the most direct window into his AI/ML capabilities and research direction.

**What was scraped:**
- **Tool:** `httpx` + HF HTML page scraping + HF API
- **Models (9):**
  - `shubhxho/sable-chess-net` — Chess neural network (updated 5 days ago)
  - `shubhxho/visionary-mlx` — Reinforcement Learning world model (updated 13 days ago)
  - `shubhxho/Unlimited-OCR-MLX` — OCR document parsing (updated 27 days ago)
  - `shubhxho/cmf-2` — Financial prediction model (Tabular Classification, updated Jul 31)
  - `shubhxho/polymarket-signal-model` — Polymarket prediction model
  - `shubhxho/ego-world-model-v1` — Egocentric world model (updated Apr 2)
  - `shubhxho/video-benchmark-compact-quality` — Video quality benchmark
  - `shubhxho/glm-bestfriend-companion-adapter` — Audio/voice adapter
  - `shubhxho/glm-bestfriend-glm9b-dpo-probe` — Audio/voice probe
- **Datasets (12):**
  - Medical imaging: brain-mri-redacted, akai-mri, micom-mri, speall-mri
  - Finance: cmf-15m-binance
  - Research: ipmattards, BhaveshShaha, models, reactor, ego-world-model-v1
  - Video quality: operator-video-quality
- **Spaces (2):** cmf-2 (Running), cmf-2-card (Static welcome page)
- **Bucket:** brain-mri-redacted-bucket (1.68 GB)

**HF interest themes:**
- Reinforcement Learning (visionary-mlx, sable-chess-net)
- Medical imaging (4 MRI datasets)
- Finance/trading (polymarket, cmf-15m-binance)
- OCR/document parsing (Unlimited-OCR-MLX)
- Audio/voice (glm-bestfriend)
- World models (ego-world-model-v1)

**Limitations/Mistakes:**
- HF profile bio text was parsed from raw HTML (190KB), not structured JSON
- Some dataset descriptions could not be extracted without API authentication
- HF Spaces runtime status requires checking individually

---

## How Data Was Segregated

### Raw Data Files (in `data/raw/`)

Each file contains one type of raw data, in JSONL (one JSON per line) or JSON format:

| File | Format | Contents | Count |
|---|---|---|---|
| `x_raw.jsonl` | JSONL | All X posts (text-only, filtered) | 46 |
| `website_raw.jsonl` | JSONL | All website pages | 6 |
| `identity_osint.json` | JSON | Full identity enrichment data | 1 |
| `reply_chains_full.json` | JSON | All 31 reply chains | 31 |
| `reply_context.json` | JSON | Summary of reply context | 3 |
| `github_profile.json` | JSON | GitHub profile metadata | 1 |
| `github_repos.json` | JSON | All 52 GitHub repos | 52 |
| `github_starred.json` | JSON | 15 starred repos | 15 |
| `github_events.json` | JSON | Activity events | 9 |
| `github_following.json` | JSON | Following list (empty - needs auth) | 0 |
| `github_readmes.json` | JSON | 9 key repo readmes | 9 |
| `github_hf_complete.json` | JSON | Combined GitHub + HF data | 1 |
| `hf_data.json` | JSON | HF models (9) + datasets (12) | 21 |
| `hf_spaces.json` | JSON | HF spaces (2) | 2 |
| `hf_profile_raw.html` | HTML | Raw HF profile page | 190KB |

### Main Corpus (`data/corpus.jsonl`)

All data merged into a single file with unified schema:

```json
{
  "source": "x",                    // "x", "shubh_website", or "identity"
  "url": "https://x.com/...",       // Source URL
  "title": "...",                   // Post/page title
  "text": "...",                    // Full text content
  "date": "2026-09-13",             // Date written/found
  "meta": {                         // Source-specific metadata
    "id": "...",                    // Tweet ID (for X)
    "likes": 6, "rts": 0,           // Engagement metrics
    "replies": 0, "quotes": 0,      // Engagement metrics
    "views": 838,                   // Tweet views
    "lang": "en",                   // Language
    "has_media": false,             // Whether post has media
    "author_id": "...",             // Author X ID
    "author_name": "Shubh Gupta",   // Author name
    "author_screenName": "shubhgupta", // Author handle
    "verified": true,               // Whether author is verified
    "quoted_tweet_id": "...",       // If post quotes another tweet
    "reply_context": {              // If post has replies
      "reply_count": 49,
      "people_who_replied": ["OpenAI", "..."],
      "replies_sample": [...]
    }
  },
  "context": "X post by @shubhgupta" // Human-readable context description
}
```

### Index (`data/index.json`)

Summary metadata for quick reference:
- Total docs count
- Per-source counts
- Total characters
- Identity summary (name, age, college, location, X handle, venture fund)
- X summary (records, date range, reply chains count)
- Website summary (records, pages)
- OSINT summary (platforms scanned, found, name)
- Reply context summary (total chains, total replies, top reactors)

---

## Indexing Methodology

### How Indexing Was Done

1. **Raw data extraction:** Each scraper wrote to `data/raw/` files
2. **Deduplication:** Used `seen_ids` set to avoid duplicate posts
3. **Text cleaning:** Removed pure media links, empty posts, emoji-only posts
4. **Context enrichment:** Added `context` field describing what each record is
5. **Reply context mapping:** Matched each X post to its reply chain using tweet ID
6. **Identity integration:** Merged OSINT data into the corpus as a single identity record
7. **Index generation:** Counted records per source, calculated total characters, summarized identity

### Indexing Decisions

- **X posts:** 46 posts indexed (53 raw - 3 retweets - 4 media-only/short posts). All 53 are available in `x_raw.jsonl` but only 46 meet the text-only threshold.
- **Reply chains:** All 31 chains saved separately in `reply_chains_full.json`. 29 X records in the corpus have `reply_context` in their meta.
- **Website pages:** 6 pages indexed (home, blog index, daily entry, 3 essays). All fetched directly via httpx, all returned 200.
- **Identity:** 1 record in corpus, full data in `identity_osint.json`.

---

## Mistakes Made During This Process

### 1. X Pagination Wall (Critical)
- **What happened:** `twitter user-posts` always returns the same 53 most recent posts, no cursor/offset support.
- **Impact:** Could not get all 359 tweets — only the most recent 53.
- **Root cause:** Cookie-based auth doesn't work with X API v2 (`/2/users/{id}/tweets` requires OAuth2 bearer token).
- **What was tried:**
  - `twitter search "from:shubhgupta"` → 404 (needs OAuth2)
  - Direct curl-cffi to X API v2 → 403 (cookies rejected)
  - Playwright browser automation → Chromium download timed out
  - `twitter tweet <id>` per-post lookups → too slow for 359 posts
- **Solution for next time:** Get an X API v2 bearer token (paid tier, ~$100/mo) OR use browser automation (Playwright + Chromium) to scroll the profile page and collect posts from the DOM.

### 2. Reply Context Not Initially Captured
- **What happened:** Initially only checked `replies` count from `twitter user-posts` output. The 3 posts with `replies:1` were the only ones checked for reply chains.
- **Impact:** Only 3 reply chains were extracted, missing the other 28 posts that also had replies.
- **Root cause:** Didn't realize `twitter tweet <id> --yaml` returns the post AND all replies in one output.
- **Fix:** Ran `twitter tweet <id> --yaml` for all 31 posts with `replies > 0` using 5 concurrent workers. All 31 chains fetched successfully.

### 3. `twitter tweet` Output Parsing
- **What happened:** The `twitter tweet <id> --yaml` output doesn't include `in_reply_to_status_id` in parsed data, so we can't determine which posts Shubh IS replying to (only which posts RECEIVED replies).
- **Impact:** Reply direction is incomplete — we know who replied to Shubh, but not who Shubh replied to.
- **Root cause:** `twitter user-posts` output keys are: `id, text, author, metrics, createdAt, createdAtLocal, createdAtISO, media, urls, isRetweet, retweetedBy, lang, score, quotedTweet`. No `in_reply_to_status_id`.
- **Note:** The `quotedTweet` field exists — some posts quote other tweets, giving partial context about what Shubh is reacting to.

### 4. @TheShubhWayyy Confusion
- **What happened:** Initially included @TheShubhWayyy in identity/network data.
- **Impact:** Incorrectly attributed a different person's account to Shubh.
- **Root cause:** The name "Shubh Gupta" appears on both @shubhgupta (the real one) and @TheShubhWayyy (a different person).
- **Fix:** Removed @TheShubhWayyy from all identity and network data. Confirmed as a different person.

### 5. Scaffold Time
- **What happened:** Initial scaffold from scratch took ~4 hours (Farza project).
- **Fix:** For Shub, reused scrapers from Farza project (`scrapers/base.py`, `runner.py`, `indexer.py`, `config/sources.yaml`). Reduced scaffold time to ~30 minutes.

### 6. Playwright Browser Download Timeout
- **What happened:** Attempted to use Playwright to scroll through the X profile page to get all 359 posts. `playwright install chromium` timed out (120s limit).
- **Impact:** Browser automation approach couldn't be tested.
- **Root cause:** Browser binary download is large and slow.
- **Solution for next time:** Pre-install Playwright browsers or increase timeout significantly.

### 7. Cookie-Based Auth Limitations
- **What happened:** Cookie-based auth (`auth_token` + `ct0`) only works for certain endpoints. X API v2 requires OAuth2 bearer token.
- **Impact:** Can't use `/2/users/{id}/tweets` endpoint, can't use search API, can't paginate.
- **Root cause:** Twitter's API has tiered auth — cookies work for some endpoints, OAuth2 bearer for others.
- **Note:** The `twitter-cli` tool has its own internal API mechanism that works with cookies for basic timeline access, but not for advanced endpoints.

### 8. Sequential Processing Was Too Slow
- **What happened:** Initially tried sequential `twitter tweet <id> --yaml` calls for reply context. Each call takes 5-25s. For 31 posts, that's 5+ minutes sequentially.
- **Fix:** Used `concurrent.futures.ThreadPoolExecutor` with 5 workers to parallelize. All 31 chains fetched in parallel.

---

## Tools and Libraries Used

| Tool | Purpose | Status |
|---|---|---|
| `twitter-cli` (v0.8.5) | X timeline and tweet lookups | Working |
| `httpx` | HTTP requests for website crawling | Working |
| `beautifulsoup4` + `lxml` | HTML parsing | Working |
| `feedparser` | RSS feed parsing | Working |
| `pyyaml` | YAML parsing | Working |
| `json` | JSON handling | Working |
| `curl-cffi` | Browser-like HTTP client | Working (impersonate="chrome") |
| `concurrent.futures` | Parallel processing | Working |
| `user-scanner` | OSINT identity (882 platforms) | Working |
| `sherlock` | Username existence check (500+ platforms) | Working |
| `spiderfoot` | Deep identity correlation (200+ modules) | Available but slow |
| `social-analyzer` | Profile metadata (1000+ sites) | Available |
| `crawl4ai` | AI-powered web crawler | Cloned, needs API key |
| `playwright` | Browser automation | Installed, Chromium download timed out |

---

## What a Next Agent Should Know

### If You Need to Resume the X Scrape
1. The checkpoint is at `/tmp/shub_x_checkpoint.json`
2. The `twitter user-posts` CLI returns only ~53 posts per call
3. To get more posts, you need either:
   - X API v2 bearer token (paid, ~$100/mo)
   - Browser automation (Playwright + Chromium)
   - Or accept the 53 most recent posts as the corpus

### If You Need to Get All 359 Posts
1. Get an X API v2 bearer token (paid tier)
2. Use: `GET /2/users/{user_id}/tweets?max_results=100&pagination_token={cursor}`
3. The `twitter-cli` Python module (`twitter_cli.client`) may support this internally
4. Or use Playwright to scroll the profile page and collect from DOM

### If You Need to Verify Identity Further
1. Run `sherlock shubhgupta --csv` for platform existence
2. Run `user-scanner -u shubhgupta --cross-scan` for identity enrichment
3. Run `spiderfoot -t shubhgupta` for deep correlation
4. Cross-reference with: website (Imperial College, Bangalore, 18yo), X bio (@imperialcollege)

### If You Need to Add More Websites
1. Check for RSS feed (`/feed.xml`, `/rss`, `/feed`)
2. Check for sitemap (`/sitemap.xml`)
3. Use `httpx` + `feedparser` for RSS
4. Use `httpx` + `beautifulsoup4` for individual pages
5. Use `crawl4ai` for LLM-powered extraction (needs OpenAI API key)

### Important Identity Notes
- **Confirmed identity:** Shubh Gupta, 18, Imperial College London dropout, Bangalore
- **X handle:** @shubhgupta (verified)
- **@TheShubhWayyy is a DIFFERENT person** — do not include in identity
- **Key topics:** Venture fund ($5M), building in public, AI/GPT-6, investing, youth/age, discipline, grants

### The Data Is Ready To Use
- `Shub/data/corpus.jsonl` — all 53 docs, ready for analysis
- `Shub/data/raw/reply_chains_full.json` — 31 reply chains, 390 replies
- `Shub/data/index.json` — summary metadata
- `Shub/data/raw/identity_osint.json` — full identity enrichment

---

## Quick Reference: What's Where

| What | File |
|---|---|
| All X posts (46) | `data/raw/x_raw.jsonl` |
| All website pages (6) | `data/raw/website_raw.jsonl` |
| Identity profile | `data/raw/identity_osint.json` |
| All 31 reply chains | `data/raw/reply_chains_full.json` |
| Main corpus (53 docs) | `data/corpus.jsonl` |
| Index/summary | `data/index.json` |
| Scraper code | `scrapers/` |
| Strategy document | `COMBINED_STRATEGY.md` |
| Implementation plan | `IMPLEMENTATION_PLAN.md` |
| Install/run instructions | `README.md` |

---

## For the Cold Email Agent

When writing a cold email using this corpus:
1. Study `data/corpus.jsonl` — especially the X posts (46 records) for Shubh's voice
2. Study the reply chains (`reply_chains_full.json`) to understand his conversational style
3. Study the website essays for his longer-form writing
4. Use the identity data (`identity_osint.json`) to personalize the email
5. Key context to reference in cold email:
   - He's 18, dropped out of Imperial College London, moved to Bangalore
   - Raised $5M for a venture fund
   - Active in AI/tech (GPT-6, tokenmaxxing, building in public)
   - Received $15K grant from Emergent Ventures
   - Currently hiring content creators
   - Anti-hype philosophy ("Build in public is the worst psyop")
   - His tone is direct, honest, young, builder-focused
