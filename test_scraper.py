#!/usr/bin/env python3
"""
Test script for the Overstat.gg scraper.
Use this to debug and verify scraping works before running the full pipeline.
"""

import sys
from src.scraper import OverstatScraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_single_url(url: str, data_type: str):
    """
    Test scraping a single URL.

    Args:
        url: Overstat.gg URL to scrape
        data_type: "player" or "team"
    """
    print(f"\n{'='*70}")
    print(f"Testing Scraper")
    print(f"{'='*70}")
    print(f"URL: {url}")
    print(f"Type: {data_type}")
    print(f"{'='*70}\n")

    with OverstatScraper(headless=False, timeout=60000) as scraper:
        try:
            stats = scraper.scrape_url(url, data_type)

            print(f"\n{'='*70}")
            print(f"Results: Found {len(stats)} entries")
            print(f"{'='*70}\n")

            if stats:
                print("Sample data (first 5 entries):")
                print(f"{'-'*70}")
                for i, stat in enumerate(stats[:5], 1):
                    print(f"\n{i}. {stat.get('player_name', stat.get('team_name', 'Unknown'))}")
                    for key, value in stat.items():
                        print(f"   {key}: {value}")

                print(f"\n{'-'*70}")
                print(f"Total entries: {len(stats)}")
            else:
                print("WARNING: No data extracted!")
                print("Check output/debug_page.html to see the page structure")

        except Exception as e:
            print(f"\nERROR: {str(e)}")
            print("Check output/error_*.png for screenshot")
            return False

    return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_scraper.py <url> <type>")
        print("")
        print("Examples:")
        print("  python test_scraper.py 'https://overstat.gg/tournament/.../player-standings' player")
        print("  python test_scraper.py 'https://overstat.gg/tournament/.../scoreboard' team")
        sys.exit(1)

    url = sys.argv[1]
    data_type = sys.argv[2]

    if data_type not in ['player', 'team']:
        print("ERROR: Type must be 'player' or 'team'")
        sys.exit(1)

    success = test_single_url(url, data_type)
    sys.exit(0 if success else 1)
