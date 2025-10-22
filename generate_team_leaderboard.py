#!/usr/bin/env python3
"""
Generate Team Leaderboard
Clean, presentable format showing team rankings with rosters
"""

import json
import csv
from datetime import datetime

print("VESA League - Team Leaderboard Generator")
print("="*70)

# Load team ratings
with open('output/team_ratings_combined.json', 'r') as f:
    teams = json.load(f)

print(f"Loaded {len(teams)} teams")

# Teams are already sorted by rating
for i, team in enumerate(teams, 1):
    team['rank'] = i

# Generate timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# === CSV OUTPUT (Clean & Simple) ===
csv_file = f'output/team_leaderboard_{timestamp}.csv'
with open(csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Rank', 'Team Name', 'Team Rating', 'Tier', 'Player 1', 'Player 2', 'Player 3',
                     'P1 Rating', 'P2 Rating', 'P3 Rating'])

    for team in teams:
        ratings = team.get('player_ratings', [0, 0, 0])
        writer.writerow([
            team['rank'],
            team['team_name'],
            f"{team['team_rating']:.2f}",
            team['tier'],
            team.get('player1', ''),
            team.get('player2', ''),
            team.get('player3', ''),
            f"{ratings[0]:.2f}" if len(ratings) > 0 else '',
            f"{ratings[1]:.2f}" if len(ratings) > 1 else '',
            f"{ratings[2]:.2f}" if len(ratings) > 2 else ''
        ])

print(f"✓ CSV saved to: {csv_file}")

# === JSON OUTPUT (Detailed) ===
json_file = f'output/team_leaderboard_{timestamp}.json'
with open(json_file, 'w') as f:
    json.dump(teams, f, indent=2)

print(f"✓ JSON saved to: {json_file}")

# === TEXT REPORT (Pretty Print) ===
txt_file = f'output/team_leaderboard_{timestamp}.txt'
with open(txt_file, 'w') as f:
    f.write("="*90 + "\n")
    f.write("VESA LEAGUE - TEAM RANKINGS (SEASON 12)\n")
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("="*90 + "\n\n")

    f.write("Team ratings based on aggregate player performance (S4-S12)\n")
    f.write("Recency Bias: S12(28%), S11(24%), S8(18%), S6(14%), S5(10%), S4(6%)\n")
    f.write("Top Lobby Bonus: 15% for players in elite divisions\n\n")

    # Top 50 Teams
    f.write("="*90 + "\n")
    f.write("TOP 50 TEAMS\n")
    f.write("="*90 + "\n")
    f.write(f"{'Rank':<6} {'Team Name':<30} {'Rating':<10} {'Tier':<6} {'Players Found'}\n")
    f.write("-"*90 + "\n")

    for team in teams[:50]:
        found = f"{len(team.get('found_players', []))}/3"
        f.write(f"{team['rank']:<6} {team['team_name'][:29]:<30} {team['team_rating']:<10.2f} "
                f"{team['tier']:<6} {found}\n")

    # Tier distribution
    f.write("\n" + "="*90 + "\n")
    f.write("TIER DISTRIBUTION\n")
    f.write("="*90 + "\n")

    tier_counts = {}
    for team in teams:
        tier = team['tier']
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    total_teams = len(teams)
    tier_order = ['S+', 'S', 'A+', 'A', 'B+', 'B', 'C+', 'C', 'C-', 'D+', 'D', 'D-']
    for tier in tier_order:
        count = tier_counts.get(tier, 0)
        if count > 0:
            pct = (count / total_teams) * 100
            bar = '█' * int(pct / 2)
            f.write(f"Tier {tier:3} ({count:>4} teams, {pct:>5.1f}%): {bar}\n")

    # Top 20 with full rosters
    f.write("\n" + "="*90 + "\n")
    f.write("TOP 20 TEAMS - FULL ROSTERS\n")
    f.write("="*90 + "\n\n")

    for i, team in enumerate(teams[:20], 1):
        f.write(f"{i}. {team['team_name']} - {team['team_rating']:.2f} (Tier {team['tier']})\n")

        # Players with ratings
        ratings = team.get('player_ratings', [])
        players = [
            team.get('player1', 'Unknown'),
            team.get('player2', 'Unknown'),
            team.get('player3', 'Unknown')
        ]

        for j, player in enumerate(players):
            rating_str = f"{ratings[j]:.2f}" if j < len(ratings) else "N/A"
            match_type = team.get('match_types', [])[j] if j < len(team.get('match_types', [])) else 'unknown'
            f.write(f"   • {player}: {rating_str}")
            if match_type == 'alias':
                f.write(" (matched via alias)")
            elif j in range(len(team.get('missing_players', []))):
                f.write(" (not found - default rating)")
            f.write("\n")

        f.write("\n")

    # Division placement summary
    f.write("="*90 + "\n")
    f.write("S12 DIVISION PLACEMENTS\n")
    f.write("="*90 + "\n\n")

    # Load division assignments
    try:
        with open('output/division_assignments.json', 'r') as div_f:
            divisions = json.load(div_f)

        for div_num in range(1, 8):
            div_data = divisions['divisions'].get(str(div_num), {})
            div_teams = div_data.get('teams', [])
            if div_teams:
                day = div_data.get('day', 'Unknown')
                avg = div_data['stats']['avg_rating']
                f.write(f"Division {div_num} ({day}): {len(div_teams)} teams, Avg Rating: {avg:.2f}\n")
                f.write(f"  Top 3: ")
                top_3 = div_teams[:3]
                f.write(", ".join([f"{t['team_name']} ({t['rating']:.1f})" for t in top_3]))
                f.write("\n\n")
    except:
        f.write("Division assignments not available\n\n")

print(f"✓ Text report saved to: {txt_file}")

# === SUMMARY STATISTICS ===
print("\n" + "="*70)
print("TEAM LEADERBOARD SUMMARY")
print("-"*70)
print(f"Total Teams: {len(teams)}")
print(f"\nTop 10 Teams:")
for i, team in enumerate(teams[:10], 1):
    print(f"  {i}. {team['team_name']}: {team['team_rating']:.2f} (Tier {team['tier']})")

print(f"\nTier Distribution:")
tier_order = ['S+', 'S', 'A+', 'A', 'B+', 'B', 'C+', 'C', 'C-', 'D+', 'D', 'D-']
for tier in tier_order:
    count = tier_counts.get(tier, 0)
    if count > 0:
        pct = (count / total_teams) * 100
        print(f"  Tier {tier:3}: {count:4} teams ({pct:5.1f}%)")

print(f"\nPlayer Match Rate:")
total_slots = len(teams) * 3
exact = sum(t.get('match_types', []).count('exact') for t in teams)
alias = sum(t.get('match_types', []).count('alias') for t in teams)
missing = sum(len(t.get('missing_players', [])) for t in teams)
print(f"  Exact matches: {exact}/{total_slots} ({exact/total_slots*100:.1f}%)")
print(f"  Alias matches: {alias}/{total_slots} ({alias/total_slots*100:.1f}%)")
print(f"  Not found: {missing}/{total_slots} ({missing/total_slots*100:.1f}%)")

print(f"\n✓ All team leaderboard files generated successfully!")
