#!/usr/bin/env python3
"""
Apply lobby and day weights to S11 placement data
"""

import json
from src.weights import WeightingSystem

print("VESA League - S11 Weight Application")
print("="*70)

# Load S11 raw data
with open('output/s11_placements_raw.json', 'r') as f:
    players = json.load(f)

print(f"Loaded {len(players)} player entries\n")

# Load weighting system
weights = WeightingSystem('config/weights.json')

# Apply weights
for player in players:
    raw_score = player['score']
    day = player['day']
    lobby = str(player['lobby'])
    
    weighted_score = weights.calculate_weighted_score(raw_score, day, lobby)
    player['weighted_score'] = weighted_score

# Save
output_file = 'output/s11_weighted_rankings.json'
with open(output_file, 'w') as f:
    json.dump(players, f, indent=2)

print(f"✅ Weights applied to {len(players)} entries")
print(f"Saved to: {output_file}")
print(f"\nNext step: Deduplicate with aliases")
print("  python3 deduplicate_s11_with_aliases.py")
