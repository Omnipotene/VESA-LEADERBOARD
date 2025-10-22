#!/usr/bin/env python3
"""
Scrape VESA Season 4 tournament data from Overstat
Integrates with existing S11 and S12 data
"""

import json
import time
import sys
sys.path.append('.')

# Import the working scraper function
from working_scraper import scrape_overstat_players

print("VESA Season 4 - Data Scraper")
print("="*70)

# Season 4 tournament URLs
tournaments = {
    'Contenders': {
        'Week 1': 'https://overstat.gg/_x3nGz',
        'Week 2': 'https://overstat.gg/_3fC4y',
        'Week 3': 'https://overstat.gg/_nhI8w',
        'Week 4': 'https://overstat.gg/_8lTus',
        'Week 5': 'https://overstat.gg/_RWoVm',
        'MP Finals': 'https://overstat.gg/_RFuok',
        'Player Stats': 'https://overstat.gg/_hxy1S'
    },
    'Challengers': {
        'Week 1': 'https://overstat.gg/_lgtmD',
        'Week 2': 'https://overstat.gg/_8SoH1',
        'Week 3': 'https://overstat.gg/_xtKqJ',
        'Week 4': 'https://overstat.gg/_dk1Gk',
        'Week 5': 'https://overstat.gg/_pDIZR',
        'MP Finals': 'https://overstat.gg/_daATB',
        'Player Stats': 'https://overstat.gg/_AVlmX'
    },
    'Pinnacle': {
        'Week 1': 'https://overstat.gg/_SewNr',
        'Week 2': 'https://overstat.gg/_io5oW',
        'Week 3': 'https://overstat.gg/_1KNS4',
        'Week 4': 'https://overstat.gg/_PfyCM',
        'Week 5': 'https://overstat.gg/_BN17W',
        # 'MP Finals': '',  # Missing
        'Player Stats': 'https://overstat.gg/_QNkod'
    }
}

all_players = []
errors = []

print("\nScraping Season 4 tournaments...")
print("-"*70)

for league, weeks in tournaments.items():
    print(f"\n{league} League:")

    for week_name, url in weeks.items():
        if not url:
            print(f"  {week_name}: SKIPPED (no URL)")
            continue

        print(f"  {week_name}: Scraping {url}...", end=' ', flush=True)

        try:
            # Use the working scraper function
            data = scrape_overstat_players(url)

            if data:
                # Tag each player with league and week info
                for player in data:
                    player['league'] = league
                    player['week'] = week_name
                    player['season'] = 'S4'

                all_players.extend(data)
                print(f"✓ {len(data)} players")
            else:
                print("✗ No data")
                errors.append({'league': league, 'week': week_name, 'url': url, 'error': 'No data returned'})

        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
            errors.append({'league': league, 'week': week_name, 'url': url, 'error': str(e)})

        # Rate limiting
        time.sleep(2)

print(f"\n{'='*70}")
print(f"Scraping complete!")
print(f"Total players scraped: {len(all_players)}")
print(f"Errors: {len(errors)}")

# Save raw data
raw_output = 'output/s4_raw_data.json'
with open(raw_output, 'w') as f:
    json.dump(all_players, f, indent=2)

print(f"\n✅ Raw data saved to: {raw_output}")

# Save errors if any
if errors:
    error_output = 'output/s4_scrape_errors.json'
    with open(error_output, 'w') as f:
        json.dump(errors, f, indent=2)
    print(f"⚠️  Errors saved to: {error_output}")

# Aggregate player stats
print(f"\n{'='*70}")
print("Aggregating player statistics...")
print("-"*70)

from collections import defaultdict

player_stats = defaultdict(lambda: {
    'total_score': 0,
    'total_kills': 0,
    'games_played': 0,
    'leagues': set(),
    'weeks': [],
    'all_names_used': set()
})

for entry in all_players:
    player_name = entry.get('player_name', '').strip()
    if not player_name:
        continue

    # Use lowercase for canonical matching
    canonical_name = player_name.lower()

    player_stats[canonical_name]['total_score'] += entry.get('score', 0)
    player_stats[canonical_name]['total_kills'] += entry.get('kills', 0)
    player_stats[canonical_name]['games_played'] += entry.get('games', 0)
    player_stats[canonical_name]['leagues'].add(entry.get('league', 'Unknown'))
    player_stats[canonical_name]['weeks'].append(entry.get('week', 'Unknown'))
    player_stats[canonical_name]['all_names_used'].add(player_name)

# Convert to list and calculate final scores
s4_players = []
for canonical_name, stats in player_stats.items():
    # Use the most common name variant
    primary_name = max(stats['all_names_used'], key=len) if stats['all_names_used'] else canonical_name

    s4_players.append({
        'player_name': primary_name,
        'canonical_id': canonical_name,
        'total_score': stats['total_score'],
        'total_kills': stats['total_kills'],
        'games_played': stats['games_played'],
        'final_score': stats['total_score'],  # Can add weighting here later
        'leagues_played': list(stats['leagues']),
        'weeks_played': len(set(stats['weeks'])),
        'all_names_used': list(stats['all_names_used'])
    })

# Sort by final score
s4_players_sorted = sorted(s4_players, key=lambda x: x['final_score'], reverse=True)

# Add ranks
for i, player in enumerate(s4_players_sorted, 1):
    player['rank'] = i

# Save aggregated data
aggregated_output = 'output/s4_players_ranked.json'
with open(aggregated_output, 'w') as f:
    json.dump(s4_players_sorted, f, indent=2)

print(f"Unique players: {len(s4_players_sorted)}")
print(f"\nTOP 20 SEASON 4 PLAYERS:")
print("-"*70)
print(f"{'Rank':<5} {'Player':<30} {'Score':<10} {'Kills':<8} {'Games':<8} {'Leagues'}")
print("-"*70)

for i, p in enumerate(s4_players_sorted[:20], 1):
    leagues_str = ', '.join(p['leagues_played'])
    print(f"{i:<5} {p['player_name'][:29]:<30} {p['final_score']:<10.2f} {p['total_kills']:<8} {p['games_played']:<8} {leagues_str}")

print(f"\n{'='*70}")
print(f"✅ Season 4 data aggregated and saved to: {aggregated_output}")
print(f"\nNext step: Integrate with S11+S12 data")
print("  python3 combine_all_seasons.py")
