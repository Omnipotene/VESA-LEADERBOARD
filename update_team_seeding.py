#!/usr/bin/env python3
"""
Update team seeding with Power Rankings
Replaces aggregate-only ratings with composite power scores
"""

import json

print("VESA League - Team Seeding Update (Power Rankings)")
print("="*70)

# Load existing team ratings (has roster info)
print("\nLoading existing team ratings...")
with open('output/team_ratings_combined.json', 'r') as f:
    team_ratings = json.load(f)

print(f"✓ Loaded {len(team_ratings)} teams with roster data")

# Load power rankings
print("\nLoading power rankings...")
with open('output/power_rankings.json', 'r') as f:
    power_rankings = json.load(f)

# Build lookup: team_name -> power_score
power_lookup = {team['team_name']: team for team in power_rankings}
print(f"✓ Loaded {len(power_rankings)} teams with power scores")

# Define tier thresholds based on power score distribution
# Calculate percentiles for fair tier assignment
power_scores = sorted([team['power_score'] for team in power_rankings], reverse=True)

def get_percentile(value, sorted_list):
    """Get percentile rank of value in sorted list"""
    if not sorted_list:
        return 0
    count_above = sum(1 for v in sorted_list if v > value)
    return (count_above / len(sorted_list)) * 100

def assign_tier(power_score):
    """Assign tier based on power score percentile"""
    percentile = get_percentile(power_score, power_scores)

    if percentile < 5:  # Top 5%
        return 'A', 'Elite'
    elif percentile < 15:  # Top 15%
        return 'B', 'Upper-Mid Skill'
    elif percentile < 40:  # Top 40%
        return 'C', 'Mid Skill'
    else:  # Bottom 60%
        return 'D', 'Developing'

# Update team ratings with power scores
print("\nUpdating team ratings with power scores...")
updated_teams = []
teams_updated = 0
teams_not_in_power = []

for team in team_ratings:
    team_name = team['team_name']

    # Try to find this team in power rankings
    power_data = power_lookup.get(team_name)

    if power_data:
        # Update with power score
        team['team_rating'] = power_data['power_score']
        team['power_rank'] = power_data['power_rank']

        # Update tier based on new rating
        tier, tier_desc = assign_tier(power_data['power_score'])
        team['tier'] = tier
        team['tier_desc'] = tier_desc

        # Add power ranking components for reference
        team['elo'] = power_data['elo']
        team['consistency_score'] = power_data['consistency_score']
        team['form_score'] = power_data['form_score']
        team['games_played'] = power_data['games_played']

        teams_updated += 1
    else:
        # Team not in power rankings (no match history)
        # Keep their original aggregate rating
        teams_not_in_power.append(team_name)

    updated_teams.append(team)

# Sort by team rating (highest first)
updated_teams_sorted = sorted(updated_teams, key=lambda x: x['team_rating'], reverse=True)

# Save updated ratings
output_file = 'output/team_ratings_combined.json'
with open(output_file, 'w') as f:
    json.dump(updated_teams_sorted, f, indent=2)

# Statistics
print("\n" + "="*70)
print("UPDATE COMPLETE:")
print("-"*70)
print(f"Total teams: {len(team_ratings)}")
print(f"Updated with power scores: {teams_updated}")
print(f"Kept aggregate ratings (no match data): {len(teams_not_in_power)}")

if teams_not_in_power:
    print(f"\nTeams not in power rankings (kept aggregate ratings):")
    for team_name in teams_not_in_power[:20]:
        print(f"  - {team_name}")
    if len(teams_not_in_power) > 20:
        print(f"  ... and {len(teams_not_in_power) - 20} more")

# Show new tier distribution
print(f"\n{'='*70}")
print("NEW TIER DISTRIBUTION:")
print("-"*70)
tier_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
for team in updated_teams_sorted:
    tier_counts[team['tier']] += 1

for tier in ['A', 'B', 'C', 'D']:
    count = tier_counts[tier]
    pct = (count / len(updated_teams_sorted)) * 100
    print(f"Tier {tier}: {count} teams ({pct:.1f}%)")

# Show top 20 teams
print(f"\n{'='*70}")
print("TOP 20 TEAMS (NEW POWER RANKINGS):")
print("-"*70)
print(f"{'Rank':<5} {'Team':<30} {'Power':<8} {'Tier':<5} {'Elo':<6} {'Cons':<6} {'Form':<6}")
print("-"*70)

for i, team in enumerate(updated_teams_sorted[:20], 1):
    power = team.get('team_rating', 0)
    elo = team.get('elo', 0)
    cons = team.get('consistency_score', 0)
    form = team.get('form_score', 0)
    tier = team.get('tier', '?')

    print(f"{i:<5} {team['team_name'][:29]:<30} {power:<8.1f} {tier:<5} {elo:<6.0f} {cons:<6.1f} {form:<6.1f}")

print(f"\n✓ Updated team ratings saved to: {output_file}")
print(f"\nNext step: Regenerate division assignments with new ratings")
print("  python3 division_seeding.py")
