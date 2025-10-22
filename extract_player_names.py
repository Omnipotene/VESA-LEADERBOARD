#!/usr/bin/env python3
"""
Extract in-game player names from Overstat URLs in the roster CSV
"""

import csv
import json
import urllib.parse

print("VESA League - Extract Player Names from Overstat URLs")
print("="*70)

# Function to extract player name from Overstat URL
def extract_name_from_url(url):
    """
    Extract player name from URL like:
    https://overstat.gg/player/77595.super%20sub%20lumdum/overview
    Returns: "super sub lumdum"
    """
    if not url or 'overstat.gg/player/' not in url:
        return None

    try:
        # Extract the part after /player/
        player_part = url.split('/player/')[1].split('/')[0]

        # If there's a dot, the name is after it
        if '.' in player_part:
            encoded_name = player_part.split('.', 1)[1]
            # URL decode the name (handles %20 etc)
            name = urllib.parse.unquote(encoded_name)
            return name.strip()
        else:
            # No name in URL, just ID
            return None
    except:
        return None

# Load roster CSV and extract names
player_mapping = []  # List of {discord_name, overstat_url, ingame_name}
seen_players = set()  # Track unique discord names to avoid duplicates

with open('data/rosters.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        team_name = row.get('Team Name', '').strip()

        if not team_name or 'Lobby' in team_name:
            continue

        # Process all 3 rostered players
        for i in range(1, 4):
            discord_name = row.get(f'Rostered Player {i} Discord Username', '').strip()
            overstat_url = row.get(f'Rostered Player {i} Overstat Link', '').strip()

            if discord_name and overstat_url:
                ingame_name = extract_name_from_url(overstat_url)

                # Only add if we haven't seen this discord name yet
                if discord_name.lower() not in seen_players:
                    player_mapping.append({
                        'team': team_name,
                        'discord_name': discord_name,
                        'overstat_url': overstat_url,
                        'ingame_name': ingame_name if ingame_name else discord_name  # Fallback to discord name
                    })
                    seen_players.add(discord_name.lower())

        # Process substitute players from "Sub Overstat" columns
        for col in row.keys():
            if 'Sub Overstat' in col:
                overstat_url = row.get(col, '').strip()

                if overstat_url.startswith('https://overstat.gg/player/'):
                    # Extract name from URL
                    ingame_name = extract_name_from_url(overstat_url)

                    # For subs, we might not have a discord name, so use the ingame name as identifier
                    if ingame_name:
                        # Use ingame name as discord name for subs (best we can do)
                        discord_name = ingame_name

                        # Only add if not already seen
                        if discord_name.lower() not in seen_players:
                            player_mapping.append({
                                'team': team_name,
                                'discord_name': discord_name,
                                'overstat_url': overstat_url,
                                'ingame_name': ingame_name
                            })
                            seen_players.add(discord_name.lower())

print(f"Extracted {len(player_mapping)} player name mappings")

# Show some examples
print(f"\nSample mappings:")
print("-"*70)
print(f"{'Discord Name':<20} {'In-Game Name':<25} {'Match?'}")
print("-"*70)

for mapping in player_mapping[:10]:
    discord = mapping['discord_name']
    ingame = mapping['ingame_name']
    match = "✓" if ingame and ingame != discord else "X"
    print(f"{discord:<20} {ingame:<25} {match}")

# Save mapping
output_file = "data/player_name_mapping.json"
with open(output_file, 'w') as f:
    json.dump(player_mapping, f, indent=2)

print(f"\n✅ Player name mapping saved to: {output_file}")
print("\nNow we can use in-game names to match against the player database!")
