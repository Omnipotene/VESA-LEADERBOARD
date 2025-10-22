#!/usr/bin/env python3
"""
Schedule-Aware Division Seeding Algorithm
Assigns 158 teams to 7 divisions based on:
1. Schedule compatibility (hard constraint)
2. Skill balance (optimization goal)
"""

import json
import csv
from collections import defaultdict

print("VESA League - Schedule-Aware Division Seeding")
print("="*70)

# Division schedule configuration
DIVISION_SCHEDULE = {
    1: 'Thursday',
    2: 'Wednesday',
    3: 'Monday',
    4: 'Thursday',
    5: 'Monday',
    6: 'Wednesday',
    7: 'Monday'
}

print(f"\nDivision Schedule:")
for div, day in sorted(DIVISION_SCHEDULE.items()):
    print(f"  Division {div}: {day}")
print()

# Load team ratings
with open('output/team_ratings_combined.json', 'r') as f:
    teams_with_ratings = json.load(f)

print(f"Loaded {len(teams_with_ratings)} teams with ratings")

# Create team rating lookup
team_rating_lookup = {t['team_name']: t for t in teams_with_ratings}

def parse_constraints(constraint_str):
    """Parse schedule constraint string into list of days team CANNOT play"""
    if not constraint_str or constraint_str.lower() in ['no scheduling issues', '']:
        return []

    cannot_play = []
    constraint_lower = constraint_str.lower()

    if 'monday' in constraint_lower:
        cannot_play.append('Monday')
    if 'tuesday' in constraint_lower:
        cannot_play.append('Tuesday')
    if 'wednesday' in constraint_lower:
        cannot_play.append('Wednesday')
    if 'thursday' in constraint_lower:
        cannot_play.append('Thursday')
    if 'friday' in constraint_lower:
        cannot_play.append('Friday')

    return cannot_play

# Load schedule constraints from FINAL PLACEMENTS
# Exclude waitlisted teams (teams after "Waitlist (Line 149)" row)
teams_data = []
waitlisted_teams = []
past_waitlist_marker = False

with open('data/rosters_final_placements.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        team_name = row.get('Team Name', '').strip()

        # Check for waitlist marker
        if 'waitlist' in team_name.lower():
            past_waitlist_marker = True
            continue

        if not team_name or 'Lobby' in team_name:
            continue

        constraint = row.get('Are there any days of the week your team CAN NOT play? (We can\'t promise to accommodate you as leagues are separated by skill)', '').strip()

        # Get rating data if available
        rating_data = team_rating_lookup.get(team_name, None)

        if rating_data:
            team_rating = rating_data['team_rating']
            tier = rating_data['tier']
        else:
            # Team not in ratings (shouldn't happen, but fallback)
            team_rating = 80.0
            tier = 'D'

        team_info = {
            'team_name': team_name,
            'rating': team_rating,
            'tier': tier,
            'schedule_constraint': constraint,
            'cannot_play': parse_constraints(constraint)
        }

        # Separate waitlisted teams from active teams
        if past_waitlist_marker:
            waitlisted_teams.append(team_info)
        else:
            teams_data.append(team_info)

print(f"Processed {len(teams_data)} teams from FINAL PLACEMENTS")
if waitlisted_teams:
    print(f"⚠️  Excluded {len(waitlisted_teams)} waitlisted teams (not participating):")
    for team in waitlisted_teams[:10]:  # Show first 10
        print(f"    - {team['team_name']}")

# Analyze schedule compatibility
def get_compatible_divisions(team):
    """Return list of division numbers this team can play in"""
    cannot_play = team['cannot_play']
    compatible = []

    for div_num, div_day in DIVISION_SCHEDULE.items():
        if div_day not in cannot_play:
            compatible.append(div_num)

    return compatible

# Calculate compatibility for all teams
schedule_stats = {
    'all_compatible': 0,
    'limited_options': 0,
    'no_options': 0
}

for team in teams_data:
    team['compatible_divisions'] = get_compatible_divisions(team)
    num_compatible = len(team['compatible_divisions'])

    if num_compatible == 7:
        schedule_stats['all_compatible'] += 1
    elif num_compatible > 0:
        schedule_stats['limited_options'] += 1
    else:
        schedule_stats['no_options'] += 1

print("\nSchedule Compatibility Analysis:")
print("-"*70)
print(f"Teams with all divisions available: {schedule_stats['all_compatible']}")
print(f"Teams with limited options: {schedule_stats['limited_options']}")
print(f"Teams with NO compatible divisions: {schedule_stats['no_options']}")

# Show teams with no compatible divisions (need manual review)
no_option_teams = [t for t in teams_data if len(t['compatible_divisions']) == 0]
if no_option_teams:
    print(f"\n⚠️  TEAMS WITH NO COMPATIBLE DIVISIONS:")
    print("-"*70)
    for team in no_option_teams:
        print(f"  {team['team_name']}: Cannot play {', '.join(team['cannot_play'])}")
    print("\nThese teams will need manual placement or schedule adjustment.")

# Seeding Algorithm: Top teams play top teams (Division 1 = highest rated)
# Sort teams by rating (highest to lowest)
teams_sorted = sorted(teams_data, key=lambda x: x['rating'], reverse=True)

# Initialize divisions
divisions = {i: [] for i in range(1, 8)}

print("\n" + "="*70)
print("SEEDING TEAMS INTO DIVISIONS (Skill-Grouped)")
print("="*70)

# Track division sizes
division_sizes = {i: 0 for i in range(1, 8)}

# Calculate exact target sizes dynamically based on actual team count
total_active_teams = len(teams_sorted)
base_per_division = total_active_teams // 7
extra_teams = total_active_teams % 7

# First 'extra_teams' divisions get +1 team
max_per_division = {}
for i in range(1, 8):
    if i <= extra_teams:
        max_per_division[i] = base_per_division + 1
    else:
        max_per_division[i] = base_per_division

print(f"\nTarget division sizes (for {total_active_teams} active teams):")
for div, size in max_per_division.items():
    print(f"  Division {div}: {size} teams")

# Seeding process: Fill divisions top-to-bottom
# Div 1 gets top 23 teams, Div 2 gets next 23, etc.
# IGNORE SCHEDULE CONSTRAINTS - place all teams by skill rating
unplaced_teams = []

for team in teams_sorted:
    # Try to place in the highest-priority division that has space
    # Ignore schedule constraints - just fill divisions sequentially
    placed = False
    for div_num in range(1, 8):
        # Check if division has space (IGNORE schedule compatibility)
        if division_sizes[div_num] < max_per_division[div_num]:
            divisions[div_num].append(team)
            division_sizes[div_num] += 1
            placed = True
            break

    if not placed:
        # This should never happen if math is correct
        unplaced_teams.append(team)

print(f"\nPlaced: {sum(division_sizes.values())} teams")
print(f"Unplaced: {len(unplaced_teams)} teams")

# Show division composition
print("\n" + "="*70)
print("DIVISION COMPOSITION:")
print("="*70)

for div_num in range(1, 8):
    teams_in_div = divisions[div_num]
    day = DIVISION_SCHEDULE[div_num]

    if teams_in_div:
        ratings = [t['rating'] for t in teams_in_div]
        avg_rating = sum(ratings) / len(ratings)
        max_rating = max(ratings)
        min_rating = min(ratings)

        tier_counts = defaultdict(int)
        for t in teams_in_div:
            tier_counts[t['tier']] += 1

        tier_str = ', '.join([f"{tier}:{count}" for tier, count in sorted(tier_counts.items())])
    else:
        avg_rating = 0
        max_rating = 0
        min_rating = 0
        tier_str = "Empty"

    print(f"\nDivision {div_num} ({day}):")
    print(f"  Teams: {len(teams_in_div)}/{max_per_division[div_num]}")
    print(f"  Rating: Avg={avg_rating:.2f}, Max={max_rating:.2f}, Min={min_rating:.2f}")
    print(f"  Tiers: {tier_str}")

# Show unplaced teams
if unplaced_teams:
    print("\n" + "="*70)
    print(f"⚠️  UNPLACED TEAMS ({len(unplaced_teams)}):")
    print("="*70)
    for team in unplaced_teams:
        compat_str = f"Compatible: Div {', '.join(map(str, team['compatible_divisions']))}" if team['compatible_divisions'] else "NO COMPATIBLE DIVISIONS"
        print(f"  {team['team_name']} (Rating: {team['rating']:.2f}) - {compat_str}")

# Export results
output_data = {
    'divisions': {},
    'unplaced_teams': [],
    'stats': {
        'total_teams': len(teams_data),
        'placed_teams': sum(division_sizes.values()),
        'unplaced_teams': len(unplaced_teams)
    }
}

for div_num in range(1, 8):
    teams_in_div = divisions[div_num]
    output_data['divisions'][div_num] = {
        'day': DIVISION_SCHEDULE[div_num],
        'teams': [
            {
                'team_name': t['team_name'],
                'rating': t['rating'],
                'tier': t['tier'],
                'schedule_constraint': t['schedule_constraint']
            }
            for t in sorted(teams_in_div, key=lambda x: x['rating'], reverse=True)
        ],
        'stats': {
            'count': len(teams_in_div),
            'avg_rating': sum(t['rating'] for t in teams_in_div) / len(teams_in_div) if teams_in_div else 0,
            'max_rating': max((t['rating'] for t in teams_in_div), default=0),
            'min_rating': min((t['rating'] for t in teams_in_div), default=0)
        }
    }

output_data['unplaced_teams'] = [
    {
        'team_name': t['team_name'],
        'rating': t['rating'],
        'tier': t['tier'],
        'schedule_constraint': t['schedule_constraint'],
        'compatible_divisions': t['compatible_divisions']
    }
    for t in unplaced_teams
]

# Save to JSON
with open('output/division_assignments.json', 'w') as f:
    json.dump(output_data, f, indent=2)

print("\n" + "="*70)
print("✅ DIVISION SEEDING COMPLETE")
print("="*70)
print(f"Saved to: output/division_assignments.json")
