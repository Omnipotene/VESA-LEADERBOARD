#!/usr/bin/env python3
"""
Generate Individual Player Leaderboard
Clean, presentable format for sharing
"""

import json
import csv
from datetime import datetime

print("VESA League - Individual Player Leaderboard Generator")
print("="*70)

# Load player ratings
with open('output/combined_all_seasons_ratings_with_bonus.json', 'r') as f:
    players = json.load(f)

# Sort by combined rating
players_sorted = sorted(players, key=lambda x: x['combined_rating'], reverse=True)

print(f"Loaded {len(players_sorted)} players")

# Assign ranks
for i, player in enumerate(players_sorted, 1):
    player['rank'] = i

# Determine tier based on rating thresholds (bell curve distribution)
def assign_player_tier(rating):
    if rating >= 160:
        return 'S+', 'Elite Pro'
    elif rating >= 140:
        return 'S', 'Elite'
    elif rating >= 120:
        return 'A+', 'Advanced High'
    elif rating >= 100:
        return 'A', 'High Skill'
    elif rating >= 85:
        return 'B+', 'Above Average+'
    elif rating >= 70:
        return 'B', 'Above Average'
    elif rating >= 60:
        return 'C+', 'Average+'
    elif rating >= 50:
        return 'C', 'Average'
    elif rating >= 40:
        return 'C-', 'Average-'
    elif rating >= 30:
        return 'D+', 'Below Average+'
    elif rating >= 20:
        return 'D', 'Below Average'
    else:
        return 'D-', 'Developing'

total_players = len(players_sorted)
for player in players_sorted:
    tier, tier_desc = assign_player_tier(player['combined_rating'])
    player['tier'] = tier
    player['tier_desc'] = tier_desc

# Generate timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# === CSV OUTPUT (Clean & Simple) ===
csv_file = f'output/player_leaderboard_{timestamp}.csv'
with open(csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Rank', 'Player Name', 'Rating', 'Tier', 'Seasons Played', 'Top Lobby Bonus'])

    for player in players_sorted:
        writer.writerow([
            player['rank'],
            player['player_name'],
            f"{player['combined_rating']:.2f}",
            player['tier'],
            ', '.join(player['seasons_played']),
            'Yes' if player.get('top_lobby_bonus', False) else 'No'
        ])

print(f"✓ CSV saved to: {csv_file}")

# === JSON OUTPUT (Detailed) ===
json_file = f'output/player_leaderboard_{timestamp}.json'
with open(json_file, 'w') as f:
    json.dump(players_sorted, f, indent=2)

print(f"✓ JSON saved to: {json_file}")

# === TEXT REPORT (Pretty Print) ===
txt_file = f'output/player_leaderboard_{timestamp}.txt'
with open(txt_file, 'w') as f:
    f.write("="*80 + "\n")
    f.write("VESA LEAGUE - INDIVIDUAL PLAYER RANKINGS\n")
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("="*80 + "\n\n")

    f.write("Multi-Season Weighted Ratings (S4-S12)\n")
    f.write("Recency Bias: S12(28%), S11(24%), S8(18%), S6(14%), S5(10%), S4(6%)\n")
    f.write("Top Lobby Bonus: 15% for elite division players\n\n")

    f.write("="*80 + "\n")
    f.write("TOP 100 PLAYERS\n")
    f.write("="*80 + "\n")
    f.write(f"{'Rank':<6} {'Player':<25} {'Rating':<10} {'Tier':<6} {'Seasons':<15} {'Bonus'}\n")
    f.write("-"*80 + "\n")

    for player in players_sorted[:100]:
        bonus = '⭐' if player.get('top_lobby_bonus', False) else ''
        seasons = ', '.join(player['seasons_played'])
        f.write(f"{player['rank']:<6} {player['player_name'][:24]:<25} {player['combined_rating']:<10.2f} "
                f"{player['tier']:<6} {seasons[:14]:<15} {bonus}\n")

    # Tier distribution
    f.write("\n" + "="*80 + "\n")
    f.write("TIER DISTRIBUTION\n")
    f.write("="*80 + "\n")

    tier_counts = {}
    for player in players_sorted:
        tier = player['tier']
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    tier_order = ['S+', 'S', 'A+', 'A', 'B+', 'B', 'C+', 'C', 'C-', 'D+', 'D', 'D-']
    for tier in tier_order:
        count = tier_counts.get(tier, 0)
        if count > 0:
            pct = (count / total_players) * 100
            bar = '█' * int(pct / 2)
            f.write(f"Tier {tier:3} ({count:>4} players, {pct:>5.1f}%): {bar}\n")

    # Top 10 highlight
    f.write("\n" + "="*80 + "\n")
    f.write("TOP 10 PLAYERS\n")
    f.write("="*80 + "\n\n")

    for i, player in enumerate(players_sorted[:10], 1):
        bonus_text = ' (TOP LOBBY BONUS)' if player.get('top_lobby_bonus', False) else ''
        f.write(f"{i}. {player['player_name']} - {player['combined_rating']:.2f}{bonus_text}\n")
        f.write(f"   Tier {player['tier']} ({player['tier_desc']}) | Seasons: {', '.join(player['seasons_played'])}\n\n")

print(f"✓ Text report saved to: {txt_file}")

# === SUMMARY STATISTICS ===
print("\n" + "="*70)
print("LEADERBOARD SUMMARY")
print("-"*70)
print(f"Total Players: {total_players}")
print(f"\nTop 10 Players:")
for i, player in enumerate(players_sorted[:10], 1):
    bonus = ' ⭐' if player.get('top_lobby_bonus', False) else ''
    print(f"  {i}. {player['player_name']}: {player['combined_rating']:.2f}{bonus}")

print(f"\nTier Distribution:")
tier_order = ['S+', 'S', 'A+', 'A', 'B+', 'B', 'C+', 'C', 'C-', 'D+', 'D', 'D-']
for tier in tier_order:
    count = tier_counts.get(tier, 0)
    if count > 0:
        pct = (count / total_players) * 100
        print(f"  Tier {tier:3}: {count:4} players ({pct:5.1f}%)")

print(f"\n✓ All leaderboard files generated successfully!")
