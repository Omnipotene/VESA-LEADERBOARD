#!/usr/bin/env python3
"""
Apply player name aliases before deduplication
"""

import json

# Load aliases
with open('config/player_aliases.json', 'r') as f:
    alias_config = json.load(f)

aliases = alias_config.get('aliases', {})

# Load player data
with open('output/weighted_rankings.json', 'r') as f:
    players = json.load(f)

print("VESA League - Player Alias Resolution")
print("="*70)
print(f"Loaded {len(aliases)} aliases")

# Apply aliases
changes = 0
for player in players:
    old_name = player['player_name']
    if old_name in aliases:
        new_name = aliases[old_name]
        player['player_name'] = new_name
        player['original_name'] = old_name
        changes += 1
        print(f"  '{old_name}' → '{new_name}'")

print(f"\nApplied {changes} name changes")

# Save updated data
with open('output/weighted_rankings_aliased.json', 'w') as f:
    json.dump(players, f, indent=2)

print("✅ Saved to: output/weighted_rankings_aliased.json")
print("\nNow run: python3 deduplicate_and_export.py")
