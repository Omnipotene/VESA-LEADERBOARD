#!/usr/bin/env python3
"""
Scrape S11 Placement Data from Overstat
"""

import csv
import json
import time
from src.scraper import OverstatScraper

print("VESA League - S11 Placement Scraper")
print("="*70)

# Load S11 placement URLs
with open('config/s11_placements_urls.csv', 'r') as f:
    reader = csv.DictReader(f)
    urls_to_scrape = []
    
    for row in reader:
        url = row['url'].strip()
        day = int(row['day'])
        lobby = row['lobby'].strip()  # Keep as string (handles "1.5" etc)
        data_type = row['type'].strip()
        
        urls_to_scrape.append({
            'url': url,
            'day': day,
            'lobby': lobby,
            'type': data_type
        })

print(f"Found {len(urls_to_scrape)} S11 placement lobbies to scrape")
print(f"  Days: {sorted(set(u['day'] for u in urls_to_scrape))}")
print(f"  Lobbies per day: {len([u for u in urls_to_scrape if u['day'] == 1])}")
print()

# Scrape all lobbies
all_data = []
successful = 0
failed = 0

with OverstatScraper(headless=True, timeout=60000) as scraper:
    for i, url_config in enumerate(urls_to_scrape, 1):
        url = url_config['url']
        day = url_config['day']
        lobby = url_config['lobby']
        data_type = url_config['type']
        
        print(f"[{i}/{len(urls_to_scrape)}] Day {day}, Lobby {lobby}...", end=' ', flush=True)
        
        try:
            data = scraper.scrape_url(url, data_type)
            
            # Add metadata
            for entry in data:
                entry['day'] = day
                entry['lobby'] = lobby
                entry['source_url'] = url
            
            all_data.extend(data)
            successful += 1
            print(f"✓ {len(data)} players")
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            failed += 1
            print(f"✗ ERROR: {e}")
            continue

print(f"\n{'='*70}")
print("SCRAPING COMPLETE")
print("="*70)
print(f"Successful: {successful}/{len(urls_to_scrape)}")
print(f"Failed: {failed}/{len(urls_to_scrape)}")
print(f"Total player entries: {len(all_data)}")

# Save raw data
output_file = "output/s11_placements_raw.json"
with open(output_file, 'w') as f:
    json.dump(all_data, f, indent=2)

print(f"\nSaved to: {output_file}")
print(f"\nNext step: Apply weights and deduplicate")
print("  python3 apply_s11_weights.py")
