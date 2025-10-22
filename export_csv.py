#!/usr/bin/env python3
"""
Export weighted rankings to CSV
"""

import json
import csv
from datetime import datetime

# Load weighted rankings
with open('output/weighted_rankings.json', 'r') as f:
    players = json.load(f)

# Create CSV filename with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_file = f"output/vesa_leaderboard_{timestamp}.csv"

print("VESA League - CSV Export")
print("="*70)

# Write to CSV
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)

    # Header
    writer.writerow([
        'Rank',
        'Player Name',
        'Division',
        'Total Weighted Points',
        'Raw Points',
        'Total Kills',
        'Total Damage',
        'Lobby',
        'Lobby Weight'
    ])

    # Data rows
    for rank, player in enumerate(players, start=1):
        writer.writerow([
            rank,
            player['player_name'],
            player['division'],
            f"{player['weighted_score']:.2f}",
            f"{player['score']:.0f}",
            player['kills'],
            player['damage'],
            player['lobby'],
            player['lobby_weight']
        ])

print(f"✅ Exported {len(players)} players to CSV")
print(f"📁 File: {csv_file}")

# Also create a simplified version (just top stats)
simple_csv = f"output/vesa_leaderboard_simple_{timestamp}.csv"

with open(simple_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)

    writer.writerow([
        'Rank',
        'Player Name',
        'Total Points',
        'Total Kills',
        'Total Damage'
    ])

    for rank, player in enumerate(players, start=1):
        writer.writerow([
            rank,
            player['player_name'],
            f"{player['weighted_score']:.2f}",
            player['kills'],
            player['damage']
        ])

print(f"✅ Also created simplified version")
print(f"📁 File: {simple_csv}")

# Print summary
print(f"\n{'='*70}")
print("SUMMARY")
print(f"{'='*70}")
print(f"Total players: {len(players)}")
print(f"Total kills: {sum(p['kills'] for p in players):,}")
print(f"Total damage: {sum(p['damage'] for p in players):,}")

print(f"\nTop 5 Players:")
for i, p in enumerate(players[:5], 1):
    print(f"  {i}. {p['player_name']:20} - {p['weighted_score']:6.2f} pts ({p['division']})")

print(f"\n{'='*70}")
print("FILES READY TO USE!")
print(f"{'='*70}")
print(f"\nDetailed CSV (all columns):")
print(f"  {csv_file}")
print(f"\nSimplified CSV (rank, name, points, kills, damage):")
print(f"  {simple_csv}")
print(f"\nOpen these files in Excel, Google Sheets, or any spreadsheet app!")
