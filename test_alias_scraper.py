#!/usr/bin/env python3
"""
Test: Scrape player profile pages to get complete name history/aliases
"""

import csv
import json
import time
from src.scraper import OverstatScraper

print("VESA League - Player Alias Scraper (TEST - First 5 Players)")
print("="*70)

# Load roster to get Overstat profile URLs
player_profiles = []

with open('data/rosters.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        team_name = row.get('Team Name', '').strip()

        if not team_name or 'Lobby' in team_name:
            continue

        # Extract player profile links (not stats links, but profile links)
        for i in range(1, 4):
            discord = row.get(f'Rostered Player {i} Discord Username', '').strip()
            overstat_link = row.get(f'Rostered Player {i} Overstat Link', '').strip()

            if discord and overstat_link:
                # Convert to profile/overview URL
                if '/player/' in overstat_link:
                    player_part = overstat_link.split('/player/')[1].split('/')[0]
                    player_id = player_part.split('.')[0]

                    profile_url = f'https://overstat.gg/player/{player_id}/overview'

                    player_profiles.append({
                        'discord_name': discord,
                        'overstat_link': overstat_link,
                        'profile_url': profile_url,
                        'player_id': player_id
                    })

print(f"Found {len(player_profiles)} player profiles total")

# Remove duplicates
unique_profiles = {}
for p in player_profiles:
    if p['player_id'] not in unique_profiles:
        unique_profiles[p['player_id']] = p

print(f"Unique players: {len(unique_profiles)}")

# TEST: Only scrape first 5 players
test_profiles = list(unique_profiles.items())[:5]
print(f"\nTesting with first {len(test_profiles)} players...")
print("-"*70)

aliases_data = []
successful = 0
failed = 0

with OverstatScraper(headless=True, timeout=30000) as scraper:
    for i, (player_id, profile) in enumerate(test_profiles, 1):
        discord = profile['discord_name']
        url = profile['profile_url']

        print(f"\n{i}. Scraping {discord}...")

        try:
            page = scraper.browser.new_page()
            page.set_default_timeout(30000)
            page.goto(url, timeout=30000, wait_until='domcontentloaded')

            # Wait for content to load
            time.sleep(3)

            # Extract all in-game names
            names = page.evaluate('''
                () => {
                    const names = [];

                    // Find the "In-game Names" section using Vue data attribute
                    const namesDivs = document.querySelectorAll('[data-v-d5849fba].text-center');

                    namesDivs.forEach(div => {
                        const text = div.innerText.trim();
                        // Exclude the header and only get valid name entries
                        if (text && text.length > 0 && text.length < 100 && !text.includes('In-game Names')) {
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
                print(f"   ✓ Found {len(names)} aliases: {', '.join(names[:5])}{'...' if len(names) > 5 else ''}")
            else:
                failed += 1
                print(f"   ✗ NO ALIASES FOUND")

            # Rate limiting
            time.sleep(2)

        except Exception as e:
            failed += 1
            print(f"   ✗ ERROR - {e}")
            try:
                page.close()
            except:
                pass
            continue

print(f"\n{'='*70}")
print("TEST COMPLETE")
print("="*70)
print(f"Successful: {successful}/{len(test_profiles)}")
print(f"Failed: {failed}/{len(test_profiles)}")

if aliases_data:
    print(f"\nTotal aliases collected: {sum(p['alias_count'] for p in aliases_data)}")
    print(f"Average aliases per player: {sum(p['alias_count'] for p in aliases_data) / len(aliases_data):.1f}")

print(f"\n{'='*70}")
print("If this looks good, run the full scraper: python3 scrape_player_aliases.py")
