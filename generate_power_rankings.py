#!/usr/bin/env python3
"""
Generate unified Power Rankings combining:
- Elo ratings (40%)
- Aggregate season performance (25%)
- Consistency (15%)
- Recent form (15%)
- Top finish rate (5%)
"""

import json

print("VESA League - Power Rankings Generator")
print("="*70)

# Load all the data sources
print("\nLoading data sources...")

# 1. Elo ratings
with open('output/elo_ratings.json', 'r') as f:
    elo_data = {team['team_name']: team for team in json.load(f)}

# 2. Advanced metrics (consistency, form)
with open('output/advanced_metrics.json', 'r') as f:
    metrics_data = {team['team_name']: team for team in json.load(f)}

# 3. Aggregate season ratings (our original system)
with open('output/combined_all_seasons_ratings_with_bonus.json', 'r') as f:
    aggregate_data = {team['player_name']: team for team in json.load(f)}

print(f"✓ Loaded Elo data for {len(elo_data)} teams")
print(f"✓ Loaded metrics for {len(metrics_data)} teams")
print(f"✓ Loaded aggregate ratings for {len(aggregate_data)} teams")

# Weighting scheme
WEIGHTS = {
    'elo': 0.40,
    'aggregate': 0.25,
    'consistency': 0.15,
    'form': 0.15,
    'top_finish': 0.05
}

print(f"\nWeighting scheme:")
for component, weight in WEIGHTS.items():
    print(f"  {component}: {weight*100:.0f}%")

# Normalize all metrics to 0-100 scale
def normalize(value, min_val, max_val):
    """Normalize value to 0-100 range"""
    if max_val == min_val:
        return 50
    return ((value - min_val) / (max_val - min_val)) * 100

# Find min/max for each metric
elo_values = [team['current_elo'] for team in elo_data.values()]
elo_min, elo_max = min(elo_values), max(elo_values)

aggregate_values = [team['combined_rating'] for team in aggregate_data.values()]
agg_min, agg_max = min(aggregate_values), max(aggregate_values)

consistency_values = [team['consistency_score'] for team in metrics_data.values()]
cons_min, cons_max = 0, 100  # Already 0-100

form_values = [team['form_score'] for team in metrics_data.values()]
form_min, form_max = 0, 100  # Already 0-100

top3_values = [team['top3_rate'] for team in metrics_data.values()]
top3_min, top3_max = min(top3_values), max(top3_values)

print(f"\nValue ranges:")
print(f"  Elo: {elo_min:.0f} - {elo_max:.0f}")
print(f"  Aggregate: {agg_min:.1f} - {agg_max:.1f}")
print(f"  Consistency: {cons_min} - {cons_max}")
print(f"  Form: {form_min} - {form_max}")
print(f"  Top3 Rate: {top3_min:.1f}% - {top3_max:.1f}%")

# Calculate power rankings
power_rankings = []

# Get all unique team names across all sources
all_teams = set(elo_data.keys()) | set(metrics_data.keys()) | set(aggregate_data.keys())

for team_name in all_teams:
    # Get data from each source (with defaults if missing)
    elo = elo_data.get(team_name, {}).get('current_elo', 1500)
    aggregate = aggregate_data.get(team_name, {}).get('combined_rating', 0)
    metrics = metrics_data.get(team_name, {})

    consistency = metrics.get('consistency_score', 50)
    form = metrics.get('form_score', 50)
    top3_rate = metrics.get('top3_rate', 0)
    games_played = metrics.get('games_played', elo_data.get(team_name, {}).get('games_played', 0))

    # Skip teams with very few games
    if games_played < 5:
        continue

    # Normalize each metric
    elo_normalized = normalize(elo, elo_min, elo_max)
    aggregate_normalized = normalize(aggregate, agg_min, agg_max)
    consistency_normalized = consistency  # Already 0-100
    form_normalized = form  # Already 0-100
    top3_normalized = normalize(top3_rate, top3_min, top3_max)

    # Calculate weighted power score
    power_score = (
        elo_normalized * WEIGHTS['elo'] +
        aggregate_normalized * WEIGHTS['aggregate'] +
        consistency_normalized * WEIGHTS['consistency'] +
        form_normalized * WEIGHTS['form'] +
        top3_normalized * WEIGHTS['top_finish']
    )

    power_rankings.append({
        'team_name': team_name,
        'power_score': power_score,
        'elo': elo,
        'elo_normalized': elo_normalized,
        'aggregate_rating': aggregate,
        'aggregate_normalized': aggregate_normalized,
        'consistency_score': consistency,
        'form_score': form,
        'top3_rate': top3_rate,
        'top3_normalized': top3_normalized,
        'games_played': games_played
    })

# Sort by power score
power_rankings_sorted = sorted(power_rankings, key=lambda x: x['power_score'], reverse=True)

# Add ranks
for i, team in enumerate(power_rankings_sorted, 1):
    team['power_rank'] = i

# Save power rankings
output_file = 'output/power_rankings.json'
with open(output_file, 'w') as f:
    json.dump(power_rankings_sorted, f, indent=2)

# Statistics
print("\n" + "="*70)
print("POWER RANKINGS COMPLETE:")
print("-"*70)
print(f"Teams ranked: {len(power_rankings_sorted)}")

print(f"\n{'='*70}")
print("TOP 30 POWER RANKINGS:")
print("-"*70)
print(f"{'Rank':<5} {'Team':<30} {'Power':<8} {'Elo':<6} {'Agg':<6} {'Cons':<6} {'Form':<6}")
print("-"*70)

for team in power_rankings_sorted[:30]:
    print(f"{team['power_rank']:<5} {team['team_name'][:29]:<30} {team['power_score']:<8.1f} {team['elo']:<6.0f} {team['aggregate_rating']:<6.1f} {team['consistency_score']:<6.1f} {team['form_score']:<6.1f}")

print(f"\n✓ Power rankings saved to: {output_file}")
print(f"\nNext step: Update S13 seeding with power rankings")
print("  python3 update_team_seeding.py")
