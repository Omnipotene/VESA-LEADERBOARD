#!/usr/bin/env python3
"""
Deduplicate players and export final CSV
Keep only the best weighted score for each player
"""

import json
import csv
from datetime import datetime

# Load weighted rankings
with open('output/weighted_rankings.json', 'r') as f:
    all_players = json.load(f)

print("VESA League - Deduplication & Final Export")
print("="*70)
print(f"Total entries before deduplication: {len(all_players)}")

# Deduplicate - keep the best weighted score for each player
player_best = {}

for player in all_players:
    name = player['player_name']

    # If we haven't seen this player, or this entry has a better weighted score
    if name not in player_best or player['weighted_score'] > player_best[name]['weighted_score']:
        player_best[name] = player

# Convert back to list and sort by weighted score
unique_players = sorted(player_best.values(), key=lambda x: x['weighted_score'], reverse=True)

print(f"Unique players after deduplication: {len(unique_players)}")
print(f"Duplicates removed: {len(all_players) - len(unique_players)}")

# Create CSV filename with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_file = f"output/vesa_leaderboard_final_{timestamp}.csv"

# Write detailed CSV
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)

    writer.writerow([
        'Rank',
        'Player Name',
        'Division',
        'Weighted Points',
        'Raw Points',
        'Kills',
        'Damage',
        'Lobby',
        'Lobby Weight'
    ])

    for rank, player in enumerate(unique_players, start=1):
        writer.writerow([
            rank,
            player['player_name'],
            player['division'],
            f"{player['weighted_score']:.2f}",
            f"{player['score']:.0f}",
            player['kills'],
            player['damage'],
            player['lobby'],
            f"{player['lobby_weight']:.2f}"
        ])

print(f"\n✅ Exported {len(unique_players)} unique players")
print(f"📁 Detailed CSV: {csv_file}")

# Create simplified version
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

    for rank, player in enumerate(unique_players, start=1):
        writer.writerow([
            rank,
            player['player_name'],
            f"{player['weighted_score']:.2f}",
            player['kills'],
            player['damage']
        ])

print(f"📁 Simple CSV: {simple_csv}")

# Save deduplicated JSON
dedup_json = "output/unique_players_ranked.json"
with open(dedup_json, 'w') as f:
    json.dump(unique_players, f, indent=2)

print(f"📁 JSON: {dedup_json}")

# Print summary
print(f"\n{'='*70}")
print("FINAL LEADERBOARD - TOP 20")
print(f"{'='*70}")
print(f"{'Rank':<5} {'Player':<20} {'Division':<27} {'Weighted Pts':<12} {'Kills':<6}")
print("-"*70)

for i, p in enumerate(unique_players[:20], 1):
    print(f"{i:<5} {p['player_name']:<20} {p['division']:<27} "
          f"{p['weighted_score']:<12.2f} {p['kills']:<6}")

# Division breakdown of top 20
print(f"\n{'='*70}")
print("TOP 20 DIVISION BREAKDOWN:")
print(f"{'='*70}")

top20_divs = {}
for p in unique_players[:20]:
    div = p['division']
    top20_divs[div] = top20_divs.get(div, 0) + 1

for div, count in sorted(top20_divs.items(), key=lambda x: x[1], reverse=True):
    print(f"  {div:30} {count} players")

# Overall stats
print(f"\n{'='*70}")
print("OVERALL STATISTICS:")
print(f"{'='*70}")
print(f"Total unique players: {len(unique_players)}")
print(f"Total kills: {sum(p['kills'] for p in unique_players):,}")
print(f"Total damage: {sum(p['damage'] for p in unique_players):,}")

print(f"\n{'='*70}")
print("✅ EXPORT COMPLETE!")
print(f"{'='*70}")
print("\nYour files are ready in the output/ folder:")
print(f"  • {csv_file}")
print(f"  • {simple_csv}")
print("\nOpen in Excel or Google Sheets!")
