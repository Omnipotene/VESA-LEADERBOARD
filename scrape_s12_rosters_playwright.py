#!/usr/bin/env python3
"""
Scrape S12 Team Rosters using Playwright to Extract Discord Names
This will help us build comprehensive alias mappings for S12 players
"""

import sys
sys.path.append('src')

from scraper import OverstatScraper
import json
import csv
from collections import defaultdict
import time

print("VESA S12 - Roster Scraper (Discord Name Extraction with Playwright)")
print("="*70)

# Load placement URLs
placement_urls = []
with open('config/s12_placements_urls.csv', 'r') as f:
    reader = csv.DictReader(f)
    placement_urls = list(reader)

print(f"Loaded {len(placement_urls)} placement lobby URLs")

# Convert to roster URLs
roster_urls = []
for lobby in placement_urls:
    roster_url = lobby['url'].replace('/player-standings', '/team-rosters')
    roster_urls.append({
        'url': roster_url,
        'description': lobby['description']
    })

print(f"Converted to {len(roster_urls)} roster URLs")

all_rosters = defaultdict(lambda: {
    'discord_name': None,
    'in_game_names': set(),
    'teams': set()
})

successful_scrapes = 0
failed_scrapes = 0

print("\nScraping team rosters from S12 placement lobbies...")
print("-"*70)

# Use Playwright scraper
with OverstatScraper(headless=True, timeout=60000) as scraper:
    for i, lobby_info in enumerate(roster_urls, 1):
        url = lobby_info['url']
        print(f"\n{i}/{len(roster_urls)}: {lobby_info['description'][:60]}")
        print(f"  URL: {url}")

        try:
            # Create a custom scraper for roster pages
            page = scraper.browser.new_page()
            page.set_default_timeout(60000)

            # Navigate to roster page
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            print("  ⏳ Waiting for page to load...")
            time.sleep(5)  # Wait for React to render

            # Extract roster data using JavaScript
            roster_data = page.evaluate("""
                () => {
                    const rosters = [];

                    // Find all team containers
                    const teamSections = document.querySelectorAll('[class*="team"], [class*="roster"]');

                    // If no specific team sections, try to find table rows grouped by team
                    const allRows = document.querySelectorAll('table tbody tr, .roster-row, [class*="player-row"]');

                    let currentTeam = null;

                    allRows.forEach((row) => {
                        // Check if this is a team header row
                        const teamHeader = row.querySelector('[class*="team-name"], h2, h3, h4, strong');
                        if (teamHeader) {
                            currentTeam = teamHeader.innerText.trim();
                            return;
                        }

                        // Try to extract player info
                        const cells = row.querySelectorAll('td, [class*="player"], [class*="name"]');

                        if (cells.length >= 2) {
                            let playerName = null;
                            let discordName = null;

                            // Try different selectors for player name and discord
                            cells.forEach((cell, idx) => {
                                const text = cell.innerText.trim();
                                const dataDiscord = cell.getAttribute('data-discord');
                                const title = cell.getAttribute('title');

                                // Look for discord name in attributes
                                if (dataDiscord) {
                                    discordName = dataDiscord;
                                }

                                // Look for player name (usually first non-empty cell)
                                if (text && !playerName && text.length > 0 && !text.match(/^\\d+$/)) {
                                    playerName = text;
                                }

                                // Check if cell contains both IGN and Discord (common format: "IGN (Discord)")
                                const match = text.match(/^(.+?)\\s*\\((.+?)\\)$/);
                                if (match) {
                                    playerName = match[1].trim();
                                    discordName = match[2].trim();
                                }
                            });

                            if (playerName) {
                                rosters.push({
                                    team: currentTeam || 'Unknown',
                                    player_name: playerName,
                                    discord_name: discordName || playerName  // Fallback to player_name
                                });
                            }
                        }
                    });

                    return rosters;
                }
            """)

            if roster_data and len(roster_data) > 0:
                print(f"  ✅ Found {len(roster_data)} players")

                for player in roster_data:
                    discord = player['discord_name'].lower().strip()
                    ign = player['player_name']
                    team = player['team']

                    all_rosters[discord]['discord_name'] = discord
                    all_rosters[discord]['in_game_names'].add(ign)
                    all_rosters[discord]['teams'].add(team)

                successful_scrapes += 1
            else:
                print(f"  ⚠️  No roster data found")

                # Save screenshot for debugging
                screenshot_path = f"output/roster_debug_{i}.png"
                page.screenshot(path=screenshot_path)
                print(f"  📸 Screenshot saved: {screenshot_path}")

                failed_scrapes += 1

            page.close()

        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}")
            failed_scrapes += 1

        # Progress checkpoint every 5 lobbies
        if i % 5 == 0:
            print(f"\n  📊 Progress: {successful_scrapes} successful, {failed_scrapes} failed, {len(all_rosters)} unique players")

        # Rate limiting
        time.sleep(2)

print()
print("="*70)
print("SCRAPING COMPLETE")
print("="*70)
print(f"Successful scrapes: {successful_scrapes}/{len(roster_urls)}")
print(f"Failed scrapes: {failed_scrapes}/{len(roster_urls)}")
print(f"Unique players found: {len(all_rosters)}")

# Convert to output format matching existing alias structure
output_aliases = []

for discord_name, data in all_rosters.items():
    if data['in_game_names']:
        output_aliases.append({
            'discord_name': discord_name,
            'aliases': sorted(list(data['in_game_names'])),
            'teams_s12': sorted(list(data['teams']))
        })

# Sort by discord name
output_aliases.sort(key=lambda x: x['discord_name'])

# Save results
output_file = 'data/s12_rosters_scraped.json'
with open(output_file, 'w') as f:
    json.dump(output_aliases, f, indent=2)

print(f"\n✅ Saved S12 roster data to: {output_file}")
print(f"   Total players: {len(output_aliases)}")
print(f"   Total aliases: {sum(len(p['aliases']) for p in output_aliases)}")

# Show sample
print(f"\nSample players (first 10):")
for player in output_aliases[:10]:
    aliases = ', '.join(player['aliases'][:3])
    if len(player['aliases']) > 3:
        aliases += f" (+{len(player['aliases'])-3} more)"
    print(f"  {player['discord_name']}: {aliases}")

print(f"\nNext step: Merge this data into player_aliases.json")
print("  Run: python3 merge_s12_aliases.py")
