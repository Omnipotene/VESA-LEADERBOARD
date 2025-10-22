#!/usr/bin/env python3
"""
Apply 50/50 custom scoring to S12 data:
65% Individual (kills & damage) + 35% Team placement (weighted score)
"""

import json

print("VESA League - S12 Custom Scoring (50/50 Split)")
print("="*70)
print("Formula: 65% Individual Stats + 35% Team Placement")
print("="*70)

# Load deduplicated player data
with open('output/s12_unique_players.json', 'r') as f:
    players = json.load(f)

print(f"Loaded {len(players)} unique players\n")

# Calculate custom scores
for player in players:
    # Individual component (65%)
    # Formula: (Kills × 10) + (Damage / 100)
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

# Update ranks
for i, player in enumerate(players_sorted, 1):
    player['rank'] = i

# Save
output_file = 'output/s12_players_ranked.json'
with open(output_file, 'w') as f:
    json.dump(players_sorted, f, indent=2)

# Display top 20 with breakdown
print("TOP 20 - Custom Scoring Breakdown:")
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

print(f"\n{'='*70}")
print("✅ S12 SCORING COMPLETE")
print("="*70)
print(f"Saved to: {output_file}")
print(f"\nNext step: Run team seeding with S12 data")
print("  python3 team_seeding_s12.py")
