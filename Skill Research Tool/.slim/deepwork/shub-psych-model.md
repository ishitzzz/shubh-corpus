# Shub Psychological Model & Utilization Map — Deepwork Plan

## Goal & Understanding
Perform a multi-source data inventory, triangulation, psychological model construction, and utilization mapping for Shubh Gupta's corpus (X/Twitter, website/blog/daily notes, GitHub, Hugging Face) to produce:
1. A detailed psychological model (fixed 7 fields) where every element is backed by triangulated evidence (≥2 sources, no strong contradiction).
2. A utilization map that translates the model into precise decisions for a highly relatable cold email **TO Shubh Gupta** (i.e., outreach that sits inside his frame, feels recognizably "of the same vibe").
Framework: Follow `Shub/dataanalysisstrategy.md` exactly (Inventory → Triangulation → Model → Utilization).
Output feeds a later cold-email-writing task (not part of this plan).

## Working Assumptions (state them briefly)
- The corpus reflects Shubh's voice as of Sept 2026 (website scraped 2026-09-20, X up to 2026-09-13).
- GitHub handle `shubhxho` and X handle `@shubhgupta` refer to the same person (bio links & timeline consistency to be checked in Phase 1).
- "Writer" in the utilization framework = the client commissioning this analysis; their project/persona details will be provided before Phase 3 starts (or we proceed with a placeholder and flag the gap).
- Analysis location: `Shub/analysis/` (new directory). Machine-readable outputs: `inventory.jsonl`, `triangulation.jsonl`, `psych_model.json`, `utilization_map.jsonl`.
- Deepwork rigor: mechanical work (extraction, validation scripts) → @fixer; judgment work (categorization, triangulation, model writing) → @oracle; each phase gated by an independent @oracle review (fresh session).

## Data Sources (fresh inventory & known issues)
Corpus: `Shub/data/corpus.jsonl` (53 records: 46 X, 6 website, 1 identity — note: website text in corpus is STALE, see DQ4)
Raw:
- `Shub/data/raw/website_raw.jsonl` (6 pages, CURRENT text scraped 2026-09-20)
- `Shub/data/raw/x_raw.jsonl` (22 lines — likely STALE/partial; corpus X count 46 suggests an earlier run)
- `Shub/data/raw/reply_chains_full.json` (31 chains, 390 replies — CURRENT)
- `Shub/data/raw/reply_context.json` (STALE 3 chains — do NOT use)
- `Shub/data/raw/identity_osint.json`
- `Shub/data/raw/github_hf_complete.json` (consolidated: 52 repos, 15 starred, 9 readmes, 9 HF models, 12 HF datasets, 2 HF spaces, events, stats)
- `Shub/data/raw/github_profile.json`, `github_repos.json`, `github_starred.json`, `github_readmes.json`, `github_events.json`, `github_following.json`, `github_html_scrape.json` (note: `github_repos_detailed.json` is empty `[]`)
- `Shub/data/raw/hf_data.json`, `hf_datasets.json`, `hf_models.json`, `hf_spaces.json`, `hf_profile_raw.html`
- `shubhgupta.csv` (sherlock results: 67 platforms where `shubhgupta` exists)

Known Data Quality Issues (to resolve in Phase 1):
- **DQ1**: `x_raw.jsonl` (22 lines) ≠ corpus X count (46) — corpus likely built from an overwritten earlier raw file. Resolution: Prefer corpus for X records (it is the deduped, indexed output); treat `x_raw.jsonl` as supplemental/raw cache only.
- **DQ2**: `github_repos_detailed.json` empty `[]` — ignore; use `github_hf_complete.json` for repo details.
- **DQ3**: `Shub/data/index.json` internal inconsistencies:
  - `x_summary.records: 19` vs `per_source.x: 46` — trust `per_source`.
  - Website essay dates truncated (`"Sat, 19 Se"`).
- **DQ4**: Website text version drift — corpus holds Sep-19 text ("interning at an HFT firm", no Bihar mention); `website_raw.jsonl` holds Sep-20 text ("Hudson River Trading", "exited robotics co for six figures", "Born and raised in rural Bihar"). Resolution: **USE `website_raw.jsonl` as the single source of truth for website content**; corpus website records are stale and should be superseded.
- **DQ5**: `reply_context.json` stale (3 chains) — **USE `reply_chains_full.json`** (31 chains).
- **DQ6**: GitHub profile `twitter_username: "shubhxho"` vs X `@shubhgupta` — flag as a bio-link inconsistency to resolve in Phase 1 (cross-cutting metadata E).
- **DQ7**: X dates in corpus lack year (e.g., `"Sun Sep 13"`) vs ISO in `x_raw.jsonl` — normalize to full ISO timestamp for timeline consistency (E) using `x_raw.jsonl` or infer year from context.
- **DQ8**: Identity data fragmentation — pieces in `corpus.jsonl` (identity record), `identity_osint.json`, website bio, X bio — merge into a single source-of-truth identity profile.

## Phase Plan (3 phases, 3 gates)
### Phase 1 — Reconciliation & Evidence-Linked Inventory (Mechanical + Judgment)
**Goal**: Build a single-source-of-truth, deduplicated inventory where every data point is bucketed into A–E with raw evidence attached (URL, date, exact quote/repo description). Resolve all DQs above.
- **1.1** (@fixer): Write extraction/validation scripts:
  - `Shub/analysis/scripts/extract_inventory.py` — reads all sources, applies DQ resolutions (prefers `website_raw` for website text; corpus for X; `reply_chains_full` for replies; merges identity sources), buckets items, emits `Shub/analysis/data/inventory.jsonl`:
    ```jsonl
    {"bucket":"A|B|C|D|E", "source":"website|x|github|hf|meta", "url":"...", "date":"ISO8601", "exact_quote":"...", "item_id":"...", "notes":""}
    ```
  - `Shub/analysis/scripts/validate_inventory.py` — assertions: (a) covers all X ids in corpus; (b) all 6 website pages; (c) 31 reply chains; (d) github/hf stats match `github_hf_complete.json`; (e) every item has non-empty `url` and `exact_quote`; (f) no duplicate `item_id`.
- **1.2** (orchestrator): Run scripts, review output, fix edge cases, ensure counts match expectations (~53 corpus records + website updates + github/hf stats + identity merge).
- **Gate 1** (@oracle — fresh session): Review inventory completeness, DQ resolutions, and script correctness.  
  **Rationale**: Inventory quality gates all downstream work; independent check prevents garbage-in-garbage-out.  
  **Exit criteria**: Validator script passes; oracle signs off on bucketing decisions and evidence links.

### Phase 2 — Triangulation & Psychological Model Construction (Judgment)
**Goal**: Apply explicit pairing rules (per `dataanalysisstrategy.md`) to generate candidate traits, retain only those with ≥2-source support and no strong contradiction, weight higher when narrative (A) + behavior (C/D) + attitude (B) agree. Write the model in the 7 fixed fields.
- **2.1** (@oracle): 
  - Read `inventory.jsonl`.
  - For each source layer (A,B,C,D), generate candidate traits (explicit theses, opinions, capabilities, values, communication patterns).
  - For each trait, search the other three layers for confirming/refuting evidence (exact quotes, timestamps, repo descriptions).
  - Retain trait iff: (a) ≥2 distinct source layers support it; (b) no strong contradiction exists (e.g., A says "X", B/C/D show consistent opposite).
  - Weight trait higher when: narrative (A) is backed by behavioral evidence (C/D shipping) and real-time attitude (B).
  - Output `Shub/analysis/data/triangulation.jsonl`:
    ```jsonl
    {"trait_id":"...", "trait_text":"...", "supporting_sources":["A","C"], "evidence_quotes":[{"source":"A", "url":"...", "quote":"..."}, ...], "weight":"high|medium|low", "contradictions_log":["..."]}
    ```
  - Construct the psychological model in the 7 fixed fields (each field short, evidence-linked to trait IDs):
    - Primary Drivers
    - Core Identity Narrative
    - Capability Evidence Standard
    - Decision Filters for People & Projects
    - Language Magnets & Turn-offs
    - Emotional / Reciprocity Layer
    - Communication Preferences
  - Emit `Shub/analysis/data/psych_model.jsonl` (one record per field) + `Shub/analysis/03_psychological_model.md` (human-readable).
- **Gate 2** (@oracle — fresh session): Review triangulation rigor and model vs. data.  
  **Rationale**: Triangulation determines model validity; independent check prevents cherry-picking or over-indexing on single sources.  
  **Exit criteria**: 
  - Every retained trait cites ≥2 distinct source layers; every dropped trait appears in `contradictions_log`.
  - Model fields are non-vague, evidence-linked (trace to `triangulation.jsonl` trait IDs), and internally consistent.
  - Oracle signs off that no material trait was missed or wrongly retained.

### Phase 3 — Utilization Map Construction (Judgment)
**Goal**: Map the psychological model to utilization decisions for a cold email TO Shubh (relatable, in-his-frame), following Section 4 of `dataanalysisstrategy.md`. Every activated element must trace back to a triangulated trait or raw data point.
- **3.1** (@oracle): 
  - Read `psych_model.jsonl`.
  - Apply utilization mapping:
    - **Relatability engine**: Identify strongest structural parallel between Shubh's path (Core Identity Narrative + Reciprocity Layer + Capability Evidence Standard) and the **writer's path** (client-provided project/persona details — *see open question below*). Must be constraint → continued technical work → current missing resource (not superficial).
    - **Hook & frame**: Draw language/framing exclusively from Language Magnets appearing in multiple sources (weighted high).
    - **Substance**: Select only those details of the writer’s project that would pass Shubh’s Capability Evidence Standard (i.e., look at home alongside his repos/artifacts).
    - **Fit**: Map writer’s situation onto Decision Filters that survived triangulation (explicit/implicit criteria for whom he backs/respects).
    - **Voice**: Constrain every sentence to Communication Preferences (length, directness, concreteness, claim:evidence ratio) from essays + Twitter + technical writing style.
    - **Exclusion**: Remove anything triggering Turn-offs (performative language, identity without artifacts, generic ambition) regardless of cleverness.
  - Output `Shub/analysis/data/utilization_map.jsonl`:
    ```jsonl
    {"decision_type":"relatability|hook|substance|fit|voice|exclusion", "detail":"...", "source_trait_ids":[...], "source_raw_items":[...], "rationale":"..."}
    ```
    + `Shub/analysis/04_utilization_map.md` (human-readable).
- **Gate 3** (@oracle — fresh session): Review utilization traceability and framework compliance.  
  **Rationale**: Utilization must be strictly model-driven; independent check ensures no ad-hoc or unsubstantiated leaps.  
  **Exit criteria**: 
  - Every `detail` in utilization map has non-empty `source_trait_ids` (triangulated traits) OR `source_raw_items` (raw inventory items) with evidence links.
  - No Turn-off appears in activated decisions; every exclusion is justified.
  - Voice rules match observed Shubh usage (spot-check against inventory).

## Milestones & Success Criteria
- **M1 — Inventory Complete** (after Gate 1):
  - `Shub/analysis/data/inventory.jsonl` exists and passes `validate_inventory.py`.
  - Bucket counts roughly match: A≈6 (website), B≈46 (X), C≈52+ (github repos), D≈23 (hf models/datasets/spaces), E≈10-20 (bio links/timeline items).
  - All DQs resolved and documented in `Shub/analysis/00_dq_resolutions.md`.
- **M2 — Psychological Model Written** (after Gate 2):
  - `Shub/analysis/03_psychological_model.md` contains all 7 fields, each 1-3 sentences, with inline evidence links (e.g., `[see A:website_raw.jsonl#1, B:x_raw.jsonl#12]`).
  - `Shub/analysis/data/triangulation.jsonl` shows ≥2-source support for all retained traits; contradictions log is present.
- **M3 — Utilization Map Complete** (after Gate 3):
  - `Shub/analysis/04_utilization_map.md` contains all 5 utilization sections (relatability, hook, substance, fit, voice, exclusion).
  - `Shub/analysis/data/utilization_map.jsonl` passes traceability validation (every decision ties to model or raw data).
  - Package ready for cold-email-writing agent: model + utilization map.

## Risks & Mitigations
- **Risk**: X layer thin (only 53/359 posts accessible due to twitter-cli pagination wall).  
  **Mitigation**: Explicitly call this out in the model (Capability Evidence Standard may note "consistent shipping attitude despite limited public timeline"); weight other sources higher where possible.
- **Risk**: Writer’s path/project details unavailable for Relatability engine (Phase 3).  
  **Mitigation**: Proceed with a clearly marked placeholder in utilization map (e.g., `relatability: [PENDING WRITER'S PATH]`); flag as blocker for Gate 3; client must provide before utilization can be finalized.
- **Risk**: GitHub/X handle inconsistency (`shubhxho` vs `@shubhgupta`) undermines identity resolution.  
  **Mitigation**: Treat as a bio-link inconsistency to resolve in Phase 1 (check website, HF, sherlock for which handle is primary; weight timeline consistency and cross-verification).
- **Risk**: Website text version drift (corpus vs raw) causes confusion.  
  **Mitigation**: Explicitly decree `website_raw.jsonl` as SOT for website; note in DQ4 that corpus website records are stale and superseded.

## Open Questions (Client Input Needed)
1. **Writer’s path for Relatability engine**: To compute the strongest structural parallel (constraint → continued technical work → current missing resource) between Shubh and the writer, I need the client’s/project’s:
   - Origin/constraint story (e.g., limited early resources, lack of access)
   - Continued technical work (what they’ve built/shipped despite constraints)
   - Current missing resource (what they seek from Shubh’s fund — capital, mentorship, access?)
   *Without this, the relatability engine cannot run; Phase 3 utilization will be incomplete.*  
   Please provide this summary before or during Phase 3, or confirm we proceed with a placeholder and treat the utilization map as a template to fill in later.

2. **Output location preference**: Shall I place all analysis outputs under `Shub/analysis/` as assumed, or another location?

## Next Step (After This Plan)
If you approve this plan:
1. I will create the `Shub/analysis/` directory and scripts.
2. Dispatch Phase 1 (@fixer for extraction scripts, orchestrator for consolidation + validation runs).
3. Await Gate 1 (@oracle) completion before proceeding.

Do you want to proceed with Phase 1 now?