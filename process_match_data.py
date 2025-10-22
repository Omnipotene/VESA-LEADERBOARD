#!/usr/bin/env python3
"""
Process raw match data into normalized format
- Extract team placements per game
- Map team names to canonical IDs using alias system
- Create chronological match history
"""

import json
from collections import defaultdict
import re

print("VESA League - Match Data Processor")
print("="*70)

# Load raw match data
print("\nLoading raw match data...")
with open('output/match_data_all_tournaments.json', 'r') as f:
    raw_data = json.load(f)

print(f"✓ Loaded {len(raw_data)} tournaments")

# Load alias mappings for team name normalization
with open('data/player_aliases.json', 'r') as f:
    aliases_data = json.load(f)

# Build team name normalization map
# This maps various team name variations to canonical team names
team_aliases = {}
print("\nBuilding team alias map...")

# Extract unique team names from raw data to see what we're working with
all_team_names = set()
for tournament, data in raw_data.items():
    for game in data.get('games', []):
        for team in game.get('teams', []):
            team_name = team.get('name', '').strip()
            if team_name:
                all_team_names.add(team_name)

print(f"✓ Found {len(all_team_names)} unique team names across all games")

# Process all games chronologically
print("\nProcessing games chronologically...")
all_games = []

for tournament_name, tournament_data in raw_data.items():
    # Parse season and division from tournament name
    season = tournament_name.split('_')[0]  # e.g., 'S4', 'S5', etc.
    division = '_'.join(tournament_name.split('_')[1:])  # e.g., 'Pinnacle', 'Ascendant'

    for game in tournament_data.get('games', []):
        game_id = game.get('id')
        timestamp = game.get('match_start', 0)
        map_name = game.get('map_name', 'Unknown')

        # Extract team results
        teams_in_game = []
        for team in game.get('teams', []):
            team_name = team.get('name', '').strip()
            overall_stats = team.get('overall_stats', {})

            teams_in_game.append({
                'team_name': team_name,
                'team_name_raw': team_name,  # Keep original for reference
                'placement': overall_stats.get('teamPlacement', 99),
                'kills': overall_stats.get('kills', 0),
                'damage': overall_stats.get('damageDealt', 0),
                'survival_time': overall_stats.get('survivalTime', 0),
                'score': overall_stats.get('score', 0)
            })

        # Create normalized game record
        all_games.append({
            'game_id': game_id,
            'timestamp': timestamp,
            'season': season,
            'division': division,
            'tournament': tournament_name,
            'map': map_name,
            'teams': sorted(teams_in_game, key=lambda x: x['placement'])
        })

# Sort all games chronologically
all_games.sort(key=lambda x: x['timestamp'])

print(f"✓ Processed {len(all_games)} games")
print(f"  Date range: {min(g['timestamp'] for g in all_games)} to {max(g['timestamp'] for g in all_games)}")

# Save processed games
output_file = 'output/processed_matches.json'
with open(output_file, 'w') as f:
    json.dump(all_games, f, indent=2)

# Build team-centric view
print("\nBuilding team match history...")
team_history = defaultdict(list)

for game in all_games:
    for team_result in game['teams']:
        team_name = team_result['team_name']

        team_history[team_name].append({
            'game_id': game['game_id'],
            'timestamp': game['timestamp'],
            'season': game['season'],
            'division': game['division'],
            'tournament': game['tournament'],
            'map': game['map'],
            'placement': team_result['placement'],
            'kills': team_result['kills'],
            'damage': team_result['damage'],
            'score': team_result['score']
        })

# Save team history
team_history_sorted = {
    team: sorted(games, key=lambda x: x['timestamp'])
    for team, games in team_history.items()
}

output_file_teams = 'output/team_match_history.json'
with open(output_file_teams, 'w') as f:
    json.dump(team_history_sorted, f, indent=2)

# Statistics
print("\n" + "="*70)
print("PROCESSING SUMMARY:")
print("-"*70)
print(f"Total games processed: {len(all_games)}")
print(f"Unique teams found: {len(team_history)}")
print(f"Average games per team: {sum(len(games) for games in team_history.values()) / len(team_history):.1f}")

# Show top teams by game count
top_teams = sorted(team_history.items(), key=lambda x: len(x[1]), reverse=True)[:10]
print(f"\nTop 10 teams by games played:")
for i, (team, games) in enumerate(top_teams, 1):
    avg_placement = sum(g['placement'] for g in games) / len(games)
    print(f"  {i}. {team}: {len(games)} games (avg placement: {avg_placement:.1f})")

# Season distribution
season_counts = defaultdict(int)
for game in all_games:
    season_counts[game['season']] += 1

print(f"\nGames per season:")
for season in sorted(season_counts.keys()):
    print(f"  {season}: {season_counts[season]} games")

print(f"\n✓ Processed data saved to:")
print(f"  - {output_file}")
print(f"  - {output_file_teams}")

print(f"\nNext step: Build Elo rating system")
print("  python3 calculate_elo_ratings.py")
