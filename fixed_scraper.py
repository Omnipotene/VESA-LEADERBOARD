#!/usr/bin/env python3
"""
Fixed scraper - handles large tables without memory issues
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
        page.wait_for_selector("table", timeout=30000)
        time.sleep(5)

        print("Extracting player data...")

        # Instead of keeping references to all rows, we'll extract data immediately
        # This prevents the "object collected" error

        # Use JavaScript to extract all data at once
        player_data = page.evaluate("""
            () => {
                const players = [];
                const rows = document.querySelectorAll('table tbody tr');

                rows.forEach((row, index) => {
                    const cells = row.querySelectorAll('td');

                    if (cells.length >= 6) {
                        try {
                            const rank = cells[0].innerText.trim();
                            const playerName = cells[1].innerText.trim();
                            const teamName = cells[2].innerText.trim();
                            const scoreText = cells[3].innerText.trim();
                            const killsText = cells[4].innerText.trim();
                            const damageText = cells[5].innerText.trim();

                            const score = parseFloat(scoreText.replace(/,/g, '')) || 0;
                            const kills = parseInt(killsText.replace(/,/g, '')) || 0;
                            const damage = parseInt(damageText.replace(/,/g, '')) || 0;

                            players.push({
                                rank: rank,
                                player_name: playerName,
                                team_name: teamName,
                                score: score,
                                kills: kills,
                                damage: damage
                            });
                        } catch (e) {
                            console.error('Error parsing row', index, e);
                        }
                    }
                });

                return players;
            }
        """)

        browser.close()

        return player_data

if __name__ == "__main__":
    url = "https://overstat.gg/tournament/VESA%20League/13938.VESA_S11_Pinnacle_I_all_weeks_/standings/overall/player-standings"

    players = scrape_overstat_players(url)

    print(f"\n✅ Scraped {len(players)} players successfully!")

    # Save to JSON
    output_file = "output/players_data.json"
    with open(output_file, 'w') as f:
        json.dump(players, f, indent=2)

    print(f"Saved to: {output_file}")

    # Show preview
    if players:
        print(f"\nFirst 5 players:")
        for p in players[:5]:
            print(f"  {p['rank']}. {p['player_name']} ({p['team_name']}) - {p['score']} pts, {p['kills']} kills, {p['damage']:,} dmg")

        print(f"\nLast 5 players:")
        for p in players[-5:]:
            print(f"  {p['rank']}. {p['player_name']} ({p['team_name']}) - {p['score']} pts, {p['kills']} kills, {p['damage']:,} dmg")

        # Summary stats
        total_kills = sum(p['kills'] for p in players)
        total_damage = sum(p['damage'] for p in players)
        avg_score = sum(p['score'] for p in players) / len(players)

        print(f"\nSummary:")
        print(f"  Total players: {len(players)}")
        print(f"  Total kills: {total_kills:,}")
        print(f"  Total damage: {total_damage:,}")
        print(f"  Average score: {avg_score:.2f}")
