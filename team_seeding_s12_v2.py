#!/usr/bin/env python3
"""
Team Seeding System with Alias Matching - S12 Data
Uses scraped player aliases for maximum matching accuracy
"""

import csv
import json
from collections import defaultdict

print("VESA League - Team Seeding System (Season 12 Data - Alias Matching)")
print("="*70)

# Load player ratings from S12 leaderboard
with open('output/s12_players_ranked_v2.json', 'r') as f:
    players_data = json.load(f)

# Create player rating lookup (by player name)
player_ratings = {}
for p in players_data:
    rating = p['final_score']

    player_ratings[p['player_name'].lower().strip()] = {
        'rating': rating,
        'division': p.get('division', 'Unknown'),
        'kills': p['kills'],
        'raw_score': p.get('score', 0),
        'original_name': p['player_name']
    }

print(f"Loaded ratings for {len(player_ratings)} players")

# Load player aliases
with open('data/player_aliases.json', 'r') as f:
    aliases_data = json.load(f)

# Build comprehensive alias lookup: any_alias -> player_data
alias_lookup = {}
discord_to_aliases = {}

for player in aliases_data:
    discord = player['discord_name'].lower().strip()
    aliases = player['aliases']
    
    discord_to_aliases[discord] = aliases
    
    # Map every alias to this discord user
    for alias in aliases:
        alias_lower = alias.lower().strip()
        if alias_lower:
            alias_lookup[alias_lower] = discord

print(f"Loaded {len(aliases_data)} players with {sum(len(p['aliases']) for p in aliases_data)} total aliases")

# Load player name mapping (Discord -> In-Game names)
with open('data/player_name_mapping.json', 'r') as f:
    player_mapping_list = json.load(f)

# Create lookup: discord_name -> ingame_name
discord_to_ingame = {}
for mapping in player_mapping_list:
    discord_to_ingame[mapping['discord_name'].lower().strip()] = mapping['ingame_name']

print(f"Loaded {len(discord_to_ingame)} player name mappings")

# Enhanced matching function
def match_player(roster_name, player_ratings, alias_lookup, discord_to_aliases):
    """
    Try to find a match for roster_name using:
    1. Exact match in ratings database
    2. Alias lookup to find discord name, then map to rating
    """
    roster_lower = roster_name.lower().strip()
    
    # Strategy 1: Direct exact match in ratings
    if roster_lower in player_ratings:
        return player_ratings[roster_lower], 'exact', roster_name
    
    # Strategy 2: Find via alias
    # Check if roster name is an alias we know about
    if roster_lower in alias_lookup:
        discord = alias_lookup[roster_lower]
        
        # Now check if this discord user's in-game name is in ratings
        if discord in discord_to_aliases:
            aliases = discord_to_aliases[discord]
            
            # Try each alias in the ratings database
            for alias in aliases:
                alias_lower = alias.lower().strip()
                if alias_lower in player_ratings:
                    return player_ratings[alias_lower], 'alias', f"{roster_name} → {alias}"
    
    return None, None, None

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
print("Calculating team ratings with alias matching...")
print("-"*70)

DEFAULT_RATING = 200  # For players not found in database

match_stats = {'exact': 0, 'alias': 0, 'not_found': 0}

for team in teams:
    player_names = [team['player1'], team['player2'], team['player3']]
    ratings = []
    found_players = []
    missing_players = []
    match_types = []

    for pname in player_names:
        # Try alias matching
        rating_data, match_type, match_info = match_player(
            pname, player_ratings, alias_lookup, discord_to_aliases
        )

        if rating_data:
            ratings.append(rating_data['rating'])
            found_players.append(match_info if match_info else pname)
            match_types.append(match_type)
            match_stats[match_type] += 1
        else:
            # Player not found - assign default
            ratings.append(DEFAULT_RATING)
            missing_players.append(pname)
            match_stats['not_found'] += 1

    # Calculate team rating (average of 3 players)
    team_rating = sum(ratings) / 3 if ratings else DEFAULT_RATING

    team['player_ratings'] = ratings
    team['team_rating'] = team_rating
    team['found_players'] = found_players
    team['missing_players'] = missing_players
    team['match_types'] = match_types

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

# Show matching statistics
print(f"\n{'='*70}")
print("MATCHING STATISTICS:")
print("="*70)
total_players = len(teams) * 3
print(f"Total player slots: {total_players}")
print(f"  Exact matches: {match_stats['exact']} ({match_stats['exact']/total_players*100:.1f}%)")
print(f"  Alias matches: {match_stats['alias']} ({match_stats['alias']/total_players*100:.1f}%)")
print(f"  Not found: {match_stats['not_found']} ({match_stats['not_found']/total_players*100:.1f}%)")
print(f"  TOTAL FOUND: {match_stats['exact'] + match_stats['alias']} ({(match_stats['exact'] + match_stats['alias'])/total_players*100:.1f}%)")

# Show teams with missing players
missing_player_teams = [t for t in teams_sorted if t['missing_players']]
print(f"\n{'='*70}")
print(f"TEAMS WITH MISSING PLAYERS: {len(missing_player_teams)}")
print("="*70)

if missing_player_teams:
    print("First 10 teams with missing players:")
    for team in missing_player_teams[:10]:
        print(f"\n{team['team_name']} (Rating: {team['team_rating']:.2f}):")
        for p in team['missing_players']:
            print(f"    - {p} (assigned default: {DEFAULT_RATING})")

# Show examples of alias matches
alias_matches = []
for team in teams_sorted:
    for i, player in enumerate(team['found_players']):
        if i < len(team['match_types']) and team['match_types'][i] == 'alias':
            alias_matches.append((team['team_name'], player))

if alias_matches:
    print(f"\nExample alias matches (first 10):")
    for i, (team, match) in enumerate(alias_matches[:10]):
        print(f"  {match}")

# Save team ratings
output_file = "output/team_ratings_s12_aliases.json"
with open(output_file, 'w') as f:
    json.dump(teams_sorted, f, indent=2)

print(f"\n{'='*70}")
print("✅ TEAM RATINGS CALCULATED (with alias matching)")
print("="*70)
print(f"Saved to: {output_file}")
print(f"\nNext step: Review results and proceed with division seeding")
