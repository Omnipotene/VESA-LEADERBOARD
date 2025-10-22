#!/usr/bin/env python3
"""
Infer S11 division placements based on ranking distribution
Since we don't have explicit division data for S11, we'll estimate based on:
- Top 40 players (~30%) -> Pinnacle I (score 10)
- Next 30 players (~23%) -> Pinnacle II (score 8)
- Next 30 players (~23%) -> Vanguard (score 8)
- Remaining players -> Lower divisions (score 6, 4)

This is a reasonable approximation based on typical competitive distribution
"""

import json

print("VESA League - S11 Division Inference")
print("="*70)

# Load S11 player rankings
with open('output/s11_players_ranked.json', 'r') as f:
    s11_players = json.load(f)

total_players = len(s11_players)
print(f"Total S11 players: {total_players}\n")

# Define division breakpoints (based on rank)
# Top ~30% Pinnacle I, next ~23% Pinnacle II, next ~23% Vanguard, rest lower
PINNACLE_I_CUTOFF = 40  # Top 40 players
PINNACLE_II_CUTOFF = 70  # Next 30 players
VANGUARD_CUTOFF = 100    # Next 30 players
ASCENDANT_CUTOFF = 120   # Next 20 players
# Rest are lower tiers

division_counts = {
    'Pinnacle I': 0,
    'Pinnacle II': 0,
    'Vanguard': 0,
    'Ascendant': 0,
    'Challengers': 0
}

# Build player -> division mapping
s11_division_data = []

for player in s11_players:
    name = player['player_name'].lower().strip()
    rank = player.get('rank', 999)

    # Assign division based on rank
    if rank <= PINNACLE_I_CUTOFF:
        division = 'Pinnacle I'
        division_score = 10
    elif rank <= PINNACLE_II_CUTOFF:
        division = 'Pinnacle II'
        division_score = 8
    elif rank <= VANGUARD_CUTOFF:
        division = 'Vanguard'
        division_score = 8
    elif rank <= ASCENDANT_CUTOFF:
        division = 'Ascendant'
        division_score = 6
    else:
        division = 'Challengers'
        division_score = 6

    s11_division_data.append({
        'player_name': name,
        'rank': rank,
        'division': division,
        'division_score': division_score,
        'season': 'S11'
    })

    division_counts[division] += 1

# Save to file
output_file = 'data/s11_inferred_divisions.json'
with open(output_file, 'w') as f:
    json.dump(s11_division_data, f, indent=2)

print("Division Distribution:")
print("-"*70)
for div, count in division_counts.items():
    pct = (count / total_players * 100) if total_players > 0 else 0
    score = 10 if div == 'Pinnacle I' else (8 if div in ['Pinnacle II', 'Vanguard'] else 6)
    print(f"  {div:20} {count:3} players ({pct:5.1f}%) - Score: {score}")

print(f"\n{'='*70}")
print(f"✅ S11 divisions inferred and saved to: {output_file}")
print(f"\nTop 10 S11 players:")
print("-"*70)
for p in s11_division_data[:10]:
    print(f"  {p['rank']:3}. {p['player_name']:30} {p['division']:15} (score: {p['division_score']})")

print(f"\n{'='*70}")
print("Next step: Update extract_division_history.py to use this data")
