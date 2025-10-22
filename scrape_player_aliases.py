#!/usr/bin/env python3
"""
Scrape player profile pages to get complete name history/aliases
"""

import csv
import json
import time
from src.scraper import OverstatScraper

print("VESA League - Player Alias Scraper")
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
                # e.g., https://overstat.gg/player/749175.Lau/overview
                # Extract player ID
                if '/player/' in overstat_link:
                    # Get the part after /player/
                    player_part = overstat_link.split('/player/')[1].split('/')[0]
                    player_id = player_part.split('.')[0]  # Get ID before the dot

                    profile_url = f'https://overstat.gg/player/{player_id}/overview'

                    player_profiles.append({
                        'discord_name': discord,
                        'overstat_link': overstat_link,
                        'profile_url': profile_url,
                        'player_id': player_id
                    })

print(f"Found {len(player_profiles)} player profiles to scrape")

# Remove duplicates (same player might be in roster twice)
unique_profiles = {}
for p in player_profiles:
    if p['player_id'] not in unique_profiles:
        unique_profiles[p['player_id']] = p

print(f"Unique players: {len(unique_profiles)}")

# Scrape aliases
print(f"\nScraping player aliases...")
print("-"*70)

aliases_data = []
successful = 0
failed = 0

with OverstatScraper(headless=True, timeout=15000) as scraper:
    for i, (player_id, profile) in enumerate(unique_profiles.items(), 1):
        discord = profile['discord_name']
        url = profile['profile_url']

        if i % 10 == 0:
            print(f"Progress: {i}/{len(unique_profiles)}")

        try:
            page = scraper.browser.new_page()
            page.set_default_timeout(15000)
            page.goto(url, timeout=15000, wait_until='domcontentloaded')

            # Wait for the specific selector instead of arbitrary sleep
            page.wait_for_selector('[data-v-d5849fba].text-center', timeout=10000)

            # Extract all in-game names
            names = page.evaluate('''
                () => {
                    const names = [];

                    // Find the "In-game Names" section using Vue data attribute
                    const namesDivs = document.querySelectorAll('[data-v-d5849fba].text-center');

                    namesDivs.forEach(div => {
                        const text = div.innerText.trim();
                        const textUpper = text.toUpperCase();
                        // Exclude headers and stats labels
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

            # Reduced rate limiting
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
print(f"Successful: {successful}/{len(unique_profiles)}")
print(f"Failed: {failed}/{len(unique_profiles)}")

# Save aliases
output_file = "data/player_aliases.json"
with open(output_file, 'w') as f:
    json.dump(aliases_data, f, indent=2)

print(f"Saved to: {output_file}")

# Show statistics
total_aliases = sum(p['alias_count'] for p in aliases_data)
avg_aliases = total_aliases / len(aliases_data) if aliases_data else 0

print(f"\nTotal aliases collected: {total_aliases}")
print(f"Average aliases per player: {avg_aliases:.1f}")

print(f"\n{'='*70}")
print("Next step: Re-run team seeding with alias matching")
