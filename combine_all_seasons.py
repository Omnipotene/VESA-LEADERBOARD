#!/usr/bin/env python3
"""
Combine player ratings from S11 and S12 only
Creates a comprehensive multi-season rating system
S8 is EXCLUDED per user request
"""

import json
from collections import defaultdict

print("VESA League - Multi-Season Player Ratings (S11 + S12)")
print("="*70)

# Load all available season data
seasons_data = {}

# S11
try:
    with open('output/s11_players_ranked.json', 'r') as f:
        seasons_data['S11'] = json.load(f)
    print(f"✓ Loaded S11: {len(seasons_data['S11'])} players")
except FileNotFoundError:
    print("⚠️  S11 data not found")
    seasons_data['S11'] = []

# S12
try:
    with open('output/s12_players_ranked_v2.json', 'r') as f:
        seasons_data['S12'] = json.load(f)
    print(f"✓ Loaded S12: {len(seasons_data['S12'])} players")
except FileNotFoundError:
    print("⚠️  S12 data not found")
    seasons_data['S12'] = []

# Load alias mappings for canonical identity
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

print(f"✓ Loaded {len(name_to_discord)} alias mappings\n")

# Define season weights (S12 placement data is most critical for S12 division seeding)
SEASON_WEIGHTS = {
    'S12': 1.00,  # Most recent - placement matches (100%)
    'S11': 0.00,  # Previous season (0% - ignored)
}

print("Season Weighting:")
for season, weight in SEASON_WEIGHTS.items():
    print(f"  {season}: {weight*100:.0f}%")
print()

# Build canonical player data
player_data = defaultdict(lambda: {
    'seasons': {},
    'names_used': set(),
    'total_weighted_score': 0,
    'seasons_played': []
})

for season, players in seasons_data.items():
    if not players:
        continue

    weight = SEASON_WEIGHTS.get(season, 0.25)

    for p in players:
        player_name = p.get('player_name', '').strip()
        if not player_name:
            continue

        # Find canonical identity
        canonical = name_to_discord.get(player_name.lower(), player_name.lower())

        # Store season-specific data (only if not already stored for this season)
        if season not in player_data[canonical]['seasons']:
            score = p.get('final_score', 0)
            player_data[canonical]['seasons'][season] = {
                'score': score,
                'rank': p.get('rank', 999),
                'name_used': player_name
            }
            player_data[canonical]['total_weighted_score'] += score * weight
            player_data[canonical]['seasons_played'].append(season)

        # Always add the name used
        player_data[canonical]['names_used'].add(player_name)

# Convert to list and calculate final ratings
combined_players = []

for canonical_id, data in player_data.items():
    # Choose primary name (prefer most recent season)
    primary_name = canonical_id
    for season in ['S12', 'S11']:
        if season in data['seasons']:
            primary_name = data['seasons'][season]['name_used']
            break

    # Calculate which seasons this player participated in
    seasons_str = '+'.join(sorted(data['seasons_played']))

    # Get individual season scores
    s11_score = data['seasons'].get('S11', {}).get('score', None)
    s12_score = data['seasons'].get('S12', {}).get('score', None)

    combined_players.append({
        'canonical_id': canonical_id,
        'player_name': primary_name,
        'combined_rating': data['total_weighted_score'],
        's11_rating': s11_score,
        's12_rating': s12_score,
        'seasons_played': seasons_str,
        'all_names_used': list(data['names_used'])
    })

# Sort by combined rating
combined_players_sorted = sorted(combined_players, key=lambda x: x['combined_rating'], reverse=True)

# Add ranks
for i, player in enumerate(combined_players_sorted, 1):
    player['rank'] = i

# Save
output_file = 'output/combined_all_seasons_ratings.json'
with open(output_file, 'w') as f:
    json.dump(combined_players_sorted, f, indent=2)

# Statistics
print("="*70)
print("COMBINED STATISTICS:")
print("-"*70)

total_players = len(combined_players_sorted)
multi_season = len([p for p in combined_players_sorted if '+' in p['seasons_played']])

print(f"Total unique players: {total_players}")
print(f"Multi-season players: {multi_season} ({multi_season/total_players*100:.1f}%)")

# Season distribution
season_counts = defaultdict(int)
for p in combined_players_sorted:
    for season in p['seasons_played'].split('+'):
        season_counts[season] += 1

print(f"\nPlayers per season:")
for season in ['S11', 'S12']:
    count = season_counts.get(season, 0)
    print(f"  {season}: {count} players")

# Show top 20
print(f"\n{'='*70}")
print("TOP 20 PLAYERS (Multi-Season Ratings):")
print("-"*70)
print(f"{'Rank':<5} {'Player':<28} {'Rating':<9} {'Seasons':<13} {'S11':<6} {'S12':<6}")
print("-"*70)

for p in combined_players_sorted[:20]:
    s11 = f"{p['s11_rating']:.1f}" if p['s11_rating'] else "-"
    s12 = f"{p['s12_rating']:.1f}" if p['s12_rating'] else "-"

    print(f"{p['rank']:<5} {p['player_name'][:27]:<28} {p['combined_rating']:<9.2f} {p['seasons_played']:<13} {s11:<6} {s12:<6}")

print(f"\n{'='*70}")
print(f"✅ Multi-season ratings saved to: {output_file}")
print(f"\nNext step: Apply top lobby bonus and re-run team seeding")
print("  1. python3 apply_top_lobby_bonus_all_seasons.py")
print("  2. python3 team_seeding_combined.py")
print("  3. python3 division_seeding.py")
print("  4. python3 export_division_assignments.py")
