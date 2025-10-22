#!/usr/bin/env python3
"""
Export division assignments to CSV format
"""

import json
import csv

print("VESA League - Export Division Assignments to CSV")
print("="*70)

# Load division assignments
with open('output/division_assignments.json', 'r') as f:
    data = json.load(f)

# Prepare CSV output
csv_rows = []

for div_num in range(1, 8):
    div_data = data['divisions'][str(div_num)]
    day = div_data['day']
    teams = div_data['teams']

    for rank, team in enumerate(teams, 1):
        csv_rows.append({
            'Division': div_num,
            'Day': day,
            'Rank_in_Division': rank,
            'Team_Name': team['team_name'],
            'Team_Rating': round(team['rating'], 2),
            'Tier': team['tier'],
            'Schedule_Constraint': team['schedule_constraint']
        })

# Write to CSV
output_file = 'output/division_assignments.csv'
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'Division', 'Day', 'Rank_in_Division', 'Team_Name',
        'Team_Rating', 'Tier', 'Schedule_Constraint'
    ])
    writer.writeheader()
    writer.writerows(csv_rows)

print(f"✅ Exported {len(csv_rows)} team assignments to: {output_file}")

# Also create a summary report
print("\n" + "="*70)
print("DIVISION SUMMARY REPORT")
print("="*70)

for div_num in range(1, 8):
    div_data = data['divisions'][str(div_num)]
    stats = div_data['stats']
    day = div_data['day']

    print(f"\nDivision {div_num} ({day}):")
    print(f"  Teams: {stats['count']}")
    print(f"  Avg Rating: {stats['avg_rating']:.2f}")
    print(f"  Rating Range: {stats['min_rating']:.2f} - {stats['max_rating']:.2f}")

    # Show top 3 teams
    print(f"  Top 3 Teams:")
    for i, team in enumerate(div_data['teams'][:3], 1):
        print(f"    {i}. {team['team_name']} ({team['rating']:.2f})")

# Show unplaced teams
if data['unplaced_teams']:
    print("\n" + "="*70)
    print("⚠️  UNPLACED TEAMS - MANUAL REVIEW NEEDED")
    print("="*70)
    for team in data['unplaced_teams']:
        print(f"\nTeam: {team['team_name']}")
        print(f"  Rating: {team['rating']:.2f}")
        print(f"  Tier: {team['tier']}")
        print(f"  Schedule Constraint: {team['schedule_constraint']}")
        print(f"  Compatible Divisions: {team['compatible_divisions'] if team['compatible_divisions'] else 'NONE'}")
        print(f"  ⚠️  This team cannot play on any of the scheduled days (Mon/Wed/Thu)")

print("\n" + "="*70)
print(f"Total: {data['stats']['placed_teams']}/{data['stats']['total_teams']} teams placed")
print("="*70)
