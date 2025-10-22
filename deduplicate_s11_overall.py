#!/usr/bin/env python3
"""
Deduplicate S11 overall data using player aliases
(No weights needed - already aggregated overall standings)
"""

import json
from collections import defaultdict

print("VESA League - S11 Overall Deduplication with Aliases")
print("="*70)

# Load S11 overall data
with open('output/s11_overall_raw.json', 'r') as f:
    all_entries = json.load(f)

print(f"Loaded {len(all_entries)} player entries")

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

# Group by canonical identity
player_performances = defaultdict(list)

for entry in all_entries:
    ingame_name = entry['player_name']
    ingame_lower = ingame_name.lower().strip()
    
    if ingame_lower in name_to_discord:
        canonical = name_to_discord[ingame_lower]
    else:
        canonical = ingame_lower
    
    player_performances[canonical].append(entry)

print(f"Grouped into {len(player_performances)} unique players")

# Keep best performance for each
unique_players = []
for canonical_id, performances in player_performances.items():
    best_performance = max(performances, key=lambda x: x['score'])
    best_performance['all_names_used'] = list(set(p['player_name'] for p in performances))
    unique_players.append(best_performance)

# Sort by score
unique_players_sorted = sorted(unique_players, key=lambda x: x['score'], reverse=True)

# Save
output_file = 'output/s11_unique_players.json'
with open(output_file, 'w') as f:
    json.dump(unique_players_sorted, f, indent=2)

print(f"\nSaved {len(unique_players_sorted)} unique players to: {output_file}")
print(f"✅ S11 DEDUPLICATION COMPLETE")
print("\nNext: Apply 50/50 scoring")
