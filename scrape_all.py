#!/usr/bin/env python3
"""
Scrape all URLs from the CSV file and combine into one dataset
"""

import csv
import json
from playwright.sync_api import sync_playwright
import time

def scrape_url(url, day, lobby, description):
    """Scrape a single URL"""
    print(f"\n{'='*70}")
    print(f"Scraping: {description}")
    print(f"Lobby {lobby} (weight will be applied later)")
    print(f"{'='*70}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url, timeout=60000)
        page.wait_for_selector("table", timeout=30000)
        time.sleep(5)

        # Extract data using JavaScript
        players = page.evaluate("""
            () => {
                const players = [];
                const rows = document.querySelectorAll('table tbody tr');

                rows.forEach((row) => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 6) {
                        try {
                            players.push({
                                rank: cells[0].innerText.trim(),
                                player_name: cells[1].innerText.trim(),
                                team_name: cells[2].innerText.trim(),
                                score: parseFloat(cells[3].innerText.replace(/,/g, '')) || 0,
                                kills: parseInt(cells[4].innerText.replace(/,/g, '')) || 0,
                                damage: parseInt(cells[5].innerText.replace(/,/g, '')) || 0
                            });
                        } catch (e) {}
                    }
                });

                return players;
            }
        """)

        browser.close()
        return players

def main():
    print("VESA League - Multi-Division Scraper")
    print("="*70)

    # Load URLs from CSV
    urls_file = "config/urls.csv"
    all_players = []
    division_stats = {}

    with open(urls_file, 'r') as f:
        reader = csv.DictReader(f)
        urls = list(reader)

    print(f"\nFound {len(urls)} divisions to scrape\n")

    # Scrape each URL
    for url_data in urls:
        players = scrape_url(
            url_data['url'],
            url_data['day'],
            url_data['lobby'],
            url_data['description']
        )

        # Add division/lobby info to each player
        for player in players:
            player['division'] = url_data['description']
            player['lobby'] = url_data['lobby']
            player['day'] = url_data['day']

        all_players.extend(players)

        division_stats[url_data['description']] = {
            'player_count': len(players),
            'lobby': url_data['lobby']
        }

        print(f"✅ Scraped {len(players)} players from {url_data['description']}")

    # Save combined data
    output_file = "output/all_divisions_data.json"
    with open(output_file, 'w') as f:
        json.dump(all_players, f, indent=2)

    print(f"\n{'='*70}")
    print("SCRAPING COMPLETE!")
    print(f"{'='*70}")
    print(f"\nTotal players scraped: {len(all_players)}")
    print(f"Saved to: {output_file}")

    print(f"\nBreakdown by division:")
    for div, stats in division_stats.items():
        print(f"  {div:30} Lobby {stats['lobby']}: {stats['player_count']:3} players")

    # Calculate totals
    total_kills = sum(p['kills'] for p in all_players)
    total_damage = sum(p['damage'] for p in all_players)

    print(f"\nOverall stats:")
    print(f"  Total kills: {total_kills:,}")
    print(f"  Total damage: {total_damage:,}")

    print(f"\nTop 10 players across all divisions:")
    sorted_players = sorted(all_players, key=lambda x: x['score'], reverse=True)
    for i, p in enumerate(sorted_players[:10], 1):
        print(f"  {i:2}. {p['player_name']:20} ({p['division']:25}) - {p['score']:6.0f} pts, {p['kills']:3} kills")

if __name__ == "__main__":
    main()
