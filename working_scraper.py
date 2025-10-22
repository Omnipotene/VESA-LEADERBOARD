#!/usr/bin/env python3
"""
Working scraper - extracts actual player data from Overstat
"""

from playwright.sync_api import sync_playwright
import time
import json

def scrape_overstat_players(url):
    """Scrape player standings from Overstat.gg"""

    print(f"Scraping: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Loading page...")
        page.goto(url, timeout=60000)

        print("Waiting for data to load...")
        # Wait for the table to appear
        page.wait_for_selector("table", timeout=30000)

        # Extra wait for React to fully render
        time.sleep(5)

        print("Extracting player data...")

        # Get all table rows
        players = []
        rows = page.query_selector_all("table tbody tr")

        print(f"Found {len(rows)} rows")

        for i, row in enumerate(rows):
            try:
                # Get all cells in the row
                cells = row.query_selector_all("td")

                if len(cells) < 6:
                    continue

                # Extract text from each cell
                rank = cells[0].inner_text().strip()
                player_name = cells[1].inner_text().strip()
                team_name = cells[2].inner_text().strip()

                # Stats columns - adjust indices based on actual table structure
                score_text = cells[3].inner_text().strip()
                kills_text = cells[4].inner_text().strip()
                damage_text = cells[5].inner_text().strip()

                # Parse numbers
                try:
                    score = float(score_text.replace(',', ''))
                except:
                    score = 0

                try:
                    kills = int(kills_text.replace(',', ''))
                except:
                    kills = 0

                try:
                    damage = int(damage_text.replace(',', ''))
                except:
                    damage = 0

                player_data = {
                    'rank': rank,
                    'player_name': player_name,
                    'team_name': team_name,
                    'score': score,
                    'kills': kills,
                    'damage': damage
                }

                players.append(player_data)

                # Print first 5 for preview
                if i < 5:
                    print(f"  {rank}. {player_name} ({team_name}) - {score} pts, {kills} kills, {damage:,} dmg")

            except Exception as e:
                print(f"Error parsing row {i}: {e}")
                continue

        browser.close()

        return players

if __name__ == "__main__":
    url = "https://overstat.gg/tournament/VESA%20League/13938.VESA_S11_Pinnacle_I_all_weeks_/standings/overall/player-standings"

    players = scrape_overstat_players(url)

    print(f"\n✅ Scraped {len(players)} players successfully!")

    # Save to JSON
    output_file = "output/players_data.json"
    with open(output_file, 'w') as f:
        json.dump(players, f, indent=2)

    print(f"Saved to: {output_file}")

    # Show summary stats
    if players:
        total_kills = sum(p['kills'] for p in players)
        total_damage = sum(p['damage'] for p in players)
        print(f"\nSummary:")
        print(f"  Total players: {len(players)}")
        print(f"  Total kills: {total_kills:,}")
        print(f"  Total damage: {total_damage:,}")
        print(f"\nTop 5 players:")
        for p in players[:5]:
            print(f"  {p['rank']}. {p['player_name']} - {p['score']} pts")
