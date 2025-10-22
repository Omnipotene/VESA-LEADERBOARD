#!/usr/bin/env python3
"""
Calculate advanced performance metrics:
- Consistency (placement variance)
- Hot streaks (recent form)
- Top finish rates
"""

import json
import math
from collections import defaultdict

print("VESA League - Advanced Metrics Calculator")
print("="*70)

# Load team match history
print("\nLoading team match history...")
with open('output/team_match_history.json', 'r') as f:
    team_history = json.load(f)

print(f"✓ Loaded history for {len(team_history)} teams")

# Calculate metrics for each team
team_metrics = []

for team_name, games in team_history.items():
    if len(games) < 5:  # Need minimum games for meaningful stats
        continue

    # Sort by timestamp
    games_sorted = sorted(games, key=lambda x: x['timestamp'])

    placements = [g['placement'] for g in games_sorted]

    # CONSISTENCY METRICS
    avg_placement = sum(placements) / len(placements)
    variance = sum((p - avg_placement) ** 2 for p in placements) / len(placements)
    std_dev = math.sqrt(variance)

    # Consistency score (inverse of std dev, normalized)
    # Lower std dev = more consistent = higher score
    consistency_score = max(0, 100 - (std_dev * 5))  # Scale to 0-100

    # TOP FINISH RATES
    top3_count = sum(1 for p in placements if p <= 3)
    top5_count = sum(1 for p in placements if p <= 5)
    top10_count = sum(1 for p in placements if p <= 10)
    bottom5_count = sum(1 for p in placements if p >= 16)

    top3_rate = (top3_count / len(placements)) * 100
    top5_rate = (top5_count / len(placements)) * 100
    top10_rate = (top10_count / len(placements)) * 100
    bottom5_rate = (bottom5_count / len(placements)) * 100

    # RECENT FORM / HOT STREAK
    # Calculate average placement for last N games
    last_10_games = games_sorted[-10:] if len(games_sorted) >= 10 else games_sorted
    last_20_games = games_sorted[-20:] if len(games_sorted) >= 20 else games_sorted

    last_10_avg = sum(g['placement'] for g in last_10_games) / len(last_10_games)
    last_20_avg = sum(g['placement'] for g in last_20_games) / len(last_20_games)

    # Hot streak score: compare recent form to overall average
    # Positive = improving, Negative = declining
    form_10 = avg_placement - last_10_avg  # Positive if recent games better than average
    form_20 = avg_placement - last_20_avg

    # Form score (0-100, where 100 = much better recently)
    form_score = 50 + (form_10 * 5)  # Each placement better = +5 points
    form_score = max(0, min(100, form_score))  # Clamp to 0-100

    # BOOM/BUST RATIO
    # High ceiling (best finishes) vs low floor (worst finishes)
    best_placement = min(placements)
    worst_placement = max(placements)
    placement_range = worst_placement - best_placement

    # Teams with small range are more consistent
    # Teams with large range are boom/bust

    team_metrics.append({
        'team_name': team_name,
        'games_played': len(games),
        'avg_placement': avg_placement,
        'std_dev': std_dev,
        'consistency_score': consistency_score,
        'top3_rate': top3_rate,
        'top5_rate': top5_rate,
        'top10_rate': top10_rate,
        'bottom5_rate': bottom5_rate,
        'last_10_avg': last_10_avg,
        'last_20_avg': last_20_avg,
        'form_score': form_score,
        'form_trend_10': form_10,
        'form_trend_20': form_20,
        'best_placement': best_placement,
        'worst_placement': worst_placement,
        'placement_range': placement_range
    })

# Save metrics
output_file = 'output/advanced_metrics.json'
with open(output_file, 'w') as f:
    json.dump(team_metrics, f, indent=2)

# Statistics
print("\n" + "="*70)
print("ADVANCED METRICS SUMMARY:")
print("-"*70)
print(f"Teams analyzed: {len(team_metrics)}")
print(f"Minimum games required: 5")

# Show most consistent teams
print(f"\n{'='*70}")
print("TOP 10 MOST CONSISTENT TEAMS:")
print("-"*70)
consistent = sorted(team_metrics, key=lambda x: x['consistency_score'], reverse=True)[:10]
print(f"{'Rank':<5} {'Team':<30} {'Score':<8} {'Std Dev':<9} {'Avg Place'}")
print("-"*70)
for i, team in enumerate(consistent, 1):
    print(f"{i:<5} {team['team_name'][:29]:<30} {team['consistency_score']:<8.1f} {team['std_dev']:<9.2f} {team['avg_placement']:.1f}")

# Show teams on hottest streaks
print(f"\n{'='*70}")
print("TOP 10 HOTTEST TEAMS (Recent Form):")
print("-"*70)
hot_teams = sorted(team_metrics, key=lambda x: x['form_score'], reverse=True)[:10]
print(f"{'Rank':<5} {'Team':<30} {'Form':<8} {'L10 Avg':<9} {'Overall Avg'}")
print("-"*70)
for i, team in enumerate(hot_teams, 1):
    print(f"{i:<5} {team['team_name'][:29]:<30} {team['form_score']:<8.1f} {team['last_10_avg']:<9.1f} {team['avg_placement']:.1f}")

# Show highest top-3 finish rates
print(f"\n{'='*70}")
print("TOP 10 TEAMS BY TOP-3 FINISH RATE:")
print("-"*70)
top_finishers = sorted(team_metrics, key=lambda x: x['top3_rate'], reverse=True)[:10]
print(f"{'Rank':<5} {'Team':<30} {'Top3%':<8} {'Top5%':<8} {'Games'}")
print("-"*70)
for i, team in enumerate(top_finishers, 1):
    print(f"{i:<5} {team['team_name'][:29]:<30} {team['top3_rate']:<8.1f} {team['top5_rate']:<8.1f} {team['games_played']}")

print(f"\n✓ Advanced metrics saved to: {output_file}")
print(f"\nNext step: Generate combined power rankings")
print("  python3 generate_power_rankings.py")
