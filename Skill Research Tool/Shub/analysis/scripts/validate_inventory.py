#!/usr/bin/env python3
"""
Validate the inventory.jsonl file.
Checks:
1. All required items are present
2. Each item has url and exact_quote
3. No duplicate item_ids
4. Bucket counts match expectations
"""

import json
from pathlib import Path

def load_jsonl(filepath):
    """Load JSONL file"""
    with open(filepath, 'r') as f:
        return [json.loads(line.strip()) for line in f if line.strip()]

def main():
    inventory_path = Path("/Users/ishitjain/Desktop/writing skill/Shub/analysis/data/inventory.jsonl")
    corpus_path = Path("/Users/ishitjain/Desktop/writing skill/Shub/data/corpus.jsonl")
    raw_website_path = Path("/Users/ishitjain/Desktop/writing skill/Shub/data/raw/website_raw.jsonl")
    raw_reply_chains_path = Path("/Users/ishitjain/Desktop/writing skill/Shub/data/raw/reply_chains_full.json")
    raw_github_hf_path = Path("/Users/ishitjain/Desktop/writing skill/Shub/data/raw/github_hf_complete.json")
    raw_identity_path = Path("/Users/ishitjain/Desktop/writing skill/Shub/data/raw/identity_osint.json")
    
    print("Loading inventory...")
    inventory = load_jsonl(inventory_path)
    
    print(f"Total inventory items: {len(inventory)}")
    
    # Check 1: No missing url or exact_quote
    missing_url = [item for item in inventory if not item.get("url")]
    missing_quote = [item for item in inventory if not item.get("exact_quote")]
    
    if missing_url:
        print(f"ERROR: {len(missing_url)} items missing url")
        for item in missing_url[:3]:
            print(f"  Item {item.get('item_id')}: missing url")
    else:
        print("OK: All items have url")
        
    if missing_quote:
        print(f"ERROR: {len(missing_quote)} items missing exact_quote")
        for item in missing_quote[:3]:
            print(f"  Item {item.get('item_id')}: missing exact_quote")
    else:
        print("OK: All items have exact_quote")
    
    # Check 2: No duplicate item_ids
    item_ids = [item.get("item_id") for item in inventory]
    duplicate_ids = [item_id for item_id in set(item_ids) if item_ids.count(item_id) > 1]
    
    if duplicate_ids:
        print(f"ERROR: Duplicate item_ids found: {duplicate_ids}")
    else:
        print("OK: No duplicate item_ids")
    
    # Check 3: Verify website count (should be 6 from website_raw.jsonl)
    website_items = [item for item in inventory if item.get("bucket") == "A" and item.get("source") == "website"]
    expected_website = 6
    if len(website_items) != expected_website:
        print(f"ERROR: Expected {expected_website} website items, got {len(website_items)}")
    else:
        print(f"OK: Website count correct ({len(website_items)} items)")
    
    # Check 4: Verify X count (should be 46 posts + 31 reply originals + 390 replies = 467)
    x_items = [item for item in inventory if item.get("bucket") == "B"]
    expected_x = 46 + 31 + 390  # posts + reply originals + replies
    if len(x_items) != expected_x:
        print(f"ERROR: Expected {expected_x} X items, got {len(x_items)}")
    else:
        print(f"OK: X count correct ({len(x_items)} items)")
        # Breakdown
        x_posts = [item for item in x_items if item.get("source") == "x"]
        x_reply_originals = [item for item in x_items if item.get("source") == "x_reply_context"]
        x_replies = [item for item in x_items if item.get("source") == "x_reply"]
        print(f"  - X posts: {len(x_posts)}")
        print(f"  - X reply originals: {len(x_reply_originals)}")
        print(f"  - X replies: {len(x_replies)}")
    
    # Check 5: Verify GitHub repos (should be 52)
    github_repos = [item for item in inventory if item.get("bucket") == "C" and item.get("source") == "github_repo"]
    expected_github_repos = 52
    if len(github_repos) != expected_github_repos:
        print(f"ERROR: Expected {expected_github_repos} GitHub repos, got {len(github_repos)}")
    else:
        print(f"OK: GitHub repos count correct ({len(github_repos)} items)")
    
    # Check 6: Verify HF items (should be 23: 9 models + 12 datasets + 2 spaces)
    hf_items = [item for item in inventory if item.get("bucket") == "D"]
    expected_hf = 9 + 12 + 2  # models + datasets + spaces
    if len(hf_items) != expected_hf:
        print(f"ERROR: Expected {expected_hf} HF items, got {len(hf_items)}")
    else:
        print(f"OK: HF count correct ({len(hf_items)} items)")
        hf_models = [item for item in hf_items if item.get("source") == "hf_model"]
        hf_datasets = [item for item in hf_items if item.get("source") == "hf_dataset"]
        hf_spaces = [item for item in hf_items if item.get("source") == "hf_space"]
        print(f"  - HF models: {len(hf_models)}")
        print(f"  - HF datasets: {len(hf_datasets)}")
        print(f"  - HF spaces: {len(hf_spaces)}")
    
    # Check 7: Verify identity/E items (should be around 6)
    e_items = [item for item in inventory if item.get("bucket") == "E"]
    print(f"INFO: Bucket E (cross-cutting metadata) has {len(e_items)} items")
    e_sources = {}
    for item in e_items:
        source = item.get("source", "unknown")
        e_sources[source] = e_sources.get(source, 0) + 1
    for source, count in sorted(e_sources.items()):
        print(f"  - {source}: {count}")
    
    print("\nValidation complete.")

if __name__ == "__main__":
    main()