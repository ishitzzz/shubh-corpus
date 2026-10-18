# Farza corpus scraper (HeyClicky-era voice)

Public first-party writing only. No transcripts, no third-party summaries.

## Install
```
pip install -r requirements.txt
# Optional (user-suggested libs, for v2 advanced crawling):
# pip install scrapling crawlee snscrape
# git clone https://github.com/D4Vinci/Scrapling.git
# git clone https://github.com/apify/crawlee.git
# git clone https://github.com/Panniantong/Agent-Reach.git
```

## Run (respectful delays built in)
```
python3 runner.py --source farza_com
python3 runner.py --source substack --limit 200
python3 runner.py --source heyclicky
python3 runner.py --source gdoc
python3 runner.py --source buildspace_letter
python3 runner.py --source youtube --limit 100
python3 runner.py --source x --limit 1000   # best-effort; often blocked
python3 runner.py --source all --limit 200  # everything
python3 indexer.py  # -> data/corpus.jsonl + data/index.json
```

## Output format
`data/raw/<source>.jsonl` + `data/corpus.jsonl`, one JSON per line:
`{source, url, title, text, date, meta}`

## Notes / limits
- X/Twitter is login + rate-limit walled. If snscrape fails, paste top posts into `data/x_manual.jsonl` or use X API v2 `from:FarzaTV -filter:replies`.
- Instagram is login-walled; manual paste into `data/ig_manual.jsonl`.
- GDoc needs "Anyone with link can view" else export 403s — instructions logged.
- Start set (best coverage): farza.com + full Substack archive + last 500-1000 original X posts + Buildspace letter + vision GDoc.
