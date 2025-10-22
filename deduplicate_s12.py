#!/usr/bin/env python3
"""
Deduplicate S12 players - keep best weighted performance for each unique player
"""

import json
from collections import defaultdict

print("VESA League - S12 Player Deduplication")
print("="*70)

# Load weighted data
with open('output/s12_weighted_rankings.json', 'r') as f:
    all_entries = json.load(f)

print(f"Loaded {len(all_entries)} player entries")

# Group by player name (case-insensitive)
player_performances = defaultdict(list)

for entry in all_entries:
    player_name = entry['player_name'].lower().strip()
    player_performances[player_name].append(entry)

print(f"Found {len(player_performances)} unique players")

# Keep best performance for each player
unique_players = []

for player_name, performances in player_performances.items():
    # Sort by weighted score (highest first)
    best_performance = max(performances, key=lambda x: x['weighted_score'])

    # Count appearances
    appearances = len(performances)

    # Add appearance count to player data
    best_performance['appearances'] = appearances
    best_performance['all_scores'] = [p['score'] for p in performances]
    best_performance['all_weighted_scores'] = [p['weighted_score'] for p in performances]

    unique_players.append(best_performance)

# Sort by weighted score
unique_players_sorted = sorted(unique_players, key=lambda x: x['weighted_score'], reverse=True)

# Assign divisions (simplified - based on weighted score)
for i, player in enumerate(unique_players_sorted, 1):
    player['rank'] = i

    # Simplified division assignment (you can adjust these thresholds)
    if i <= 60:
        player['division'] = 'Pinnacle'
    elif i <= 120:
        player['division'] = 'Vanguard'
    elif i <= 240:
        player['division'] = 'Ascendant'
    elif i <= 360:
        player['division'] = 'Emergent'
    elif i <= 480:
        player['division'] = 'Challengers'
    else:
        player['division'] = 'Tendies'

# Save deduplicated data
output_file = 'output/s12_unique_players.json'
with open(output_file, 'w') as f:
    json.dump(unique_players_sorted, f, indent=2)

# Show summary
print(f"\n{'='*70}")
print("DEDUPLICATION COMPLETE")
print("="*70)
print(f"Original entries: {len(all_entries)}")
print(f"Unique players: {len(unique_players_sorted)}")
print(f"Duplicates removed: {len(all_entries) - len(unique_players_sorted)}")
print(f"Saved to: {output_file}")

# Show top 20
print(f"\n{'='*70}")
print("TOP 20 PLAYERS (Weighted Scores):")
print("="*70)
print(f"{'Rank':<5} {'Player':<20} {'Division':<12} {'Score':<8} {'Appearances'}")
print("-"*70)

for i, p in enumerate(unique_players_sorted[:20], 1):
    print(f"{i:<5} {p['player_name']:<20} {p['division']:<12} {p['weighted_score']:<8.2f} {p['appearances']}")

# Division distribution
from collections import Counter
div_counts = Counter(p['division'] for p in unique_players_sorted)

print(f"\n{'='*70}")
print("DIVISION DISTRIBUTION:")
print("="*70)
for div in ['Pinnacle', 'Vanguard', 'Ascendant', 'Emergent', 'Challengers', 'Tendies']:
    count = div_counts.get(div, 0)
    print(f"  {div:<12}: {count:3} players")

print(f"\n{'='*70}")
print("Next step: python3 custom_scoring_s12.py (for 50/50 individual scoring)")
