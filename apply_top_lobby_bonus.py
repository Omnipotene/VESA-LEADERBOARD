#!/usr/bin/env python3
"""
Apply bonus weighting to players who competed in top lobbies (A/B divisions)
This rewards players who performed well against tougher competition
"""

import json

print("Applying Top Lobby Bonus to Player Ratings")
print("="*70)

# Load top lobby players list
with open('data/top_lobby_players.json', 'r') as f:
    top_lobby_players = set(player.lower() for player in json.load(f))

print(f"Loaded {len(top_lobby_players)} top lobby players")

# Load player name mapping to match Discord -> In-game names
with open('data/player_name_mapping.json', 'r') as f:
    player_mapping = json.load(f)

# Create Discord -> In-game lookup
discord_to_ingame = {}
for mapping in player_mapping:
    discord = mapping['discord_name'].lower()
    ingame = mapping['ingame_name']
    discord_to_ingame[discord] = ingame

# Load combined ratings
with open('output/combined_s11_s12_ratings.json', 'r') as f:
    players = json.load(f)

print(f"Loaded {len(players)} player ratings")

# Apply bonus to top lobby players
TOP_LOBBY_BONUS = 1.15  # 15% bonus for competing in top lobbies

bonus_applied_count = 0
for player in players:
    player_name = player['player_name'].lower()

    # Check if this player competed in top lobbies
    # Try both their in-game name and check if any Discord name maps to them
    is_top_lobby = False

    # Direct name check
    if player_name in top_lobby_players:
        is_top_lobby = True

    # Check via Discord mapping
    for discord, ingame in discord_to_ingame.items():
        if discord in top_lobby_players and ingame.lower() == player_name:
            is_top_lobby = True
            break

    if is_top_lobby:
        original_rating = player['combined_rating']
        player['combined_rating'] = original_rating * TOP_LOBBY_BONUS
        player['top_lobby_bonus'] = True
        bonus_applied_count += 1

print(f"\n✅ Applied {TOP_LOBBY_BONUS}x bonus to {bonus_applied_count} players")

# Re-sort by rating
players_sorted = sorted(players, key=lambda x: x['combined_rating'], reverse=True)

# Show top 20 with bonus indicator
print("\nTOP 20 PLAYERS (with bonus applied):")
print("-"*70)
print(f"{'Rank':<5} {'Player':<30} {'Rating':<10} {'Bonus'}")
print("-"*70)

for i, player in enumerate(players_sorted[:20], 1):
    bonus_marker = "✓" if player.get('top_lobby_bonus', False) else ""
    print(f"{i:<5} {player['player_name']:<30} {player['combined_rating']:<10.2f} {bonus_marker}")

# Save updated ratings
output_file = 'output/combined_s11_s12_ratings_with_bonus.json'
with open(output_file, 'w') as f:
    json.dump(players_sorted, f, indent=2)

print(f"\n✅ Saved updated ratings to: {output_file}")
print("\nNext: Re-run team_seeding_combined.py with the new ratings file")
