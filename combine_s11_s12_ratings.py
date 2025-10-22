#!/usr/bin/env python3
"""
Combine S11 and S12 player ratings with weighted average
S12 weight: 60% (more recent)
S11 weight: 40% (older data)
"""

import json

print("VESA League - Combined S11+S12 Player Ratings")
print("="*70)
print("Weighting: S12 (60%) + S11 (40%)")
print("="*70)

# Load S12 ratings
with open('output/s12_players_ranked_v2.json', 'r') as f:
    s12_players = json.load(f)

# Load S11 ratings (will be created after S11 scoring)
with open('output/s11_players_ranked.json', 'r') as f:
    s11_players = json.load(f)

print(f"Loaded S12: {len(s12_players)} players")
print(f"Loaded S11: {len(s11_players)} players")

# Create lookups by player name (using aliases already handled in deduplication)
s12_ratings = {}
for p in s12_players:
    # Store all names this player used
    names = p.get('all_names_used', [p['player_name']])
    for name in names:
        s12_ratings[name.lower().strip()] = p['final_score']

s11_ratings = {}
for p in s11_players:
    names = p.get('all_names_used', [p['player_name']])
    for name in names:
        s11_ratings[name.lower().strip()] = p['final_score']

# Get all unique players across both seasons
all_player_names = set(s12_ratings.keys()) | set(s11_ratings.keys())

print(f"Total unique players across both seasons: {len(all_player_names)}\n")

# Calculate combined ratings
combined_players = []
s12_weight = 0.6
s11_weight = 0.4

stats = {'both_seasons': 0, 's12_only': 0, 's11_only': 0}

for player_name in all_player_names:
    s12_score = s12_ratings.get(player_name)
    s11_score = s11_ratings.get(player_name)

    # Skip if both are None (shouldn't happen)
    if not s12_score and not s11_score:
        continue

    if s12_score and s11_score:
        # Player in both seasons - weighted average
        combined_score = (s12_score * s12_weight) + (s11_score * s11_weight)
        seasons_played = 'S11+S12'
        stats['both_seasons'] += 1
    elif s12_score:
        # S12 only
        combined_score = s12_score
        seasons_played = 'S12'
        stats['s12_only'] += 1
    else:
        # S11 only
        combined_score = s11_score
        seasons_played = 'S11'
        stats['s11_only'] += 1

    combined_players.append({
        'player_name': player_name,
        'combined_rating': combined_score,
        's12_rating': s12_score,
        's11_rating': s11_score,
        'seasons_played': seasons_played
    })

# Sort by combined rating
combined_players_sorted = sorted(combined_players, key=lambda x: x['combined_rating'], reverse=True)

# Add ranks
for i, player in enumerate(combined_players_sorted, 1):
    player['rank'] = i

# Save
output_file = 'output/combined_s11_s12_ratings.json'
with open(output_file, 'w') as f:
    json.dump(combined_players_sorted, f, indent=2)

# Display stats
print("Player Distribution:")
print(f"  Both S11 & S12: {stats['both_seasons']} ({stats['both_seasons']/len(all_player_names)*100:.1f}%)")
print(f"  S12 only: {stats['s12_only']} ({stats['s12_only']/len(all_player_names)*100:.1f}%)")
print(f"  S11 only: {stats['s11_only']} ({stats['s11_only']/len(all_player_names)*100:.1f}%)")

# Show top 20
print(f"\nTOP 20 COMBINED RATINGS:")
print("="*70)
print(f"{'Rank':<5} {'Player':<25} {'Combined':<10} {'S12':<10} {'S11':<10}")
print("-"*70)

for i, p in enumerate(combined_players_sorted[:20], 1):
    s12 = f"{p['s12_rating']:.2f}" if p['s12_rating'] else "-"
    s11 = f"{p['s11_rating']:.2f}" if p['s11_rating'] else "-"
    print(f"{i:<5} {p['player_name'][:24]:<25} {p['combined_rating']:<10.2f} {s12:<10} {s11:<10}")

print(f"\n{'='*70}")
print("✅ COMBINED RATINGS CALCULATED")
print("="*70)
print(f"Saved to: {output_file}")
print(f"\nNext step: Re-run team seeding with combined ratings")
print("  python3 team_seeding_combined.py")
