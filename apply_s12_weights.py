#!/usr/bin/env python3
"""
Apply lobby and day weights to Season 12 placement data
"""

import json
from src.weights import WeightingSystem

print("VESA League - Apply Weights to S12 Placements")
print("="*70)

# Load raw S12 data
with open('output/s12_placements_raw.json', 'r') as f:
    players = json.load(f)

print(f"Loaded {len(players)} player entries (with duplicates)")

# Initialize weight system
weights = WeightingSystem('config/weights.json')

# Apply weights to each entry
for player in players:
    raw_score = player['score']
    day = player['day']
    lobby = str(player['lobby'])

    # Calculate weighted score
    weighted_score = weights.calculate_weighted_score(raw_score, day, lobby)
    lobby_weight = weights.get_lobby_weight(lobby)
    day_weight = weights.get_day_weight(day)

    # Add weight info to player data
    player['lobby_weight'] = lobby_weight
    player['day_weight'] = day_weight
    player['weighted_score'] = weighted_score

# Save weighted data
output_file = 'output/s12_weighted_rankings.json'
with open(output_file, 'w') as f:
    json.dump(players, f, indent=2)

# Show summary
print(f"\n{'='*70}")
print("WEIGHTS APPLIED")
print("="*70)
print(f"Total entries: {len(players)}")
print(f"Saved to: {output_file}")

# Show weight distribution
from collections import defaultdict
lobby_counts = defaultdict(int)
day_counts = defaultdict(int)

for p in players:
    lobby_counts[p['lobby']] += 1
    day_counts[p['day']] += 1

print(f"\nLobby distribution:")
for lobby in sorted(lobby_counts.keys(), key=lambda x: float(x)):
    weight = weights.get_lobby_weight(str(lobby))
    print(f"  Lobby {lobby}: {lobby_counts[lobby]:3} entries (weight: {weight:.2f}x)")

print(f"\nDay distribution:")
for day in sorted(day_counts.keys()):
    weight = weights.get_day_weight(day)
    print(f"  Day {day}: {day_counts[day]:3} entries (weight: {weight:.2f}x)")

print(f"\n{'='*70}")
print("Next step: python3 deduplicate_s12.py")
