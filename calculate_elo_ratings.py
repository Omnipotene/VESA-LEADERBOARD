#!/usr/bin/env python3
"""
Calculate Elo ratings for all teams based on game-by-game performance
Uses Battle Royale-specific Elo algorithm (20-team games)
"""

import json
import math
from collections import defaultdict

print("VESA League - Elo Rating Calculator")
print("="*70)

# Elo parameters
INITIAL_ELO = 1500  # Starting rating for all teams
K_FACTOR = 32       # How much ratings change per game (higher = more volatile)

def calculate_expected_placement(team_elo, opponent_elos):
    """
    Calculate expected placement for a team against opponents
    In battle royale, we compare against all other teams
    Returns expected placement (1 = expected to win, 20 = expected to place last)
    """
    # Count how many teams we expect to beat
    teams_expected_to_beat = 0

    for opp_elo in opponent_elos:
        # Probability of beating this opponent
        prob = 1 / (1 + 10 ** ((opp_elo - team_elo) / 400))
        teams_expected_to_beat += prob

    # Expected placement is inverse of teams we beat
    # If we beat 15 teams, we expect to place ~5th (20 - 15)
    expected_placement = len(opponent_elos) + 1 - teams_expected_to_beat

    return expected_placement

def calculate_elo_change(actual_placement, expected_placement, k_factor):
    """
    Calculate Elo rating change based on actual vs expected placement
    Better placement than expected = positive change
    Worse placement than expected = negative change
    """
    # Normalize placements to 0-1 scale where 0 = 1st place, 1 = last place
    # This makes the math cleaner
    max_placement = 20  # Assume 20-team games

    # Lower placement number = better performance
    # So we invert: 1st place = 1.0, 20th place = 0.0
    actual_score = (max_placement - actual_placement + 1) / max_placement
    expected_score = (max_placement - expected_placement + 1) / max_placement

    # Elo change
    change = k_factor * (actual_score - expected_score)

    return change

# Load processed match data
print("\nLoading match data...")
with open('output/processed_matches.json', 'r') as f:
    all_games = json.load(f)

print(f"✓ Loaded {len(all_games)} games")

# Initialize Elo ratings for all teams
team_elos = defaultdict(lambda: INITIAL_ELO)
team_elo_history = defaultdict(list)  # Track rating changes over time

# Process games chronologically to update Elo
print("\nCalculating Elo ratings chronologically...")
games_processed = 0

for game in all_games:
    game_id = game['game_id']
    teams_in_game = game['teams']

    # Get current Elos for all teams in this game
    current_elos = {}
    for team_data in teams_in_game:
        team_name = team_data['team_name']
        current_elos[team_name] = team_elos[team_name]

    # Calculate Elo changes for each team
    elo_changes = {}

    for team_data in teams_in_game:
        team_name = team_data['team_name']
        actual_placement = team_data['placement']
        team_elo = current_elos[team_name]

        # Get opponent Elos (all other teams in this game)
        opponent_elos = [elo for name, elo in current_elos.items() if name != team_name]

        # Calculate expected placement
        expected_placement = calculate_expected_placement(team_elo, opponent_elos)

        # Calculate Elo change
        elo_change = calculate_elo_change(actual_placement, expected_placement, K_FACTOR)
        elo_changes[team_name] = elo_change

    # Apply Elo changes and record history
    for team_data in teams_in_game:
        team_name = team_data['team_name']
        old_elo = team_elos[team_name]
        new_elo = old_elo + elo_changes[team_name]
        team_elos[team_name] = new_elo

        # Record this rating point in history
        team_elo_history[team_name].append({
            'game_id': game_id,
            'timestamp': game['timestamp'],
            'season': game['season'],
            'division': game['division'],
            'placement': team_data['placement'],
            'elo_before': old_elo,
            'elo_after': new_elo,
            'elo_change': elo_changes[team_name]
        })

    games_processed += 1
    if games_processed % 100 == 0:
        print(f"  Processed {games_processed}/{len(all_games)} games...")

print(f"✓ Processed all {games_processed} games")

# Create final Elo rankings
final_elos = []
for team_name, final_elo in team_elos.items():
    games_played = len(team_elo_history[team_name])

    # Calculate stats
    placements = [g['placement'] for g in team_elo_history[team_name]]
    avg_placement = sum(placements) / len(placements) if placements else 20

    # Get min/max Elo
    elo_values = [g['elo_after'] for g in team_elo_history[team_name]]
    peak_elo = max(elo_values) if elo_values else INITIAL_ELO
    lowest_elo = min(elo_values) if elo_values else INITIAL_ELO

    final_elos.append({
        'team_name': team_name,
        'current_elo': final_elo,
        'peak_elo': peak_elo,
        'lowest_elo': lowest_elo,
        'games_played': games_played,
        'avg_placement': avg_placement,
        'elo_change_total': final_elo - INITIAL_ELO
    })

# Sort by current Elo
final_elos_sorted = sorted(final_elos, key=lambda x: x['current_elo'], reverse=True)

# Add ranks
for i, team in enumerate(final_elos_sorted, 1):
    team['elo_rank'] = i

# Save Elo ratings
output_file = 'output/elo_ratings.json'
with open(output_file, 'w') as f:
    json.dump(final_elos_sorted, f, indent=2)

# Save Elo history
output_file_history = 'output/elo_history.json'
with open(output_file_history, 'w') as f:
    json.dump(dict(team_elo_history), f, indent=2)

# Statistics
print("\n" + "="*70)
print("ELO CALCULATION SUMMARY:")
print("-"*70)
print(f"Teams rated: {len(final_elos_sorted)}")
print(f"K-Factor used: {K_FACTOR}")
print(f"Initial Elo: {INITIAL_ELO}")

print(f"\nElo distribution:")
elo_values = [team['current_elo'] for team in final_elos_sorted]
print(f"  Highest: {max(elo_values):.0f}")
print(f"  Median: {sorted(elo_values)[len(elo_values)//2]:.0f}")
print(f"  Mean: {sum(elo_values)/len(elo_values):.0f}")
print(f"  Lowest: {min(elo_values):.0f}")
print(f"  Range: {max(elo_values) - min(elo_values):.0f}")

# Show top 20
print(f"\n{'='*70}")
print("TOP 20 TEAMS BY ELO:")
print("-"*70)
print(f"{'Rank':<5} {'Team':<30} {'Elo':<8} {'Games':<7} {'Avg Place':<10} {'Peak Elo':<9}")
print("-"*70)

for team in final_elos_sorted[:20]:
    print(f"{team['elo_rank']:<5} {team['team_name'][:29]:<30} {team['current_elo']:<8.0f} {team['games_played']:<7} {team['avg_placement']:<10.1f} {team['peak_elo']:<9.0f}")

# Show teams that gained/lost most Elo
print(f"\n{'='*70}")
print("BIGGEST GAINERS (vs starting 1500):")
print("-"*70)
gainers = sorted(final_elos_sorted, key=lambda x: x['elo_change_total'], reverse=True)[:10]
for i, team in enumerate(gainers, 1):
    print(f"{i}. {team['team_name']}: +{team['elo_change_total']:.0f} Elo ({team['games_played']} games)")

print(f"\nBIGGEST DECLINERS (vs starting 1500):")
print("-"*70)
decliners = sorted(final_elos_sorted, key=lambda x: x['elo_change_total'])[:10]
for i, team in enumerate(decliners, 1):
    print(f"{i}. {team['team_name']}: {team['elo_change_total']:.0f} Elo ({team['games_played']} games)")

print(f"\n✓ Elo ratings saved to:")
print(f"  - {output_file}")
print(f"  - {output_file_history}")

print(f"\nNext step: Calculate consistency and hot streak metrics")
print("  python3 calculate_advanced_metrics.py")
