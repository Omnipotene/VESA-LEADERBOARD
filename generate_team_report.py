#!/usr/bin/env python3
"""
Generate a human-readable team ratings report with proper tier analysis
"""

import json
from collections import defaultdict

print("VESA League - Team Ratings Report")
print("="*80)

# Load team ratings
with open('output/team_ratings_combined.json', 'r') as f:
    teams = json.load(f)

print(f"Total teams: {len(teams)}\n")

# Analyze rating distribution
ratings = [t['team_rating'] for t in teams]
ratings.sort(reverse=True)

print("RATING DISTRIBUTION:")
print("-"*80)
print(f"Highest rating: {ratings[0]:.2f}")
print(f"Lowest rating: {ratings[-1]:.2f}")
print(f"Average rating: {sum(ratings)/len(ratings):.2f}")
print(f"Median rating: {ratings[len(ratings)//2]:.2f}")

# Show rating percentiles
percentiles = [10, 25, 50, 75, 90]
print(f"\nPercentiles:")
for p in percentiles:
    idx = int(len(ratings) * p / 100)
    print(f"  {p}th percentile: {ratings[idx]:.2f}")

# Suggest better tier thresholds based on actual data
print(f"\n{'='*80}")
print("SUGGESTED TIER THRESHOLDS (based on actual data):")
print("-"*80)

# Calculate natural breakpoints (quintiles for 5 tiers)
n_tiers = 5
tier_size = len(teams) // n_tiers
tier_names = ['S (Elite)', 'A (High)', 'B (Upper-Mid)', 'C (Mid)', 'D (Lower)']

print(f"\nOption 1: Equal team distribution (~{tier_size} teams per tier)")
for i, name in enumerate(tier_names):
    start_idx = i * tier_size
    end_idx = min((i + 1) * tier_size, len(ratings))
    threshold = ratings[start_idx]
    print(f"  Tier {name}: {threshold:.2f}+ (Teams #{start_idx+1}-{end_idx})")

print(f"\nOption 2: Rating-based thresholds")
print(f"  Tier S: 230+ (Elite)")
print(f"  Tier A: 210-229 (High)")
print(f"  Tier B: 190-209 (Upper-Mid)")
print(f"  Tier C: 180-189 (Mid)")
print(f"  Tier D: <180 (Lower)")

# Current tier distribution
print(f"\n{'='*80}")
print("CURRENT TIER DISTRIBUTION:")
print("-"*80)
tier_counts = defaultdict(int)
for team in teams:
    tier_counts[team['tier']] += 1

for tier in ['S', 'A', 'B', 'C', 'D']:
    count = tier_counts.get(tier, 0)
    pct = (count / len(teams)) * 100
    print(f"  Tier {tier}: {count:3} teams ({pct:5.1f}%)")

# Show top teams by tier
print(f"\n{'='*80}")
print("TOP 30 TEAMS BY RATING:")
print("="*80)
print(f"{'Rank':<5} {'Team':<30} {'Rating':<8} {'Tier':<5} {'Players'}")
print("-"*80)

for i, team in enumerate(teams[:30], 1):
    players_found = f"{len(team['found_players'])}/3"
    print(f"{i:<5} {team['team_name']:<30} {team['team_rating']:<8.2f} {team['tier']:<5} {players_found}")

# Show teams with all players found vs not found
print(f"\n{'='*80}")
print("DATA QUALITY ANALYSIS:")
print("-"*80)

all_found = [t for t in teams if len(t['found_players']) == 3]
partial_found = [t for t in teams if 0 < len(t['found_players']) < 3]
none_found = [t for t in teams if len(t['found_players']) == 0]

print(f"Teams with all 3 players found: {len(all_found)} ({len(all_found)/len(teams)*100:.1f}%)")
print(f"Teams with 1-2 players found: {len(partial_found)} ({len(partial_found)/len(teams)*100:.1f}%)")
print(f"Teams with 0 players found: {len(none_found)} ({len(none_found)/len(teams)*100:.1f}%)")

print(f"\nAverage rating by data quality:")
print(f"  All 3 found: {sum(t['team_rating'] for t in all_found)/len(all_found):.2f}")
print(f"  1-2 found: {sum(t['team_rating'] for t in partial_found)/len(partial_found):.2f}" if partial_found else "  1-2 found: N/A")
print(f"  0 found (all defaults): {sum(t['team_rating'] for t in none_found)/len(none_found):.2f}" if none_found else "  0 found: N/A")

# Show teams that might be misrated (all defaults but should be higher)
print(f"\n{'='*80}")
print("POTENTIALLY MISRATED TEAMS (0 players found, likely new/renamed):")
print("-"*80)
print(f"{'Team':<30} {'Rating':<8} {'Players'}")
print("-"*80)

for team in none_found[:20]:
    players = f"{team['player1']}, {team['player2']}, {team['player3']}"
    print(f"{team['team_name']:<30} {team['team_rating']:<8.2f} {players[:45]}")

# Export summary stats
summary = {
    'total_teams': len(teams),
    'rating_stats': {
        'highest': ratings[0],
        'lowest': ratings[-1],
        'average': sum(ratings)/len(ratings),
        'median': ratings[len(ratings)//2]
    },
    'tier_distribution': dict(tier_counts),
    'data_quality': {
        'all_found': len(all_found),
        'partial_found': len(partial_found),
        'none_found': len(none_found)
    }
}

with open('output/team_ratings_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\n{'='*80}")
print("✅ Summary saved to: output/team_ratings_summary.json")
