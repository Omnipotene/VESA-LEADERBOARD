#!/usr/bin/env python3
"""
Scrape S11 Overall Standings (consolidated placement data)
This is faster and more reliable than individual lobby URLs
"""

import json
from src.scraper import OverstatScraper

print("VESA League - S11 Overall Standings Scraper")
print("="*70)

url = "https://overstat.gg/tournament/VESA%20League/13938.VESA_S11_Pinnacle_I_all_weeks_/standings/overall/player-standings"

print(f"Scraping: {url}\n")

with OverstatScraper(headless=True, timeout=90000) as scraper:
    try:
        data = scraper.scrape_url(url, 'player')
        
        print(f"✓ Successfully scraped {len(data)} players")
        
        # Save raw data
        output_file = "output/s11_overall_raw.json"
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Saved to: {output_file}")
        
        # Show sample
        print(f"\nSample (first 5 players):")
        for i, player in enumerate(data[:5], 1):
            print(f"{i}. {player['player_name']}: {player['score']} pts, {player['kills']} kills")
        
        print(f"\n{'='*70}")
        print("✅ S11 SCRAPING COMPLETE")
        print("="*70)
        print("Next step: Deduplicate with aliases (no weights needed - already overall)")
        print("  python3 deduplicate_s11_overall.py")
        
    except Exception as e:
        print(f"✗ ERROR: {e}")
        exit(1)
