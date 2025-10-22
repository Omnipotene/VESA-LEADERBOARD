#!/usr/bin/env python3
"""
Combine S11 and S12 player ratings with weighted average (v2)
Uses canonical player identity instead of creating duplicates from aliases
S12 weight: 60% (more recent)
S11 weight: 40% (older data)
"""

import json
from collections import defaultdict

print("VESA League - Combined S11+S12 Player Ratings (v2)")
print("="*70)
print("Weighting: S12 (60%) + S11 (40%)")
print("="*70)

# Load S12 ratings (already deduplicated by canonical identity)
with open('output/s12_players_ranked_v2.json', 'r') as f:
    s12_players = json.load(f)

# Load S11 ratings (already deduplicated by canonical identity)
with open('output/s11_players_ranked.json', 'r') as f:
    s11_players = json.load(f)

print(f"Loaded S12: {len(s12_players)} players")
print(f"Loaded S11: {len(s11_players)} players")

# Load alias mappings to find canonical identities
with open('data/player_aliases.json', 'r') as f:
    aliases_data = json.load(f)

# Build name -> discord mapping
name_to_discord = {}
for player in aliases_data:
    discord = player['discord_name'].lower().strip()
    for alias in player['aliases']:
        alias_lower = alias.lower().strip()
        if alias_lower:
            name_to_discord[alias_lower] = discord

print(f"Loaded {len(name_to_discord)} alias mappings\n")

# Build canonical player lookups
# For S12: canonical_id -> {score, primary_name, all_names}
s12_by_canonical = {}
for p in s12_players:
    primary_name = p['player_name'].lower().strip()

    # Find canonical identity
    canonical = name_to_discord.get(primary_name, primary_name)

    # Only keep best if duplicate (shouldn't happen but just in case)
    if canonical not in s12_by_canonical or p['final_score'] > s12_by_canonical[canonical]['score']:
        s12_by_canonical[canonical] = {
            'score': p['final_score'],
            'primary_name': p['player_name'],
            'all_names': p.get('all_names_used', [p['player_name']])
        }

# For S11: canonical_id -> {score, primary_name, all_names}
s11_by_canonical = {}
for p in s11_players:
    primary_name = p['player_name'].lower().strip()

    # Find canonical identity
    canonical = name_to_discord.get(primary_name, primary_name)

    if canonical not in s11_by_canonical or p['final_score'] > s11_by_canonical[canonical]['score']:
        s11_by_canonical[canonical] = {
            'score': p['final_score'],
            'primary_name': p['player_name'],
            'all_names': p.get('all_names_used', [p['player_name']])
        }

print(f"S12 players by canonical ID: {len(s12_by_canonical)}")
print(f"S11 players by canonical ID: {len(s11_by_canonical)}")

# Get all unique canonical identities
all_canonical_ids = set(s12_by_canonical.keys()) | set(s11_by_canonical.keys())
print(f"Total unique players (by canonical ID): {len(all_canonical_ids)}\n")

# Calculate combined ratings
combined_players = []
s12_weight = 0.6
s11_weight = 0.4

stats = {'both_seasons': 0, 's12_only': 0, 's11_only': 0}

for canonical_id in all_canonical_ids:
    s12_data = s12_by_canonical.get(canonical_id)
    s11_data = s11_by_canonical.get(canonical_id)

    s12_score = s12_data['score'] if s12_data else None
    s11_score = s11_data['score'] if s11_data else None

    # Skip if both are None (shouldn't happen)
    if not s12_score and not s11_score:
        continue

    # Choose primary name (prefer S12, fall back to S11)
    if s12_data:
        primary_name = s12_data['primary_name']
    else:
        primary_name = s11_data['primary_name']

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
        'canonical_id': canonical_id,
        'player_name': primary_name,
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
print(f"  Both S11 & S12: {stats['both_seasons']} ({stats['both_seasons']/len(all_canonical_ids)*100:.1f}%)")
print(f"  S12 only: {stats['s12_only']} ({stats['s12_only']/len(all_canonical_ids)*100:.1f}%)")
print(f"  S11 only: {stats['s11_only']} ({stats['s11_only']/len(all_canonical_ids)*100:.1f}%)")

# Show top 20
print(f"\nTOP 20 COMBINED RATINGS:")
print("="*70)
print(f"{'Rank':<5} {'Player':<25} {'Combined':<10} {'S12':<10} {'S11':<10} {'Seasons'}")
print("-"*70)

for i, p in enumerate(combined_players_sorted[:20], 1):
    s12 = f"{p['s12_rating']:.2f}" if p['s12_rating'] else "-"
    s11 = f"{p['s11_rating']:.2f}" if p['s11_rating'] else "-"
    print(f"{i:<5} {p['player_name'][:24]:<25} {p['combined_rating']:<10.2f} {s12:<10} {s11:<10} {p['seasons_played']}")

print(f"\n{'='*70}")
print("✅ COMBINED RATINGS CALCULATED (v2 - no duplicates)")
print("="*70)
print(f"Saved to: {output_file}")
print(f"\nNext step: Re-run team seeding with combined ratings")
print("  python3 team_seeding_combined.py")
