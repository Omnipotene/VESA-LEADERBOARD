#!/usr/bin/env python3
"""
Apply S12 Lobby-Based Bonuses to Player Ratings
Rewards players based on their S12 placement lobby appearances
Each lobby grants a percentage bonus that stacks additively
"""

import json
from collections import defaultdict

print("Applying S12 Lobby-Based Bonuses to Player Ratings")
print("="*70)

# Load lobby bonus history
with open('data/player_division_history.json', 'r') as f:
    division_history = json.load(f)

print(f"Loaded lobby bonus data for {len(division_history)} players")

# Load combined ratings (all seasons)
with open('output/combined_all_seasons_ratings.json', 'r') as f:
    players = json.load(f)

print(f"Loaded {len(players)} player ratings\n")

# Bonus tier breakdown
print("S12 Lobby Bonus System (Per-Lobby Bonuses):")
print("  Lobby 1:   +500% per appearance")
print("  Lobby 1.5: +400% per appearance")
print("  Lobby 2:   +300% per appearance")
print("  Lobby 2.5: +225% per appearance")
print("  Lobby 3:   +150% per appearance")
print("  Lobby 3.5: +100% per appearance")
print("  Lobby 4:   +75% per appearance")
print("  Lobby 4.5: +50% per appearance")
print("  Lobby 5:   +37% per appearance")
print("  Lobby 5.5: +22% per appearance")
print("  Lobby 6:   +19% per appearance")
print("  Lobby 6.5: +14% per appearance")
print("  Lobby 7:   +10% per appearance")
print()

# Apply lobby-based bonus
bonus_stats = defaultdict(int)

for player in players:
    player_name = player['player_name'].lower()
    all_names = [name.lower() for name in player.get('all_names_used', [])]
    canonical_id = player.get('canonical_id', '').lower()

    # Try to find division history for this player
    bonus_data = None

    # Strategy 1: Check by player_name
    if player_name in division_history:
        bonus_data = division_history[player_name]

    # Strategy 2: Check by canonical_id
    elif canonical_id in division_history:
        bonus_data = division_history[canonical_id]

    # Strategy 3: Check all historical names
    else:
        for name in all_names:
            if name in division_history:
                bonus_data = division_history[name]
                break

    if bonus_data:
        original_rating = player['combined_rating']
        bonus = bonus_data['consistency_bonus']

        player['combined_rating'] = original_rating * (1 + bonus)
        player['consistency_bonus'] = bonus
        player['lobby_history'] = bonus_data.get('lobby_history', [])
        player['lobby_appearances'] = bonus_data.get('lobby_appearances', 0)
        player['lobby_details'] = bonus_data.get('lobby_details', [])
        player['seasons_with_divisions'] = bonus_data['seasons_with_divisions']

        bonus_stats[bonus] += 1
    else:
        # No lobby history found - no bonus
        player['consistency_bonus'] = 0.0

# Show bonus distribution by ranges
bonus_ranges = {
    '1000%+': 0,
    '500-999%': 0,
    '300-499%': 0,
    '200-299%': 0,
    '100-199%': 0,
    '50-99%': 0,
    '0-49%': 0,
    '0%': 0
}

for bonus in bonus_stats.keys():
    bonus_pct = bonus * 100
    count = bonus_stats[bonus]
    if bonus_pct >= 1000:
        bonus_ranges['1000%+'] += count
    elif bonus_pct >= 500:
        bonus_ranges['500-999%'] += count
    elif bonus_pct >= 300:
        bonus_ranges['300-499%'] += count
    elif bonus_pct >= 200:
        bonus_ranges['200-299%'] += count
    elif bonus_pct >= 100:
        bonus_ranges['100-199%'] += count
    elif bonus_pct >= 50:
        bonus_ranges['50-99%'] += count
    elif bonus_pct > 0:
        bonus_ranges['0-49%'] += count
    else:
        bonus_ranges['0%'] += count

print(f"\nLobby Bonus Distribution:")
for range_name, count in bonus_ranges.items():
    if count > 0:
        print(f"  {range_name}: {count} players")
print(f"\nTotal players with bonuses: {sum(bonus_stats.values()) - bonus_stats.get(0.0, 0)}")
print(f"Total players without bonuses: {bonus_stats.get(0.0, 0)}")

# Re-sort by rating
players_sorted = sorted(players, key=lambda x: x['combined_rating'], reverse=True)

# Update ranks
for i, player in enumerate(players_sorted, 1):
    player['rank'] = i

# Show top 20 with bonus indicator
print("\nTOP 20 PLAYERS (with lobby bonus applied):")
print("-"*100)
print(f"{'Rank':<5} {'Player':<28} {'Rating':<10} {'Seasons':<10} {'Bonus':<8} {'Lobbies'}")
print("-"*100)

for player in players_sorted[:20]:
    bonus = player.get('consistency_bonus', 0.0)
    lobbies = player.get('lobby_history', [])
    seasons = player['seasons_played']

    bonus_str = f"{bonus*100:.0f}%" if bonus > 0 else "-"
    lobby_str = ', '.join(lobbies) if lobbies else "-"

    print(f"{player['rank']:<5} {player['player_name'][:27]:<28} {player['combined_rating']:<10.2f} {seasons:<10} {bonus_str:<8} {lobby_str}")

# Save updated ratings
output_file = 'output/combined_all_seasons_ratings_with_bonus.json'
with open(output_file, 'w') as f:
    json.dump(players_sorted, f, indent=2)

print(f"\n✅ Saved updated ratings to: {output_file}")
print("\nNext steps:")
print("  1. python3 team_seeding_combined.py")
print("  2. python3 division_seeding.py")
print("  3. python3 export_division_assignments.py")
