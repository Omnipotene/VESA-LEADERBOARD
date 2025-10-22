#!/usr/bin/env python3
"""
Custom scoring system: 70% individual performance, 30% team placement
"""

import json
from datetime import datetime
import csv

# Load deduplicated player data
with open('output/unique_players_ranked.json', 'r') as f:
    players = json.load(f)

print("VESA League - Custom Individual Scoring (50/50 Split)")
print("="*70)
print("Formula: 65% Individual Stats + 35% Team Placement")
print("="*70)

# Calculate custom scores
for player in players:
    # Individual component (65%)
    # We'll create an "individual score" from kills and damage
    # Formula: (Kills × 10) + (Damage / 100)
    # This gives roughly equal weight to kills and damage
    individual_score = (player['kills'] * 10) + (player['damage'] / 100)
    individual_component = individual_score * 0.65

    # Team placement component (35%)
    # This is the weighted team score (already accounts for lobby difficulty)
    team_component = player['weighted_score'] * 0.35

    # Combined score
    final_score = individual_component + team_component

    # Store all components for transparency
    player['individual_score'] = individual_score
    player['individual_component'] = individual_component
    player['team_component'] = team_component
    player['final_score'] = final_score

# Sort by final score
players_sorted = sorted(players, key=lambda x: x['final_score'], reverse=True)

# Display top 20 with breakdown
print(f"\nTOP 20 - Custom Scoring Breakdown:")
print("="*70)
print(f"{'Rank':<5} {'Player':<20} {'Final':<10} {'Ind(65%)':<10} {'Team(35%)':<10}")
print("-"*70)

for i, p in enumerate(players_sorted[:20], 1):
    print(f"{i:<5} {p['player_name']:<20} {p['final_score']:<10.2f} "
          f"{p['individual_component']:<10.2f} {p['team_component']:<10.2f}")

# Show detailed breakdown for top 5
print(f"\n{'='*70}")
print("TOP 5 - DETAILED BREAKDOWN:")
print("="*70)

for i, p in enumerate(players_sorted[:5], 1):
    print(f"\n{i}. {p['player_name']} ({p['division']})")
    print(f"   Individual Stats:")
    print(f"     Kills: {p['kills']} × 10 = {p['kills'] * 10:.0f}")
    print(f"     Damage: {p['damage']:,} ÷ 100 = {p['damage'] / 100:.0f}")
    print(f"     Individual Score: {p['individual_score']:.2f}")
    print(f"   Individual Component (65%): {p['individual_component']:.2f}")
    print(f"   Team Component (35%): {p['team_component']:.2f} (from weighted score: {p['weighted_score']:.2f})")
    print(f"   ═══════════════════════════════════")
    print(f"   FINAL SCORE: {p['final_score']:.2f}")

# Export to CSV
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_file = f"output/vesa_individual_leaderboard_{timestamp}.csv"

with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)

    writer.writerow([
        'Rank',
        'Player Name',
        'Division',
        'Final Score (50/50)',
        'Individual Score',
        'Team Score',
        'Kills',
        'Damage',
        'Lobby Weight'
    ])

    for rank, p in enumerate(players_sorted, start=1):
        writer.writerow([
            rank,
            p['player_name'],
            p['division'],
            f"{p['final_score']:.2f}",
            f"{p['individual_score']:.2f}",
            f"{p['weighted_score']:.2f}",
            p['kills'],
            p['damage'],
            p['lobby_weight']
        ])

print(f"\n{'='*70}")
print("✅ EXPORT COMPLETE")
print("="*70)
print(f"Exported to: {csv_file}")

# Simple version
simple_csv = f"output/vesa_individual_simple_{timestamp}.csv"

with open(simple_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)

    writer.writerow([
        'Rank',
        'Player Name',
        'Total Points',
        'Kills',
        'Damage'
    ])

    for rank, p in enumerate(players_sorted, start=1):
        writer.writerow([
            rank,
            p['player_name'],
            f"{p['final_score']:.2f}",
            p['kills'],
            p['damage']
        ])

print(f"Simple version: {simple_csv}")

# Compare with old ranking
print(f"\n{'='*70}")
print("RANKING CHANGES (Top 10)")
print("="*70)
print("Comparing: Pure Team Score vs. 50/50 Individual")
print("-"*70)

# Create mapping of old rankings
old_ranking = {p['player_name']: i+1 for i, p in enumerate(players, start=1)}

print(f"{'Player':<20} {'Old Rank':<10} {'New Rank':<10} {'Change'}")
print("-"*70)

for i, p in enumerate(players_sorted[:20], 1):
    old_rank = old_ranking.get(p['player_name'], '?')
    change = old_rank - i if isinstance(old_rank, int) else '?'
    change_str = f"+{change}" if isinstance(change, int) and change > 0 else str(change)

    print(f"{p['player_name']:<20} {old_rank:<10} {i:<10} {change_str}")

print(f"\n{'='*70}")
print("This leaderboard now highlights individual performance!")
print("Teammates will have different rankings based on their kills/damage.")
print("="*70)
