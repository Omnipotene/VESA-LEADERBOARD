#!/usr/bin/env python3
"""
Re-deduplicate S12 data using player aliases
Combines entries for the same player under different names
"""

import json
from collections import defaultdict

print("VESA League - S12 Deduplication with Aliases")
print("="*70)

# Load weighted S12 data (before original deduplication)
with open('output/s12_weighted_rankings.json', 'r') as f:
    all_entries = json.load(f)

print(f"Loaded {len(all_entries)} total player entries")

# Load aliases
with open('data/player_aliases.json', 'r') as f:
    aliases_data = json.load(f)

# Build alias lookup: any_name -> canonical_discord_name
name_to_discord = {}
for player in aliases_data:
    discord = player['discord_name'].lower().strip()
    
    # Map all aliases to this discord name
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
    
    # Find canonical identity
    if ingame_lower in name_to_discord:
        canonical = name_to_discord[ingame_lower]
    else:
        # No alias found, use the name itself as canonical
        canonical = ingame_lower
    
    player_performances[canonical].append(entry)

print(f"Grouped into {len(player_performances)} unique player identities")

# For each player, keep their best performance
unique_players = []
merged_count = 0

for canonical_id, performances in player_performances.items():
    if len(performances) > 1:
        merged_count += 1
    
    # Sort by weighted score, keep best
    best_performance = max(performances, key=lambda x: x['weighted_score'])
    best_performance['appearances'] = len(performances)
    
    # Track all names used
    all_names = list(set(p['player_name'] for p in performances))
    best_performance['all_names_used'] = all_names
    
    unique_players.append(best_performance)

# Sort by weighted score
unique_players_sorted = sorted(unique_players, key=lambda x: x['weighted_score'], reverse=True)

print(f"\nResults:")
print(f"  Total entries: {len(all_entries)}")
print(f"  Unique players: {len(unique_players)}")
print(f"  Duplicates removed: {len(all_entries) - len(unique_players)}")
print(f"  Players with multiple names: {merged_count}")

# Save
output_file = 'output/s12_unique_players_v2.json'
with open(output_file, 'w') as f:
    json.dump(unique_players_sorted, f, indent=2)

print(f"\nSaved to: {output_file}")

# Show examples of merged players
print(f"\nExamples of players with multiple names:")
multi_name_players = [p for p in unique_players_sorted if len(p.get('all_names_used', [])) > 1]
for i, player in enumerate(multi_name_players[:10], 1):
    names = player.get('all_names_used', [])
    print(f"{i}. {player['player_name']} (best name)")
    print(f"   All names used: {', '.join(names)}")
    print(f"   Appearances: {player['appearances']}, Best score: {player['weighted_score']:.2f}")

print(f"\n{'='*70}")
print("✅ DEDUPLICATION COMPLETE")
print("="*70)
print("Next step: Re-run custom scoring with new deduplicated data")
print("  python3 custom_scoring_s12_v2.py")
