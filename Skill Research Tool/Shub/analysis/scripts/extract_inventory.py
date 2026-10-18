#!/usr/bin/env python3
"""
Extract inventory from all Shubh Gupta data sources.
Resolves known data quality issues and buckets items into A-E layers.
Output: Shub/analysis/data/inventory.jsonl
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Base paths
BASE_DIR = Path("/Users/ishitjain/Desktop/writing skill/Shub")
DATA_RAW = BASE_DIR / "data/raw"
DATA_CORPUS = BASE_DIR / "data"
ANALYSIS_DATA = BASE_DIR / "analysis/data"

# Ensure output directory exists
ANALYSIS_DATA.mkdir(parents=True, exist_ok=True)

def load_jsonl(filepath):
    """Load JSONL file, return list of dicts"""
    if not filepath.exists():
        return []
    with open(filepath, 'r') as f:
        return [json.loads(line.strip()) for line in f if line.strip()]

def load_json(filepath):
    """Load JSON file"""
    if not filepath.exists():
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def iso_date(date_str):
    """Normalize date to ISO format if possible"""
    if not date_str or not isinstance(date_str, str):
        return ""
    # If already looks like ISO, return as-is
    if "T" in date_str and ("+" in date_str or date_str.endswith("Z")):
        return date_str
    # Try to parse common formats
    try:
        # Handle "Sun Sep 13" style (from corpus)
        if len(date_str.split()) == 3 and date_str.split()[0] in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
            # Assume current year 2026
            dt = datetime.strptime(f"2026 {date_str}", "%Y %a %b %d")
            return dt.isoformat()
        # Handle "2026-09-13T12:40:59+00:00" style
        if "-" in date_str and ":" in date_str:
            # Already somewhat ISO-like
            return date_str
    except:
        pass
    return date_str  # return as-is if we can't parse

def extract_website_inventory():
    """Extract from website_raw.jsonl (Bucket A: Website/Essays/Daily Notes)"""
    inventory = []
    data = load_jsonl(DATA_RAW / "website_raw.jsonl")
    for i, item in enumerate(data):
        # Use the CURRENT website text from website_raw.jsonl
        inventory.append({
            "bucket": "A",
            "source": "website",
            "url": item.get("url", ""),
            "date": iso_date(item.get("date", "")) or iso_date(item.get("date_found", "")),
            "exact_quote": item.get("text", "")[:500],  # truncate for manageability
            "item_id": f"website_{i}",
            "notes": f"section={item.get('meta',{}).get('section','')}, page_type={item.get('meta',{}).get('page_type','')}, chars={item.get('meta',{}).get('chars',0)}"
        })
    return inventory

def extract_x_inventory():
    """Extract from corpus.jsonl X records (Bucket B: Twitter/X)"""
    inventory = []
    corpus = load_jsonl(DATA_CORPUS / "corpus.jsonl")
    x_items = [item for item in corpus if item.get("source") == "x"]
    for i, item in enumerate(x_items):
        inventory.append({
            "bucket": "B",
            "source": "x",
            "url": item.get("url", ""),
            "date": iso_date(item.get("date", "")),
            "exact_quote": item.get("text", ""),
            "item_id": f"x_{item.get('id', i)}",
            "notes": f"likes={item.get('meta',{}).get('likes',0)}, rts={item.get('meta',{}).get('rts',0)}, replies={item.get('meta',{}).get('replies',0)}, views={item.get('meta',{}).get('views',0)}"
        })
    return inventory

def extract_reply_chains_inventory():
    """Extract from reply_chains_full.json (part of Bucket B: Twitter/X - real-time behavioral layer with context)"""
    inventory = []
    data = load_json(DATA_RAW / "reply_chains_full.json")
    for chain_idx, chain in enumerate(data):
        original = chain.get("original", {})
        replies = chain.get("replies", [])
        
        # Add original post
        inventory.append({
            "bucket": "B",
            "source": "x_reply_context",
            "url": f"https://x.com/shubhgupta/status/{original.get('id', '')}",
            "date": "",  # date not in this structure, would need to cross-ref with x_raw
            "exact_quote": original.get("text", ""),
            "item_id": f"reply_original_{chain_idx}",
            "notes": f"original_post, likes={original.get('metrics',{}).get('likes',0)}, replies_count={len(replies)}"
        })
        
        # Add each reply
        for reply_idx, reply in enumerate(replies):
            inventory.append({
                "bucket": "B",
                "source": "x_reply",
                "url": f"https://x.com/{reply.get('author','').lower()}/status/{reply.get('id','')}",
                "date": "",
                "exact_quote": reply.get("text", ""),
                "item_id": f"reply_{chain_idx}_{reply_idx}",
                "notes": f"reply_to_shubh, author={reply.get('author','')}"
            })
    return inventory

def extract_identity_inventory():
    """Extract identity information (Bucket E: Cross-Cutting Metadata)"""
    inventory = []
    data = load_json(DATA_RAW / "identity_osint.json")
    
    # Extract profile context
    profile = data.get("profile_context", {})
    if profile:
        inventory.append({
            "bucket": "E",
            "source": "identity_profile",
            "url": profile.get("website", ""),
            "date": "",
            "exact_quote": f"Name: {profile.get('confirmed_name','')}, Age: {profile.get('age','')}, Education: {profile.get('education','')}, Location: {profile.get('location','')}, Venture Fund: {profile.get('venture_fund','')}",
            "item_id": "identity_profile",
            "notes": f"x_handle={profile.get('x_handle','')}, x_followers={profile.get('x_followers','')}, x_total_tweets={profile.get('x_total_tweets','')}"
        })
    
    # Add website scrape info from identity
    website_scrape = data.get("identity_sources", {}).get("website_scrape", {})
    if website_scrape:
        inventory.append({
            "bucket": "E",
            "source": "identity_website_scrape",
            "url": "https://shubhxho.com/",
            "date": "",
            "exact_quote": f"Age: {website_scrape.get('age','')}, Education: {website_scrape.get('education','')}, Location: {website_scrape.get('location','')}, Topic: {website_scrape.get('topic','')}",
            "item_id": "identity_website_scrape",
            "notes": ""
        })
    
    # Add X bio info
    x_bio = data.get("identity_sources", {}).get("x_bio", {})
    if x_bio:
        inventory.append({
            "bucket": "E",
            "source": "identity_x_bio",
            "url": "https://x.com/shubhgupta",
            "date": "",
            "exact_quote": f"Bio: {x_bio.get('bio_x','')}, Followers: {x_bio.get('followers','')}, Total Tweets: {x_bio.get('total_tweets','')}",
            "item_id": "identity_x_bio",
            "notes": ""
        })
        
    # Add social graph
    social = data.get("social_graph", {})
    platforms = social.get("platforms_with_profiles", [])
    if platforms:
        inventory.append({
            "bucket": "E",
            "source": "identity_social_graph",
            "url": "",
            "date": "",
            "exact_quote": f"Platforms with profiles: {', '.join(platforms)}",
            "item_id": "identity_social_graph",
            "notes": f"name_variants: {', '.join(social.get('cross_platform_name_variants',[]))}"
        })
        
    return inventory

def extract_github_inventory():
    """Extract from github_hf_complete.json (Buckets C and D)"""
    inventory = []
    data = load_json(DATA_RAW / "github_hf_complete.json")
    
    # Bucket C: GitHub Repositories
    repos = data.get("repos", [])
    for repo in repos:
        inventory.append({
            "bucket": "C",
            "source": "github_repo",
            "url": repo.get("html_url", ""),
            "date": iso_date(repo.get("pushed_at", "")) or iso_date(repo.get("created_at", "")),
            "exact_quote": f"{repo.get('name','')}: {repo.get('description','')}",
            "item_id": f"github_repo_{repo.get('name','')}",
            "notes": f"language={repo.get('language','')}, stars={repo.get('stargazers_count',0)}, fork={repo.get('fork',False)}, pushed={repo.get('pushed_at','')}"
        })
    
    # Bucket D: Hugging Face Models
    hf_models = data.get("hf_models", [])
    for model in hf_models:
        inventory.append({
            "bucket": "D",
            "source": "hf_model",
            "url": f"https://huggingface.co/{model.get('modelId','')}",
            "date": model.get("createdAt", ""),
            "exact_quote": f"{model.get('modelId','')} ({', '.join(model.get('tags',[])[:3])})",
            "item_id": f"hf_model_{model.get('modelId','').replace('/','_')}",
            "notes": f"likes={model.get('likes',0)}, downloads={model.get('downloads',0)}, library={model.get('library_name','')}"
        })
    
    # Bucket D: Hugging Face Datasets
    hf_datasets = data.get("hf_datasets", [])
    for dataset in hf_datasets:
        inventory.append({
            "bucket": "D",
            "source": "hf_dataset",
            "url": f"https://huggingface.co/datasets/{dataset.get('id','')}",
            "date": dataset.get("createdAt", ""),
            "exact_quote": f"{dataset.get('id','')}: {dataset.get('description','')[:200]}",
            "item_id": f"hf_dataset_{dataset.get('id','').replace('/','_')}",
            "notes": f"likes={dataset.get('likes',0)}, downloads={dataset.get('downloads',0)}"
        })
    
    # Bucket D: Hugging Face Spaces
    hf_spaces = data.get("hf_spaces", [])
    for space in hf_spaces:
        inventory.append({
            "bucket": "D",
            "source": "hf_space",
            "url": f"https://huggingface.co/spaces/{space.get('id','')}",
            "date": "",
            "exact_quote": f"{space.get('id','')}: {space.get('description','')} ({space.get('type','')})",
            "item_id": f"hf_space_{space.get('id','')}",
            "notes": ""
        })
        
    # Bucket E: GitHub profile metadata (cross-cutting)
    profile = data.get("profile", {})
    if profile:
        inventory.append({
            "bucket": "E",
            "source": "github_profile",
            "url": profile.get("html_url", ""),
            "date": iso_date(profile.get("updated_at", "")) or iso_date(profile.get("created_at", "")),
            "exact_quote": f"GitHub: {profile.get('name','')} (@{profile.get('login','')}), {profile.get('public_repos',0)} repos, {profile.get('followers',0)} followers, {profile.get('following',0)} following",
            "item_id": "github_profile",
            "notes": f"company={profile.get('company','')}, blog={profile.get('blog','')}, location={profile.get('location','')}, twitter_username={profile.get('twitter_username','')}"
        })
        
    # Bucket E: GitHub stats
    stats = data.get("stats", {})
    if stats:
        inventory.append({
            "bucket": "E",
            "source": "github_stats",
            "url": "",
            "date": "",
            "exact_quote": f"GitHub stats: {stats.get('total_repos',0)} repos, {stats.get('total_starred',0)} starred, {stats.get('total_readmes',0)} readmes, {stats.get('total_hf_models',0)} HF models, {stats.get('total_hf_datasets',0)} HF datasets, {stats.get('total_hf_spaces',0)} HF spaces",
            "item_id": "github_stats",
            "notes": f"most_used_langs: {stats.get('most_used_langs',[])}, github_followers: {stats.get('github_followers',0)}, github_following: {stats.get('github_following',0)}, twitter_followers: {stats.get('twitter_followers',0)}"
        })
        
    return inventory

def main():
    print("Starting inventory extraction...")
    
    all_inventory = []
    
    # Extract from each source
    print("Extracting website inventory...")
    all_inventory.extend(extract_website_inventory())
    
    print("Extracting X inventory...")
    all_inventory.extend(extract_x_inventory())
    
    print("Extracting reply chains inventory...")
    all_inventory.extend(extract_reply_chains_inventory())
    
    print("Extracting identity inventory...")
    all_inventory.extend(extract_identity_inventory())
    
    print("Extracting GitHub/HF inventory...")
    all_inventory.extend(extract_github_inventory())
    
    # Write inventory
    output_file = ANALYSIS_DATA / "inventory.jsonl"
    with open(output_file, 'w') as f:
        for item in all_inventory:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"Extraction complete. {len(all_inventory)} items written to {output_file}")
    
    # Print bucket counts for verification
    bucket_counts = {}
    for item in all_inventory:
        bucket = item["bucket"]
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
    
    print("Bucket counts:")
    for bucket in sorted(bucket_counts.keys()):
        print(f"  {bucket}: {bucket_counts[bucket]}")

if __name__ == "__main__":
    main()