#!/usr/bin/env python3
"""
Scrape S12 Team Rosters from Overstat to Extract Discord Names
This will help us build comprehensive alias mappings for S12 players
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
from collections import defaultdict

print("VESA S12 - Roster Scraper (Discord Name Extraction)")
print("="*70)

# Load placement URLs
placement_urls = []
with open('config/s12_placements_urls.csv', 'r') as f:
    reader = csv.DictReader(f)
    placement_urls = list(reader)

print(f"Loaded {len(placement_urls)} placement lobby URLs")

# We need to convert player-standings URLs to team-rosters URLs
# Example: /player-standings -> /team-rosters

all_rosters = defaultdict(lambda: {
    'discord_name': None,
    'in_game_names': set(),
    'teams': set()
})

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

successful_scrapes = 0
failed_scrapes = 0

print("\nScraping team rosters from S12 placement lobbies...")
print("-"*70)

for i, lobby in enumerate(placement_urls, 1):
    # Convert to team-rosters URL
    roster_url = lobby['url'].replace('/player-standings', '/team-rosters')

    print(f"{i}/{len(placement_urls)}: {lobby['description'][:50]}")

    try:
        response = requests.get(roster_url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all team sections
        team_sections = soup.find_all('div', class_='team-section')

        if not team_sections:
            print(f"  ⚠️  No team sections found")
            failed_scrapes += 1
            time.sleep(2)
            continue

        players_found = 0

        for team_section in team_sections:
            # Get team name
            team_name_elem = team_section.find('h3', class_='team-name')
            team_name = team_name_elem.get_text(strip=True) if team_name_elem else 'Unknown'

            # Find all player rows
            player_rows = team_section.find_all('div', class_='roster-player')

            for player_row in player_rows:
                # Get in-game name
                ign_elem = player_row.find('span', class_='player-ign')
                if not ign_elem:
                    continue

                in_game_name = ign_elem.get_text(strip=True)

                # Get Discord name (usually in a different span or data attribute)
                discord_elem = player_row.find('span', class_='player-discord') or \
                              player_row.find('span', class_='discord-name')

                if discord_elem:
                    discord_name = discord_elem.get_text(strip=True).lower()
                else:
                    # Try to find in data attributes
                    discord_name = player_row.get('data-discord', '').lower()

                if not discord_name:
                    # Use in-game name as fallback
                    discord_name = in_game_name.lower()

                # Store the mapping
                all_rosters[discord_name]['discord_name'] = discord_name
                all_rosters[discord_name]['in_game_names'].add(in_game_name)
                all_rosters[discord_name]['teams'].add(team_name)
                players_found += 1

        print(f"  ✅ Found {players_found} players across {len(team_sections)} teams")
        successful_scrapes += 1

    except Exception as e:
        print(f"  ❌ Error: {str(e)[:50]}")
        failed_scrapes += 1

    # Rate limiting
    time.sleep(2)

    # Progress checkpoint every 5 lobbies
    if i % 5 == 0:
        print(f"  Progress: {successful_scrapes} successful, {failed_scrapes} failed")

print()
print("="*70)
print("SCRAPING COMPLETE")
print("="*70)
print(f"Successful scrapes: {successful_scrapes}/{len(placement_urls)}")
print(f"Failed scrapes: {failed_scrapes}/{len(placement_urls)}")
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
print(f"\nNext step: Merge this data into player_aliases.json")
print("  Run: python3 merge_s12_aliases.py")
