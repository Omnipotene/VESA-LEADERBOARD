#!/usr/bin/env python3
"""
Aggregate S12 Placement Data - Average Per Day Method
Calculates player ratings as: (Total Points Across All Days) / (Days Played)
"""

import json
from collections import defaultdict

print("VESA League - S12 Aggregation (Average Per Day)")
print("="*70)

# Load raw placement data
with open('output/s12_placements_raw.json', 'r') as f:
    raw_data = json.load(f)

print(f"Loaded {len(raw_data)} total day-player entries")

# Load aliases
with open('data/player_aliases.json', 'r') as f:
    aliases_data = json.load(f)

# Build alias lookup: any_name -> canonical_discord_name
name_to_discord = {}
for player in aliases_data:
    discord = player['discord_name'].lower().strip()
    for alias in player['aliases']:
        alias_lower = alias.lower().strip()
        if alias_lower:
            name_to_discord[alias_lower] = discord

print(f"Loaded {len(name_to_discord)} alias mappings\n")

# Group by canonical player identity
player_stats = defaultdict(lambda: {
    'days_played': set(),
    'total_score': 0,
    'total_kills': 0,
    'total_damage': 0,
    'lobbies': [],
    'all_names': set()
})

for entry in raw_data:
    player_name = entry.get('player_name', '').lower().strip()
    day = entry.get('day', 0)
    score = entry.get('score', 0)
    kills = entry.get('kills', 0)
    damage = entry.get('damage', 0)
    lobby = str(entry.get('lobby', ''))

    if not player_name:
        continue

    # Find canonical identity
    canonical = name_to_discord.get(player_name, player_name)

    # Aggregate stats
    player_stats[canonical]['days_played'].add(day)
    player_stats[canonical]['total_score'] += score
    player_stats[canonical]['total_kills'] += kills
    player_stats[canonical]['total_damage'] += damage
    player_stats[canonical]['lobbies'].append(lobby)
    player_stats[canonical]['all_names'].add(entry.get('player_name', ''))

print(f"Grouped into {len(player_stats)} unique players\n")

# Calculate average per day for each player
players_ranked = []

for canonical_id, stats in player_stats.items():
    days_played = len(stats['days_played'])

    if days_played == 0:
        continue

    # Calculate averages
    avg_score_per_day = stats['total_score'] / days_played
    avg_kills_per_day = stats['total_kills'] / days_played
    avg_damage_per_day = stats['total_damage'] / days_played

    player_data = {
        'canonical_id': canonical_id,
        'player_name': list(stats['all_names'])[0],  # Use first name as display name
        'all_names_used': sorted(list(stats['all_names'])),
        'days_played': days_played,
        'total_score': stats['total_score'],
        'total_kills': stats['total_kills'],
        'total_damage': stats['total_damage'],
        'avg_score_per_day': avg_score_per_day,
        'avg_kills_per_day': avg_kills_per_day,
        'avg_damage_per_day': avg_damage_per_day,
        'lobby_history': stats['lobbies'],
        'rating': avg_score_per_day  # Use average as base rating
    }

    players_ranked.append(player_data)

# Sort by average score per day
players_ranked.sort(key=lambda x: x['avg_score_per_day'], reverse=True)

# Assign ranks
for i, player in enumerate(players_ranked, 1):
    player['rank'] = i

# Save
output_file = 'output/s12_players_ranked.json'
with open(output_file, 'w') as f:
    json.dump(players_ranked, f, indent=2)

print("AGGREGATION STATISTICS:")
print("="*70)
print(f"Total unique players: {len(players_ranked)}")
print(f"\nDays Played Distribution:")

days_distribution = defaultdict(int)
for p in players_ranked:
    days_distribution[p['days_played']] += 1

for days in sorted(days_distribution.keys()):
    count = days_distribution[days]
    pct = (count / len(players_ranked)) * 100
    print(f"  {days} day(s): {count} players ({pct:.1f}%)")

print(f"\n{'='*70}")
print("TOP 20 PLAYERS (By Average Score Per Day):")
print("="*70)
print(f"{'Rank':<5} {'Player':<25} {'Avg/Day':<10} {'Total':<10} {'Days':<6} {'K/D'}")
print("-"*70)

for i, p in enumerate(players_ranked[:20], 1):
    avg_kd = f"{p['avg_kills_per_day']:.1f}k/{p['avg_damage_per_day']:.0f}d"
    print(f"{i:<5} {p['player_name']:<25} {p['avg_score_per_day']:<10.2f} "
          f"{p['total_score']:<10.2f} {p['days_played']:<6} {avg_kd}")

# Show comparison of players with different days played
print(f"\n{'='*70}")
print("AVERAGE VS TOTAL COMPARISON (Sample):")
print("="*70)
print("Players who played 4 days vs 1 day:")

four_day_players = [p for p in players_ranked if p['days_played'] == 4][:5]
one_day_players = [p for p in players_ranked if p['days_played'] == 1][:5]

print("\n4-Day Players (Top 5):")
for p in four_day_players:
    print(f"  {p['player_name']}: Avg={p['avg_score_per_day']:.2f}, Total={p['total_score']:.2f}")

print("\n1-Day Players (Top 5):")
for p in one_day_players:
    print(f"  {p['player_name']}: Avg={p['avg_score_per_day']:.2f}, Total={p['total_score']:.2f}")

print(f"\n{'='*70}")
print("✅ S12 AGGREGATION COMPLETE")
print("="*70)
print(f"Saved to: {output_file}")
print("\nRatings are now based on AVERAGE SCORE PER DAY")
print("This ensures fairness between players who played different numbers of days")
