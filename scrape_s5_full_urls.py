#!/usr/bin/env python3
"""
Scrape VESA Season 5 player data using full Overstat URLs
"""

import json
import time
import sys
sys.path.append('.')

from working_scraper import scrape_overstat_players

print("VESA Season 5 - Data Scraper (Full URLs)")
print("="*70)

# Season 5 full URLs - player standings pages
tournaments = {
    'S5': {
        'Contenders': 'https://overstat.gg/tournament/virtualesports/4077.VESA_S5_Contenders_All_Weeks/standings/overall/player-standings',
        'Challengers': 'https://overstat.gg/tournament/virtualesports/4623.VESA_S5_Challengers_All_Weeks/standings/overall/player-standings',
        'Ascendant': 'https://overstat.gg/tournament/virtualesports/4624.VESA_S5_Ascendant_All_Weeks/standings/overall/player-standings',
        'Pinnacle': 'https://overstat.gg/tournament/virtualesports/4076.VESA_Season_5_Pinnacle_League_/standings/overall/player-standings'
    }
}

all_data = {}
errors = []

print("\nScraping Season 5 Player Stats pages...")
print("-"*70)

season_players = []

for league, url in tournaments['S5'].items():
    print(f"\n{league}: Scraping {url}...")
    print("  ", end='', flush=True)

    try:
        data = scrape_overstat_players(url)

        if data:
            # Tag each player with season and league
            for player in data:
                player['season'] = 'S5'
                player['league'] = league

            season_players.extend(data)
            print(f"✓ {len(data)} players")
        else:
            print("✗ No data")
            errors.append({'season': 'S5', 'league': league, 'url': url, 'error': 'No data returned'})

    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        errors.append({'season': 'S5', 'league': league, 'url': url, 'error': str(e)})

    # Rate limiting
    time.sleep(3)

all_data['S5'] = season_players

print(f"\n{'='*70}")
print(f"Scraping complete!")
print(f"S5 players: {len(all_data.get('S5', []))}")
print(f"Errors: {len(errors)}")

# Save raw data
if season_players:
    raw_output = 'output/s5_raw_data_full_urls.json'
    with open(raw_output, 'w') as f:
        json.dump(season_players, f, indent=2)
    print(f"\n✅ Raw data saved to: {raw_output}")

# Save errors if any
if errors:
    error_output = 'output/s5_scrape_errors_full_urls.json'
    with open(error_output, 'w') as f:
        json.dump(errors, f, indent=2)
    print(f"⚠️  Errors saved to: {error_output}")

# Aggregate player stats
if not season_players:
    print(f"\n⚠️  No data collected for S5")
    sys.exit(0)

print(f"\n{'='*70}")
print("Aggregating player statistics...")
print("-"*70)

from collections import defaultdict

player_stats = defaultdict(lambda: {
    'total_score': 0,
    'total_kills': 0,
    'games_played': 0,
    'leagues': set(),
    'all_names_used': set()
})

for entry in season_players:
    player_name = entry.get('player_name', '').strip()
    if not player_name:
        continue

    # Use lowercase for canonical matching
    canonical_name = player_name.lower()

    player_stats[canonical_name]['total_score'] += entry.get('score', 0)
    player_stats[canonical_name]['total_kills'] += entry.get('kills', 0)
    player_stats[canonical_name]['games_played'] += entry.get('games', 0)
    player_stats[canonical_name]['leagues'].add(entry.get('league', 'Unknown'))
    player_stats[canonical_name]['all_names_used'].add(player_name)

# Convert to list
s5_players = []
for canonical_name, stats in player_stats.items():
    # Use the most common name variant
    primary_name = max(stats['all_names_used'], key=len) if stats['all_names_used'] else canonical_name

    s5_players.append({
        'player_name': primary_name,
        'canonical_id': canonical_name,
        'total_score': stats['total_score'],
        'total_kills': stats['total_kills'],
        'games_played': stats['games_played'],
        'final_score': stats['total_score'],
        'leagues_played': list(stats['leagues']),
        'all_names_used': list(stats['all_names_used'])
    })

# Sort by score
s5_players_sorted = sorted(s5_players, key=lambda x: x['final_score'], reverse=True)

# Add ranks
for i, player in enumerate(s5_players_sorted, 1):
    player['rank'] = i

# Save
output_file = 'output/s5_players_ranked.json'
with open(output_file, 'w') as f:
    json.dump(s5_players_sorted, f, indent=2)

print(f"Unique players: {len(s5_players_sorted)}")
print(f"Saved to: {output_file}")

# Show top 20
print(f"\nTOP 20 SEASON 5 PLAYERS:")
print(f"{'Rank':<5} {'Player':<30} {'Score':<10} {'Kills':<8} {'Games':<8} {'Leagues'}")
print("-"*70)

for p in s5_players_sorted[:20]:
    leagues_str = ', '.join(p['leagues_played'])
    print(f"{p['rank']:<5} {p['player_name'][:29]:<30} {p['final_score']:<10.2f} {p['total_kills']:<8} {p['games_played']:<8} {leagues_str}")

print(f"\n{'='*70}")
print(f"✅ Season 5 data complete!")
print(f"\nNext step: Re-run multi-season combination with S4+S5+S11+S12")
print("  python3 combine_all_seasons.py")
