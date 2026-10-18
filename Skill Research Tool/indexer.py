"""Index data/raw/*.jsonl -> data/corpus.jsonl + data/index.json (dedupe + light clean)."""
import json
from pathlib import Path
from collections import Counter

RAW = Path("data/raw")
OUT_CORPUS = Path("data/corpus.jsonl")
OUT_INDEX = Path("data/index.json")

def clean(text: str) -> str:
    lines = []
    for ln in (text or "").split("\n"):
        ln = ln.strip()
        if not ln:
            continue
        if ln.startswith(("http://", "https://")) and len(ln.split()) <= 2:
            continue
        lines.append(ln)
    return "\n".join(lines)

def main():
    seen, rows = set(), []
    per_source = Counter()
    for fp in sorted(RAW.glob("*.jsonl")):
        for line in fp.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            url = r.get("url", "")
            if not url or url in seen:
                continue
            seen.add(url)
            r["text"] = clean(r.get("text", ""))
            if len(r["text"]) < 20 and not r.get("title"):
                continue  # drop empty stubs
            rows.append(r)
            per_source[r.get("source", fp.stem)] += 1
    OUT_CORPUS.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CORPUS, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    index = {"total": len(rows), "per_source": dict(per_source),
             "chars": sum(len(r.get("text", "")) for r in rows)}
    OUT_INDEX.write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(json.dumps(index, indent=2))

if __name__ == "__main__":
    main()
