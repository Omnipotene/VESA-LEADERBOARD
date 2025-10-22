#!/usr/bin/env python3
"""
Scrape player aliases from multiple season roster files
Supports CSV files with Overstat profile links
"""

import csv
import json
import time
import os
from src.scraper import OverstatScraper

print("VESA League - Multi-Season Alias Scraper")
print("="*70)

# Define roster files to process
# Add new files here as you receive them
ROSTER_FILES = {
    'S12': {
        'file': 'data/rosters.csv',
        'format': 's12'  # S12 format
    },
    'S11': {
        'file': 'data/Copy of VESA Season 11 Signups - Signup Responses.csv',
        'format': 's11'  # S11 has different Team Name column
    },
    'S10': {
        'file': 'data/Copy of VESA Season 10 Signup Form (Responses) - Signup responses.csv',
        'format': 's12'  # S10 uses same format as S12
    },
    'S8': {
        'file': 'data/Copy of VESA Apex Season 8 Signups (v 2.0) - Signups.csv',
        'format': 's8'  # S8 has different column names
    },
    # Add these as you receive the files:
    # 'S6': {'file': 'data/rosters_s6.csv', 'format': 's6'},
    # 'S5': {'file': 'data/rosters_s5.csv', 'format': 's5'},
    # 'S4': {'file': 'data/rosters_s4.csv', 'format': 's4'},
}

print("Roster files to process:")
for season, config in ROSTER_FILES.items():
    filepath = config['file']
    if os.path.exists(filepath):
        print(f"  ✓ {season}: {filepath}")
    else:
        print(f"  ✗ {season}: {filepath} (NOT FOUND - will skip)")

print()

# Collect all player profiles
player_profiles = []

for season, config in ROSTER_FILES.items():
    filepath = config['file']
    fmt = config['format']

    if not os.path.exists(filepath):
        print(f"Skipping {season} - file not found")
        continue

    print(f"Processing {season} roster...")

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        season_count = 0

        for row in reader:
            # Different formats have different column names
            if fmt == 's12':
                team_name = row.get('Team Name', '').strip()
                if not team_name or 'Lobby' in team_name:
                    continue

                # S12 format
                for i in range(1, 4):
                    discord = row.get(f'Rostered Player {i} Discord Username', '').strip()
                    overstat_link = row.get(f'Rostered Player {i} Overstat Link', '').strip()

                    if discord and overstat_link and '/player/' in overstat_link:
                        player_part = overstat_link.split('/player/')[1].split('/')[0]
                        player_id = player_part.split('.')[0]
                        profile_url = f'https://overstat.gg/player/{player_id}/overview'

                        player_profiles.append({
                            'discord_name': discord,
                            'overstat_link': overstat_link,
                            'profile_url': profile_url,
                            'player_id': player_id,
                            'season': season
                        })
                        season_count += 1

            elif fmt == 's11':
                # S11 has a different Team Name column with extra text
                # Find the Team Name column dynamically
                team_name = None
                for key in row.keys():
                    if 'Team Name' in key:
                        team_name = row[key].strip()
                        break

                if not team_name or 'Lobby' in team_name:
                    continue

                # S11 uses same player columns as S12
                for i in range(1, 4):
                    discord = row.get(f'Rostered Player {i} Discord Username', '').strip()
                    overstat_link = row.get(f'Rostered Player {i} Overstat Link', '').strip()

                    if discord and overstat_link and '/player/' in overstat_link:
                        player_part = overstat_link.split('/player/')[1].split('/')[0]
                        player_id = player_part.split('.')[0]
                        profile_url = f'https://overstat.gg/player/{player_id}/overview'

                        player_profiles.append({
                            'discord_name': discord,
                            'overstat_link': overstat_link,
                            'profile_url': profile_url,
                            'player_id': player_id,
                            'season': season
                        })
                        season_count += 1

            elif fmt == 's8':
                team_name = row.get('Team Name', '').strip()
                if not team_name:
                    continue

                # S8 format has multi-line column headers - need to match the key
                for i in range(1, 4):
                    # Find the column that contains the pattern we're looking for
                    overstat_link = ''
                    ign = ''

                    for key in row.keys():
                        if f'Overstat and/or DGS profile (Player {i})' in key:
                            overstat_link = row[key].strip()
                        if f'In game name (Player {i})' in key:
                            ign = row[key].strip()

                    if overstat_link and '/player/' in overstat_link:
                        try:
                            player_part = overstat_link.split('/player/')[1].split('/')[0]
                            player_id = player_part.split('.')[0]
                            profile_url = f'https://overstat.gg/player/{player_id}/overview'

                            player_profiles.append({
                                'discord_name': ign if ign else f"Player_{player_id}",
                                'overstat_link': overstat_link,
                                'profile_url': profile_url,
                                'player_id': player_id,
                                'season': season
                            })
                            season_count += 1
                        except Exception as e:
                            # Silently skip malformed links
                            pass

        print(f"  Found {season_count} players in {season}")

print(f"\nTotal players found: {len(player_profiles)}")

# Remove duplicates (same player ID)
unique_profiles = {}
for p in player_profiles:
    if p['player_id'] not in unique_profiles:
        unique_profiles[p['player_id']] = p
    else:
        # Player appears in multiple seasons - keep track of that
        existing = unique_profiles[p['player_id']]
        if 'seasons' not in existing:
            existing['seasons'] = [existing['season']]
        existing['seasons'].append(p['season'])

print(f"Unique players: {len(unique_profiles)}")

# Load existing alias data (if it exists)
existing_aliases = {}
try:
    with open('data/player_aliases.json', 'r') as f:
        existing_data = json.load(f)
        for player in existing_data:
            existing_aliases[player['player_id']] = player
        print(f"Loaded {len(existing_aliases)} existing alias records")
except FileNotFoundError:
    print("No existing alias data found - will create new file")

# Identify new players to scrape
players_to_scrape = {}
for player_id, profile in unique_profiles.items():
    if player_id not in existing_aliases:
        players_to_scrape[player_id] = profile

print(f"\nNew players to scrape: {len(players_to_scrape)}")
print(f"Already have data for: {len(unique_profiles) - len(players_to_scrape)} players")

if len(players_to_scrape) == 0:
    print("\n✓ All players already have alias data!")
    print("No scraping needed.")
    exit(0)

# Scrape aliases for new players
print(f"\nScraping aliases for {len(players_to_scrape)} new players...")
print("-"*70)

aliases_data = []
successful = 0
failed = 0

with OverstatScraper(headless=True, timeout=15000) as scraper:
    for i, (player_id, profile) in enumerate(players_to_scrape.items(), 1):
        discord = profile['discord_name']
        url = profile['profile_url']

        if i % 10 == 0:
            print(f"Progress: {i}/{len(players_to_scrape)}")

        try:
            page = scraper.browser.new_page()
            page.set_default_timeout(15000)
            page.goto(url, timeout=15000, wait_until='domcontentloaded')

            # Wait for the specific selector
            page.wait_for_selector('[data-v-d5849fba].text-center', timeout=10000)

            # Extract all in-game names
            names = page.evaluate('''
                () => {
                    const names = [];
                    const namesDivs = document.querySelectorAll('[data-v-d5849fba].text-center');

                    namesDivs.forEach(div => {
                        const text = div.innerText.trim();
                        const textUpper = text.toUpperCase();
                        if (text && text.length > 0 && text.length < 100 &&
                            !textUpper.includes('IN-GAME NAMES') &&
                            !textUpper.includes('STATS')) {
                            names.push(text);
                        }
                    });

                    return names;
                }
            ''')

            page.close()

            if names and len(names) > 0:
                aliases_data.append({
                    'player_id': player_id,
                    'discord_name': discord,
                    'profile_url': url,
                    'aliases': names,
                    'alias_count': len(names)
                })
                successful += 1

                if i <= 5:  # Show first 5 as examples
                    print(f"  {discord}: {len(names)} aliases found")
            else:
                failed += 1
                print(f"  {discord}: NO ALIASES FOUND")

            time.sleep(0.5)

        except Exception as e:
            failed += 1
            print(f"  {discord}: ERROR - {e}")
            try:
                page.close()
            except:
                pass
            continue

print(f"\n{'='*70}")
print("SCRAPING COMPLETE")
print("="*70)
print(f"New players scraped: {successful}/{len(players_to_scrape)}")
print(f"Failed: {failed}/{len(players_to_scrape)}")

# Merge with existing data
all_aliases = list(existing_aliases.values()) + aliases_data

# Save merged aliases
output_file = "data/player_aliases.json"
with open(output_file, 'w') as f:
    json.dump(all_aliases, f, indent=2)

print(f"\nSaved to: {output_file}")

# Show statistics
total_aliases = sum(p.get('alias_count', len(p.get('aliases', []))) for p in all_aliases)
avg_aliases = total_aliases / len(all_aliases) if all_aliases else 0

print(f"\nTotal players in database: {len(all_aliases)}")
print(f"Total aliases collected: {total_aliases}")
print(f"Average aliases per player: {avg_aliases:.1f}")

print(f"\n{'='*70}")
print("Next steps:")
print("  1. Add more roster files to ROSTER_FILES at the top of this script")
print("  2. Re-run this script to scrape more players")
print("  3. When done, regenerate ratings:")
print("     python3 combine_all_seasons.py")
print("     python3 apply_top_lobby_bonus_all_seasons.py")
print("     python3 team_seeding_combined.py")
print("     python3 division_seeding.py")
