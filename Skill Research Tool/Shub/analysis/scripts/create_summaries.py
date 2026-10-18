#!/usr/bin/env python3
"""
Create summary files for each bucket to assist with Phase 2 triangulation analysis.
"""

import json
from collections import defaultdict
from pathlib import Path

def load_jsonl(filepath):
    """Load JSONL file"""
    with open(filepath, 'r') as f:
        return [json.loads(line.strip()) for line in f if line.strip()]

def main():
    inventory_path = Path("/Users/ishitjain/Desktop/writing skill/Shub/analysis/data/inventory.jsonl")
    output_dir = Path("/Users/ishitjain/Desktop/writing skill/Shub/analysis/summaries")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Loading inventory...")
    inventory = load_jsonl(inventory_path)
    
    # Group by bucket
    buckets = defaultdict(list)
    for item in inventory:
        buckets[item["bucket"]].append(item)
    
    # Create summary for each bucket
    for bucket_id, items in buckets.items():
        print(f"Processing bucket {bucket_id} ({len(items)} items)")
        
        # Create a readable summary file
        summary_file = output_dir / f"bucket_{bucket_id}_summary.txt"
        with open(summary_file, 'w') as f:
            f.write(f"BUCKET {bucket_id} SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            # Group by source for more detail
            sources = defaultdict(list)
            for item in items:
                sources[item.get("source", "unknown")].append(item)
            
            for source, source_items in sources.items():
                f.write(f"SOURCE: {source} ({len(source_items)} items)\n")
                f.write("-" * 30 + "\n")
                
                for i, item in enumerate(source_items[:20]):  # Limit to first 20 for readability
                    f.write(f"\n{i+1}. Item ID: {item.get('item_id', 'N/A')}\n")
                    f.write(f"   URL: {item.get('url', 'N/A')}\n")
                    f.write(f"   Date: {item.get('date', 'N/A')}\n")
                    f.write(f"   Exact Quote: {item.get('exact_quote', 'N/A')[:200]}...\n")
                    notes = item.get('notes', '')
                    if notes:
                        f.write(f"   Notes: {notes}\n")
                
                if len(source_items) > 20:
                    f.write(f"\n... and {len(source_items) - 20} more items\n")
                f.write("\n")
        
        # Also create a JSONL version for programmatic access
        jsonl_file = output_dir / f"bucket_{bucket_id}.jsonl"
        with open(jsonl_file, 'w') as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"Summaries written to {output_dir}")

if __name__ == "__main__":
    main()