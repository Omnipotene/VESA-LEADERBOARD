#!/usr/bin/env python3
"""
Merge S12 Aliases into Main player_aliases.json
Intelligently combines S12 roster data with existing alias mappings
"""

import json
from collections import defaultdict

print("VESA - Merge S12 Aliases into Main Database")
print("="*70)

# Load existing alias database
with open('data/player_aliases.json', 'r') as f:
    existing_aliases = json.load(f)

print(f"Loaded existing alias database:")
print(f"  {len(existing_aliases)} players")
print(f"  {sum(len(p['aliases']) for p in existing_aliases)} total aliases")

# Load S12 aliases from CSV
with open('data/s12_aliases_from_csv.json', 'r') as f:
    s12_aliases = json.load(f)

print(f"\nLoaded S12 alias data:")
print(f"  {len(s12_aliases)} players")
print(f"  {sum(len(p['aliases']) for p in s12_aliases)} total aliases")

# Build lookup: discord_name -> player_data
existing_by_discord = {}
for player in existing_aliases:
    discord = player['discord_name'].lower().strip()
    existing_by_discord[discord] = player

# Merge statistics
new_players = 0
updated_players = 0
new_aliases = 0

# Process S12 aliases
for s12_player in s12_aliases:
    discord = s12_player['discord_name'].lower().strip()

    if discord in existing_by_discord:
        # Existing player - add new aliases
        existing_player = existing_by_discord[discord]
        existing_aliases_set = set(alias.lower() for alias in existing_player['aliases'])

        for alias in s12_player['aliases']:
            if alias.lower() not in existing_aliases_set:
                existing_player['aliases'].append(alias)
                new_aliases += 1

        updated_players += 1

    else:
        # New player - add to database
        existing_aliases.append({
            'discord_name': s12_player['discord_name'],
            'aliases': s12_player['aliases']
        })
        new_players += 1

# Sort by discord name
existing_aliases.sort(key=lambda x: x['discord_name'].lower())

# Save merged database
output_file = 'data/player_aliases.json'
with open(output_file, 'w') as f:
    json.dump(existing_aliases, f, indent=2)

print()
print("="*70)
print("MERGE COMPLETE")
print("="*70)
print(f"New players added: {new_players}")
print(f"Existing players updated: {updated_players}")
print(f"New aliases added: {new_aliases}")
print()
print(f"Final database statistics:")
print(f"  Total players: {len(existing_aliases)}")
print(f"  Total aliases: {sum(len(p['aliases']) for p in existing_aliases)}")
print()
print(f"✅ Saved merged database to: {output_file}")
print()
print("Next step: Re-run the rating pipeline to see improved matching")
print("  python3 combine_all_seasons.py")
print("  python3 apply_top_lobby_bonus_all_seasons.py")
print("  python3 team_seeding_combined.py")
