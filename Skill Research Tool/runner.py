"""CLI: python3 runner.py --source all|farza_com|substack|heyclicky|gdoc|buildspace_letter|youtube|x|instagram --limit N"""
import argparse
from pathlib import Path
from scrapers.base import save_jsonl
from scrapers import farza_com, substack, heyclicky, gdoc, youtube, x_scrape, instagram, buildspace_letter

SOURCES = {
    "farza_com": lambda lim: farza_com.scrape(),
    "substack": lambda lim: substack.scrape(limit=lim),
    "heyclicky": lambda lim: heyclicky.scrape(),
    "gdoc": lambda lim: gdoc.scrape(),
    "buildspace_letter": lambda lim: buildspace_letter.scrape(),
    "youtube": lambda lim: youtube.scrape(limit=min(lim, 100)),
    "x": lambda lim: x_scrape.scrape(limit=lim),
    "instagram": lambda lim: instagram.scrape(),
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="all")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--out", default="data/raw")
    args = ap.parse_args()
    names = list(SOURCES) if args.source == "all" else [args.source]
    for n in names:
        print(f"== {n} ==")
        try:
            rows = SOURCES[n](args.limit)
        except Exception as e:
            print(f"{n} FAILED: {e}")
            rows = []
        save_jsonl(Path(args.out) / f"{n}.jsonl", rows)

if __name__ == "__main__":
    main()
