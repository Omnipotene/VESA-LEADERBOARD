#!/usr/bin/env python3
"""
Team Seeding System - Calculate team ratings and seed into divisions
"""

import csv
import json
from collections import defaultdict

print("VESA League - Team Seeding System (Season 12 Data)")
print("="*70)

# Load player ratings from S12 leaderboard
with open('output/s12_players_ranked.json', 'r') as f:
    players_data = json.load(f)

# Create player rating lookup (by player name)
player_ratings = {}
for p in players_data:
    # Calculate 50/50 score if not already present
    if 'final_score' in p:
        rating = p['final_score']
    else:
        # Calculate it: 50% individual + 50% team
        individual_score = (p['kills'] * 10) + (p['damage'] / 100)
        team_score = p['weighted_score']
        rating = (individual_score * 0.50) + (team_score * 0.50)

    player_ratings[p['player_name'].lower().strip()] = {
        'rating': rating,
        'division': p['division'],
        'kills': p['kills'],
        'raw_score': p['score']
    }

print(f"Loaded ratings for {len(player_ratings)} players")

# Load player name mapping (Discord -> In-Game names)
with open('data/player_name_mapping.json', 'r') as f:
    player_mapping_list = json.load(f)

# Create lookup: discord_name -> ingame_name
discord_to_ingame = {}
for mapping in player_mapping_list:
    discord_to_ingame[mapping['discord_name'].lower().strip()] = mapping['ingame_name']

print(f"Loaded {len(discord_to_ingame)} player name mappings")

# Load team rosters
teams = []
with open('data/rosters.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        team_name = row.get('Team Name', '').strip()

        # Skip header rows or empty teams
        if not team_name or 'Lobby' in team_name or team_name == '':
            continue

        # Extract player names (Discord usernames)
        discord1 = row.get('Rostered Player 1 Discord Username', '').strip()
        discord2 = row.get('Rostered Player 2 Discord Username', '').strip()
        discord3 = row.get('Rostered Player 3 Discord Username', '').strip()

        # Convert to in-game names
        player1 = discord_to_ingame.get(discord1.lower(), discord1)
        player2 = discord_to_ingame.get(discord2.lower(), discord2)
        player3 = discord_to_ingame.get(discord3.lower(), discord3)

        if player1 and player2 and player3:
            teams.append({
                'team_name': team_name,
                'player1': player1,
                'player2': player2,
                'player3': player3,
                'discord1': discord1,
                'discord2': discord2,
                'discord3': discord3
            })

print(f"Loaded {len(teams)} teams from roster file\n")

# Calculate team ratings
print("Calculating team ratings...")
print("-"*70)

DEFAULT_RATING = 200  # For players not found in database

for team in teams:
    player_names = [team['player1'], team['player2'], team['player3']]
    ratings = []
    found_players = []
    missing_players = []

    for pname in player_names:
        # Try exact match
        rating_data = player_ratings.get(pname.lower().strip())

        if rating_data:
            ratings.append(rating_data['rating'])
            found_players.append(pname)
        else:
            # Player not found - assign default
            ratings.append(DEFAULT_RATING)
            missing_players.append(pname)

    # Calculate team rating (average of 3 players)
    team_rating = sum(ratings) / 3 if ratings else DEFAULT_RATING

    team['player_ratings'] = ratings
    team['team_rating'] = team_rating
    team['found_players'] = found_players
    team['missing_players'] = missing_players

    # Assign automatic tier based on team rating
    if team_rating >= 600:
        tier = 'S'
        tier_desc = 'Auto Division 1'
    elif team_rating >= 500:
        tier = 'A'
        tier_desc = 'Must be Div 1 or 2'
    elif team_rating >= 400:
        tier = 'B'
        tier_desc = 'Must be Div 1-3'
    elif team_rating >= 300:
        tier = 'C'
        tier_desc = 'Must be Div 1-4'
    else:
        tier = 'D'
        tier_desc = 'Algorithmic'

    team['tier'] = tier
    team['tier_desc'] = tier_desc

# Sort teams by rating
teams_sorted = sorted(teams, key=lambda x: x['team_rating'], reverse=True)

# Display top 20 teams
print(f"\nTOP 20 TEAMS BY RATING:")
print("="*70)
print(f"{'Rank':<5} {'Team':<25} {'Rating':<10} {'Tier':<5} {'Players Found'}")
print("-"*70)

for i, team in enumerate(teams_sorted[:20], 1):
    print(f"{i:<5} {team['team_name']:<25} {team['team_rating']:<10.2f} {team['tier']:<5} "
          f"{len(team['found_players'])}/3")

# Show tier distribution
print(f"\n{'='*70}")
print("TIER DISTRIBUTION:")
print("="*70)

tier_counts = defaultdict(int)
for team in teams_sorted:
    tier_counts[team['tier']] += 1

for tier in ['S', 'A', 'B', 'C', 'D']:
    count = tier_counts.get(tier, 0)
    print(f"  Tier {tier}: {count:3} teams")

# Show teams with missing players
missing_player_teams = [t for t in teams_sorted if t['missing_players']]
print(f"\n{'='*70}")
print(f"TEAMS WITH MISSING PLAYERS: {len(missing_player_teams)}")
print("="*70)
print("These teams have players not found in the Season 12 database:")
print()

for team in missing_player_teams[:10]:
    print(f"{team['team_name']}:")
    for p in team['missing_players']:
        print(f"    - {p} (assigned default rating: {DEFAULT_RATING})")

# Save team ratings
output_file = "output/team_ratings_s12.json"
with open(output_file, 'w') as f:
    json.dump(teams_sorted, f, indent=2)

print(f"\n{'='*70}")
print("✅ TEAM RATINGS CALCULATED")
print("="*70)
print(f"Saved to: {output_file}")
print(f"\nNext step: Run division seeding to place teams into 7 divisions")
