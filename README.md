# Writing

A research + writing workbench. It contains a voice/style writing skill and a
scraper pipeline that builds a first-party writing corpus, then analyzes it into
a psychological model for outreach writing.

## Repository layout

```
Writing/
├── README.md                  # this file — repo overview + folder map
├── .gitignore                 # os junk, python caches, cloned deps
├── Empty Draft Folder/        # placeholder for drafts (empty)
└── Skill Research Tool/       # the actual project (scraper + analysis + writing skill)
```

### `Empty Draft Folder/`
An intentionally empty scratch folder reserved for draft writing output.
Tracked via a `.gitkeep` so the folder itself is preserved in the repo.

### `Skill Research Tool/`
The core project. A reusable, source-pluggable "scrape → index → analyze →
write" pipeline. Originally built for the Farza corpus (produced the writing
skill), then re-run against the Shubh corpus for cold-email voice matching.
See `Skill Research Tool/README.md` for install/run instructions and
`Skill Research Tool/SKILL.md` for the writing-style skill rules.

Inside `Skill Research Tool/`:

| Path | What it is |
| --- | --- |
| `runner.py` | CLI entry point. Runs one scraper source at a time (`--source ...`), or `all`. Reads `config/sources.yaml`. |
| `indexer.py` | Normalizes `data/raw/*.jsonl` into `data/corpus.jsonl` + `data/index.json`. |
| `config/sources.yaml` | Source definitions for the Farza corpus (site, Substack, X, GDoc, YouTube, Instagram, ...). |
| `scrapers/` | One module per source: `farza_com`, `substack`, `heyclicky`, `gdoc`, `buildspace_letter`, `youtube`, `instagram`, `x_scrape`, `x_twitter_cli`, plus `base.py` (shared HTTP/crawl logic). |
| `data/` | Scraper output. `raw/<source>.jsonl` per source, plus `corpus.jsonl` and `index.json`. 697 docs total. |
| `requirements.txt` | Python deps (httpx, beautifulsoup4, lxml, feedparser, pyyaml, yt-dlp). |
| `SKILL.md` | The writing skill: a direct, casual builder voice spec (short sentences, one idea per line, no hype). |
| `AGENTS.md` | Notes on the cloned dependency (Agent-Reach) used for X scraping. |
| `shubhgupta.csv` | OSINT username-enumeration output (platform existence + HTTP status) for the Shubh corpus run. |
| `.gitignore` / `.ignore` | Cloned-deps ignore + allowlist (managed by the `clonedeps` tool). |
| `.slim/` | Local workspace. `clonedeps.json` (dependency manifest) is tracked; `clonedeps/repos/` (third-party source) is ignored. `deepwork/` holds deepwork planning docs. |
| `skill/Shub/` | Skill-side scaffolding for the Shub run (analysis data + scripts). |
| `Shub/` | The Shubh corpus project — see below. |

Inside `Skill Research Tool/Shub/`:

| Path | What it is |
| --- | --- |
| `COMBINED_STRATEGY.md` | Person profile + tool evaluation (crawl4ai, user-scanner, twitter-cli, ...) and the execution strategy. |
| `IMPLEMENTATION_PLAN.md` | Step-by-step pipeline plan + real lessons learned from the Farza run (X scraping blocker chain, etc.). |
| `CORPUS_ARTIFACT.md` | Complete artifact + methodology guide: why the corpus exists, structure, X API auth limits, next-time fixes. |
| `dataanalysisstrategy.md` | The analysis framework: multi-source inventory → triangulation → psychological model → utilization. |
| `config/sources.yaml` | Source definitions (inherited from the Farza config). |
| `data/` | Shub corpus: `corpus.jsonl` (53 docs), `index.json`, and `raw/` (X, website, GitHub, Hugging Face, identity OSINT, reply chains). |
| `scrapers/` | Scraper modules for the Shub run (same shape as the top-level `scrapers/`). |
| `analysis/` | The analysis output — see below. |

Inside `Skill Research Tool/Shub/analysis/`:

| Path | What it is |
| --- | --- |
| `03_psychological_model.md` | Written psychological model of the subject, every claim backed by triangulated source evidence. |
| `data/inventory.jsonl` | Machine-readable evidence inventory (bucketed, with URL/date/quote). |
| `scripts/` | `extract_inventory.py`, `validate_inventory.py`, `create_summaries.py` — the analysis pipeline scripts. |
| `summaries/` | Per-bucket summaries + raw items: `bucket_A..E` (`.jsonl` + `_summary.txt`) across website, X, GitHub, Hugging Face, and identity sources. |

## Data format

Every record in a `corpus.jsonl` / `raw/*.jsonl` file is one JSON object per
line:

```json
{"source": "...", "url": "...", "title": "...", "text": "...", "date": "...", "meta": {}}
```

## Notes & limits

- X/Twitter and Instagram are login/rate-limit walled; these scrapers are best-effort.
- No transcripts are collected — written voice only.
- Personal / OSINT material about the corpus subject is included in this repo.
