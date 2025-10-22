#!/usr/bin/env python3
"""
Apply lobby weights to scraped data and show true rankings
"""

import json

# Load the weight configuration
with open('config/weights.json', 'r') as f:
    config = json.load(f)

lobby_weights = config['lobby_weights']['weights']

# Load the scraped data
with open('output/all_divisions_data.json', 'r') as f:
    all_players = json.load(f)

print("VESA League - Weighted Player Rankings")
print("="*80)

# Apply weights to each player
for player in all_players:
    lobby = str(player['lobby'])
    weight = float(lobby_weights.get(lobby, 1.0))

    raw_score = player['score']
    weighted_score = raw_score * weight

    player['lobby_weight'] = weight
    player['weighted_score'] = weighted_score

# Sort by weighted score
sorted_players = sorted(all_players, key=lambda x: x['weighted_score'], reverse=True)

# Show comparison
print("\nTOP 10 - BEFORE WEIGHTING (Raw Scores):")
print("-"*80)
raw_sorted = sorted(all_players, key=lambda x: x['score'], reverse=True)
for i, p in enumerate(raw_sorted[:10], 1):
    print(f"{i:2}. {p['player_name']:20} ({p['division']:25}) Raw: {p['score']:6.0f}")

print("\n" + "="*80)
print("TOP 10 - AFTER WEIGHTING (True Skill Rankings):")
print("="*80)
print(f"{'Rank':<5} {'Player':<20} {'Division':<27} {'Raw':<8} {'Weight':<8} {'Weighted':<10}")
print("-"*80)

for i, p in enumerate(sorted_players[:10], 1):
    print(f"{i:<5} {p['player_name']:<20} {p['division']:<27} "
          f"{p['score']:<8.0f} {p['lobby_weight']:<8.2f} {p['weighted_score']:<10.2f}")

print("\n" + "="*80)
print("DIVISION BREAKDOWN:")
print("="*80)

# Count players by division in top 10
top10_divisions = {}
for p in sorted_players[:10]:
    div = p['division']
    top10_divisions[div] = top10_divisions.get(div, 0) + 1

for div, count in sorted(top10_divisions.items(), key=lambda x: x[1], reverse=True):
    print(f"  {div:30} {count} players in top 10")

# Save weighted results
output_file = "output/weighted_rankings.json"
with open(output_file, 'w') as f:
    json.dump(sorted_players, f, indent=2)

print(f"\n✅ Weighted rankings saved to: {output_file}")

# Show top 20 for more context
print("\n" + "="*80)
print("TOP 20 - WEIGHTED RANKINGS:")
print("="*80)
for i, p in enumerate(sorted_players[:20], 1):
    print(f"{i:2}. {p['player_name']:20} ({p['division']:27}) "
          f"Weighted: {p['weighted_score']:6.2f} (Raw: {p['score']:.0f} × {p['lobby_weight']:.2f})")

print("\n" + "="*80)
print("This is your TRUE skill-based leaderboard!")
print("="*80)
