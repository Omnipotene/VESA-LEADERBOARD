#!/usr/bin/env python3
"""
Extract Division History from Existing Scraped Data
Builds player_division_history.json mapping each player to their division per season
Uses canonical player IDs to properly merge division history across name changes
"""

import json
from collections import defaultdict

print("VESA League - Division History Extractor")
print("="*70)

# Load alias mappings for canonical identity
with open('data/player_aliases.json', 'r') as f:
    aliases_data = json.load(f)

# Build name -> canonical discord mapping
name_to_discord = {}
for player in aliases_data:
    discord = player['discord_name'].lower().strip()
    for alias in player['aliases']:
        alias_lower = alias.lower().strip()
        if alias_lower:
            name_to_discord[alias_lower] = discord

print(f"Loaded {len(name_to_discord)} alias mappings")

# S12 Placement Lobby Bonus System (per-lobby bonuses)
# Each lobby appearance adds its bonus percentage to the player's rating
LOBBY_BONUSES = {
    '1': 81.92,     # 8192%
    '1.5': 40.96,   # 4096%
    '2': 20.48,     # 2048%
    '2.5': 10.24,   # 1024%
    '3': 5.12,      # 512%
    '3.5': 2.56,    # 256%
    '4': 1.28,      # 128%
    '4.5': 0.64,    # 64%
    '5': 0.32,      # 32%
    '5.5': 0.16,    # 16%
    '6': 0.08,      # 8%
    '6.5': 0.04,    # 4%
    '7': 0.02,      # 2%
}

# Legacy division scores for S11 (kept for backward compatibility)
DIVISION_SCORES = {
    'Pinnacle': 10,
    'Pinnacle I': 10,
    'Pinnacle II': 9,
    'Vanguard': 8,
    'Vanguard I': 8,
    'Vanguard II': 7,
    'Ascendant': 6,
    'Ascendant I': 6,
    'Ascendant II': 5,
    'Emergent': 4,
    'Emergent I': 4,
    'Emergent II': 3,
    'Challengers': 3,
    'Challengers I': 3,
    'Challengers II': 2,
    'Prospect': 2,
    'Prospect I': 2,
    'Prospect II': 1,
    'Tendies': 2,
    'Contenders': 1,
    'Contenders I': 1,
    'Contenders II': 1,
}

# Load scraped season data
seasons_data = {}

# S8 - No division data available (skip for now)
print("S8: No division data available - skipped")
seasons_data['s8'] = []

# S11 - Use inferred division data (based on rankings)
print("Loading S11 data...")
with open('data/s11_inferred_divisions.json', 'r') as f:
    s11_divisions = json.load(f)
    seasons_data['s11'] = [(p['player_name'], p['division']) for p in s11_divisions]
print(f"  S11: {len(seasons_data['s11'])} players with inferred divisions")

# S12 - Load RAW lobby data for per-day, per-lobby bonuses
print("Loading S12 raw placement data (all days)...")
with open('output/s12_placements_raw.json', 'r') as f:
    s12_raw_data = json.load(f)

# Build lobby history: canonical_id -> list of lobby appearances across all days
print("\nBuilding S12 lobby history (per-day tracking)...")
player_lobby_history = defaultdict(list)

for entry in s12_raw_data:
    player_name = entry.get('player_name', '').lower().strip()
    lobby = str(entry.get('lobby', ''))
    day = entry.get('day', 0)

    if player_name and lobby:
        # Find canonical identity
        canonical = name_to_discord.get(player_name, player_name)
        player_lobby_history[canonical].append(lobby)

print(f"  S12: {len(player_lobby_history)} players with lobby data")
print(f"  Total lobby appearances: {sum(len(lobbies) for lobbies in player_lobby_history.values())}")

# Calculate per-lobby bonuses for each player
player_division_scores = {}

for player, lobbies in player_lobby_history.items():
    total_bonus = 0.0
    lobby_details = []

    for lobby in lobbies:
        bonus = LOBBY_BONUSES.get(lobby, 0.0)
        total_bonus += bonus
        lobby_details.append(f"Lobby {lobby}: +{bonus*100:.0f}%")

    if total_bonus > 0:
        player_division_scores[player] = {
            'lobby_history': lobbies,
            'lobby_appearances': len(lobbies),
            'consistency_bonus': total_bonus,
            'lobby_details': lobby_details,
            'seasons_with_divisions': ['S12']
        }

print(f"  Total players with bonuses: {len(player_division_scores)}")

# Save division history
output_file = 'data/player_division_history.json'
with open(output_file, 'w') as f:
    json.dump(player_division_scores, f, indent=2)

print(f"\n{'='*70}")
print("S12 LOBBY BONUS SYSTEM EXTRACTED")
print("="*70)
print(f"Total players with lobby bonuses: {len(player_division_scores)}")

# Show bonus distribution by ranges
bonus_ranges = {
    '1000%+': 0,
    '500-999%': 0,
    '300-499%': 0,
    '200-299%': 0,
    '100-199%': 0,
    '50-99%': 0,
    '0-49%': 0
}

for data in player_division_scores.values():
    bonus_pct = data['consistency_bonus'] * 100
    if bonus_pct >= 1000:
        bonus_ranges['1000%+'] += 1
    elif bonus_pct >= 500:
        bonus_ranges['500-999%'] += 1
    elif bonus_pct >= 300:
        bonus_ranges['300-499%'] += 1
    elif bonus_pct >= 200:
        bonus_ranges['200-299%'] += 1
    elif bonus_pct >= 100:
        bonus_ranges['100-199%'] += 1
    elif bonus_pct >= 50:
        bonus_ranges['50-99%'] += 1
    else:
        bonus_ranges['0-49%'] += 1

print(f"\nLobby Bonus Distribution:")
for range_name, count in bonus_ranges.items():
    print(f"  {range_name}: {count} players")

# Show top bonus players
print(f"\nTop 10 Players by Total Lobby Bonus:")
top_players = sorted(player_division_scores.items(), key=lambda x: x[1]['consistency_bonus'], reverse=True)[:10]
for i, (player, data) in enumerate(top_players, 1):
    bonus_pct = data['consistency_bonus'] * 100
    lobbies_str = ', '.join(data['lobby_history'])
    print(f"  {i}. {player}: +{bonus_pct:.0f}% (Lobbies: {lobbies_str})")

print(f"\nSaved to: {output_file}")
