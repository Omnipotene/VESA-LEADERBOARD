#!/usr/bin/env python3
"""
Scrape Season 12 Placements data from all lobbies
"""

import csv
import json
import time
from src.scraper import OverstatScraper

print("VESA League - Season 12 Placements Scraper")
print("="*70)

# Load URLs from CSV
urls_to_scrape = []
with open('config/s12_placements_urls.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        urls_to_scrape.append({
            'url': row['url'],
            'day': int(row['day']),
            'lobby': row['lobby'],
            'type': row['type'],
            'description': row['description']
        })

print(f"Found {len(urls_to_scrape)} URLs to scrape\n")

# Scrape each URL
all_scraped_data = []
successful = 0
failed = 0

# Use context manager to properly initialize browser
with OverstatScraper(headless=True) as scraper:
    for i, url_config in enumerate(urls_to_scrape, 1):
        url = url_config['url']
        day = url_config['day']
        lobby = url_config['lobby']
        data_type = url_config['type']
        desc = url_config['description']

        print(f"[{i}/{len(urls_to_scrape)}] {desc}")
        print(f"  URL: {url}")

        try:
            # Scrape the URL
            data = scraper.scrape_url(url, data_type)

            # Add metadata
            for entry in data:
                entry['day'] = day
                entry['lobby'] = lobby
                entry['source_url'] = url

            all_scraped_data.extend(data)
            successful += 1

            print(f"  ✓ Scraped {len(data)} players")
            print()

            # Rate limiting - wait between requests
            if i < len(urls_to_scrape):
                print(f"  Waiting 3 seconds before next scrape...")
                time.sleep(3)

        except Exception as e:
            print(f"  ✗ ERROR: {e}\n")
            failed += 1
            continue

# Save all data to JSON
output_file = "output/s12_placements_raw.json"
with open(output_file, 'w') as f:
    json.dump(all_scraped_data, f, indent=2)

print("="*70)
print("SCRAPING COMPLETE")
print("="*70)
print(f"Successful: {successful}/{len(urls_to_scrape)}")
print(f"Failed: {failed}/{len(urls_to_scrape)}")
print(f"Total players scraped: {len(all_scraped_data)}")
print(f"Saved to: {output_file}")
print(f"\nNext step: Apply weights and deduplicate")
