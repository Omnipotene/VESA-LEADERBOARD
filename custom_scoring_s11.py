#!/usr/bin/env python3
"""
Apply 50/50 custom scoring to S11 data:
65% Individual (kills & damage) + 35% Team placement (weighted score)
"""

import json

print("VESA League - S11 Custom Scoring (50/50 Split)")
print("="*70)
print("Formula: 65% Individual Stats + 35% Team Placement")
print("="*70)

# Load deduplicated S11 player data
with open('output/s11_unique_players.json', 'r') as f:
    players = json.load(f)

print(f"Loaded {len(players)} unique players\n")

# Calculate custom scores
for player in players:
    # Individual component (65%)
    individual_score = (player['kills'] * 10) + (player['damage'] / 100)
    individual_component = individual_score * 0.65

    # Team placement component (35%)
    # S11 overall doesn't have weighted_score, use raw score
    team_component = player['score'] * 0.65

    # Combined score
    final_score = individual_component + team_component

    # Store all components
    player['individual_score'] = individual_score
    player['individual_component'] = individual_component
    player['team_component'] = team_component
    player['final_score'] = final_score

# Sort by final score
players_sorted = sorted(players, key=lambda x: x['final_score'], reverse=True)

# Update ranks
for i, player in enumerate(players_sorted, 1):
    player['rank'] = i

# Save
output_file = 'output/s11_players_ranked.json'
with open(output_file, 'w') as f:
    json.dump(players_sorted, f, indent=2)

# Display top 20
print("TOP 20 - Custom Scoring:")
print("="*70)
print(f"{'Rank':<5} {'Player':<20} {'Final':<10} {'Ind(65%)':<10} {'Team(35%)':<10}")
print("-"*70)

for i, p in enumerate(players_sorted[:20], 1):
    print(f"{i:<5} {p['player_name']:<20} {p['final_score']:<10.2f} "
          f"{p['individual_component']:<10.2f} {p['team_component']:<10.2f}")

print(f"\n{'='*70}")
print("✅ S11 SCORING COMPLETE")
print("="*70)
print(f"Saved to: {output_file}")
print(f"\nNext step: Combine S11 and S12 ratings")
print("  python3 combine_s11_s12_ratings.py")
