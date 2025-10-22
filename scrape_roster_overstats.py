#!/usr/bin/env python3
"""
Scrape valid Overstat URLs from roster CSV to get real in-game names
"""

import csv
import json
import re
import time
from collections import defaultdict
from src.scraper import OverstatScraper

print("VESA League - Roster Overstat Scraper")
print("="*70)

# Load existing mapping
with open('data/player_name_mapping.json', 'r') as f:
    existing_mapping = json.load(f)

print(f"Loaded {len(existing_mapping)} existing mappings")

# Create lookup: discord_name -> mapping entry
existing_lookup = {entry['discord_name'].lower().strip(): entry for entry in existing_mapping}

# Extract Overstat URLs from roster CSV
players_to_scrape = []
invalid_urls = []

with open('data/rosters.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        team_name = row.get('Team Name', '').strip()

        # Skip header rows or empty teams
        if not team_name or 'Lobby' in team_name or team_name == '':
            continue

        # Process each of 3 players
        for i in range(1, 4):
            discord = row.get(f'Rostered Player {i} Discord Username', '').strip()
            overstat_url = row.get(f'Rostered Player {i} Overstat Link', '').strip()

            if not discord:
                continue

            discord_lower = discord.lower().strip()

            # Check if URL is valid Overstat link
            if overstat_url.startswith('https://overstat.gg/player/'):
                # Check if we already have a good mapping for this player
                if discord_lower in existing_lookup:
                    existing = existing_lookup[discord_lower]
                    # If existing mapping has same URL and ingame_name != discord_name, skip
                    if existing.get('overstat_url') == overstat_url and existing['ingame_name'] != discord:
                        continue

                players_to_scrape.append({
                    'team': team_name,
                    'discord_name': discord,
                    'overstat_url': overstat_url
                })
            else:
                # Invalid or missing URL
                if overstat_url and overstat_url != discord:
                    invalid_urls.append({
                        'team': team_name,
                        'discord_name': discord,
                        'invalid_url': overstat_url
                    })

print(f"\nFound {len(players_to_scrape)} players with valid Overstat URLs to scrape")
print(f"Found {len(invalid_urls)} players with invalid/missing URLs")

# Show sample of invalid URLs
if invalid_urls:
    print(f"\nSample invalid URLs (first 10):")
    for entry in invalid_urls[:10]:
        print(f"  {entry['team']}: {entry['discord_name']} → {entry['invalid_url']}")

# Save invalid URLs for manual review
with open('output/invalid_overstat_urls.json', 'w') as f:
    json.dump(invalid_urls, f, indent=2)

print(f"\nSaved invalid URLs to: output/invalid_overstat_urls.json")

# Deduplicate by URL (multiple teams might reference same player)
unique_urls = {}
for entry in players_to_scrape:
    url = entry['overstat_url']
    if url not in unique_urls:
        unique_urls[url] = entry

print(f"Deduped to {len(unique_urls)} unique Overstat URLs to scrape\n")

# Scrape each player profile
print("Starting Overstat profile scraping...")
print("-"*70)

scraped_data = []
errors = []

with OverstatScraper(headless=True, timeout=30000) as scraper:
    # Create a page from the browser
    page = scraper.browser.new_page()
    page.set_default_timeout(30000)

    for i, (url, entry) in enumerate(unique_urls.items(), 1):
        try:
            print(f"[{i}/{len(unique_urls)}] {entry['discord_name']}...", end=' ')

            # Navigate to player overview page
            page.goto(url, wait_until='domcontentloaded')

            # Wait for page to load
            time.sleep(1)

            # Extract player name from the page
            # Try multiple selectors
            player_name = None

            # Method 1: Try h1 with player name
            try:
                player_name_elem = page.query_selector('h1')
                if player_name_elem:
                    player_name = player_name_elem.inner_text().strip()
            except:
                pass

            # Method 2: Try meta tag
            if not player_name:
                try:
                    player_name = page.eval_on_selector('meta[property="og:title"]', 'el => el.content')
                    if player_name:
                        # Clean up title (remove " - Overstat" suffix)
                        player_name = player_name.split(' - ')[0].strip()
                except:
                    pass

            # Method 3: Extract from URL (last resort)
            if not player_name:
                # URL format: https://overstat.gg/player/ID.NAME/overview
                match = re.search(r'/player/\d+\.([^/]+)/', url)
                if match:
                    player_name = match.group(1)
                    # URL decode
                    player_name = player_name.replace('%20', ' ')

            if player_name:
                scraped_data.append({
                    'team': entry['team'],
                    'discord_name': entry['discord_name'],
                    'overstat_url': url,
                    'ingame_name': player_name
                })
                print(f"✓ {player_name}")
            else:
                errors.append({
                    'discord_name': entry['discord_name'],
                    'url': url,
                    'error': 'Could not extract player name'
                })
                print("✗ Could not extract name")

            # Rate limiting
            time.sleep(0.5)

        except Exception as e:
            errors.append({
                'discord_name': entry['discord_name'],
                'url': url,
                'error': str(e)
            })
            print(f"✗ ERROR: {str(e)}")

    page.close()

print("\n" + "="*70)
print(f"Scraping complete!")
print(f"  Successfully scraped: {len(scraped_data)}")
print(f"  Errors: {len(errors)}")

# Merge with existing mapping
# Build updated mapping
discord_to_new_data = {entry['discord_name'].lower().strip(): entry for entry in scraped_data}

updated_mapping = []
updated_count = 0
kept_count = 0

# First, update existing entries
for existing_entry in existing_mapping:
    discord_lower = existing_entry['discord_name'].lower().strip()

    if discord_lower in discord_to_new_data:
        # Update with new scraped data
        new_entry = discord_to_new_data[discord_lower]
        updated_mapping.append(new_entry)
        updated_count += 1
        # Remove from dict so we know it's processed
        del discord_to_new_data[discord_lower]
    else:
        # Keep existing entry
        updated_mapping.append(existing_entry)
        kept_count += 1

# Add any new entries that weren't in existing mapping
for new_entry in discord_to_new_data.values():
    updated_mapping.append(new_entry)

print(f"\nMapping update summary:")
print(f"  Updated existing entries: {updated_count}")
print(f"  Kept unchanged entries: {kept_count}")
print(f"  New entries added: {len(discord_to_new_data)}")
print(f"  Total entries: {len(updated_mapping)}")

# Save updated mapping
with open('data/player_name_mapping.json', 'w') as f:
    json.dump(updated_mapping, f, indent=2)

print(f"\n✅ Updated mapping saved to: data/player_name_mapping.json")

# Save errors for review
if errors:
    with open('output/roster_scrape_errors.json', 'w') as f:
        json.dump(errors, f, indent=2)
    print(f"⚠️  Errors saved to: output/roster_scrape_errors.json")

# Show examples of updated mappings
print(f"\nExample updated mappings (first 10):")
for entry in scraped_data[:10]:
    print(f"  {entry['discord_name']} → {entry['ingame_name']}")

print(f"\nNext step: Re-run team seeding")
print("  python3 team_seeding_combined.py")
