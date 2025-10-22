#!/usr/bin/env python3
"""
Deduplicate S11 data using player aliases
"""

import json
from collections import defaultdict

print("VESA League - S11 Deduplication with Aliases")
print("="*70)

# Load weighted S11 data
with open('output/s11_weighted_rankings.json', 'r') as f:
    all_entries = json.load(f)

print(f"Loaded {len(all_entries)} total player entries")

# Load aliases
with open('data/player_aliases.json', 'r') as f:
    aliases_data = json.load(f)

# Build alias lookup
name_to_discord = {}
for player in aliases_data:
    discord = player['discord_name'].lower().strip()
    for alias in player['aliases']:
        alias_lower = alias.lower().strip()
        if alias_lower:
            name_to_discord[alias_lower] = discord

print(f"Loaded {len(name_to_discord)} alias mappings")

# Group entries by canonical player identity
player_performances = defaultdict(list)

for entry in all_entries:
    ingame_name = entry['player_name']
    ingame_lower = ingame_name.lower().strip()
    
    if ingame_lower in name_to_discord:
        canonical = name_to_discord[ingame_lower]
    else:
        canonical = ingame_lower
    
    player_performances[canonical].append(entry)

print(f"Grouped into {len(player_performances)} unique player identities")

# Keep best performance for each player
unique_players = []
for canonical_id, performances in player_performances.items():
    best_performance = max(performances, key=lambda x: x['weighted_score'])
    best_performance['appearances'] = len(performances)
    best_performance['all_names_used'] = list(set(p['player_name'] for p in performances))
    unique_players.append(best_performance)

# Sort by weighted score
unique_players_sorted = sorted(unique_players, key=lambda x: x['weighted_score'], reverse=True)

print(f"\nResults:")
print(f"  Total entries: {len(all_entries)}")
print(f"  Unique players: {len(unique_players)}")
print(f"  Duplicates removed: {len(all_entries) - len(unique_players)}")

# Save
output_file = 'output/s11_unique_players.json'
with open(output_file, 'w') as f:
    json.dump(unique_players_sorted, f, indent=2)

print(f"\nSaved to: {output_file}")
print(f"\n{'='*70}")
print("✅ S11 DEDUPLICATION COMPLETE")
print("="*70)
print("Next step: Apply custom scoring")
print("  python3 custom_scoring_s11.py")
