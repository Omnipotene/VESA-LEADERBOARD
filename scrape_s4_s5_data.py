#!/usr/bin/env python3
"""
Scrape VESA Season 4 and Season 5 tournament data
Uses Player Stats pages which aggregate all weekly data
"""

import json
import time
import sys
sys.path.append('.')

from working_scraper import scrape_overstat_players

print("VESA Seasons 4 & 5 - Data Scraper (Player Stats Pages)")
print("="*70)

# Focus on the aggregate Player Stats pages which have all the data
# These are more reliable than individual week pages
tournaments = {
    'S4': {
        'Contenders': 'https://overstat.gg/_hxy1S',
        'Challengers': 'https://overstat.gg/_AVlmX',
        'Pinnacle': 'https://overstat.gg/_QNkod'
    },
    'S5': {
        'Contenders': 'https://overstat.gg/_6UQzh',
        'Challengers': 'https://overstat.gg/_Vn8PF',
        'Ascendant': 'https://overstat.gg/_KunvA',
        'Pinnacle': 'https://overstat.gg/_w4SHG'
    }
}

all_data = {}
errors = []

print("\nScraping Player Stats pages (aggregate data for full season)...")
print("-"*70)

for season, leagues in tournaments.items():
    print(f"\n{season}:")
    season_players = []

    for league, url in leagues.items():
        print(f"  {league}: Scraping {url}...", end=' ', flush=True)

        try:
            data = scrape_overstat_players(url)

            if data:
                # Tag each player with season and league
                for player in data:
                    player['season'] = season
                    player['league'] = league

                season_players.extend(data)
                print(f"✓ {len(data)} players")
            else:
                print("✗ No data")
                errors.append({'season': season, 'league': league, 'url': url, 'error': 'No data returned'})

        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
            errors.append({'season': season, 'league': league, 'url': url, 'error': str(e)})

        # Rate limiting
        time.sleep(3)

    all_data[season] = season_players

print(f"\n{'='*70}")
print(f"Scraping complete!")
print(f"S4 players: {len(all_data.get('S4', []))}")
print(f"S5 players: {len(all_data.get('S5', []))}")
print(f"Errors: {len(errors)}")

# Process and save each season
for season in ['S4', 'S5']:
    if season not in all_data or not all_data[season]:
        print(f"\n⚠️  No data for {season}")
        continue

    players = all_data[season]

    # Aggregate by player (handle duplicates across leagues)
    from collections import defaultdict

    player_stats = defaultdict(lambda: {
        'total_score': 0,
        'total_kills': 0,
        'games_played': 0,
        'leagues': set(),
        'all_names_used': set()
    })

    for entry in players:
        player_name = entry.get('player_name', '').strip()
        if not player_name:
            continue

        canonical_name = player_name.lower()

        player_stats[canonical_name]['total_score'] += entry.get('score', 0)
        player_stats[canonical_name]['total_kills'] += entry.get('kills', 0)
        player_stats[canonical_name]['games_played'] += entry.get('games', 0)
        player_stats[canonical_name]['leagues'].add(entry.get('league', 'Unknown'))
        player_stats[canonical_name]['all_names_used'].add(player_name)

    # Convert to list
    season_players_agg = []
    for canonical_name, stats in player_stats.items():
        primary_name = max(stats['all_names_used'], key=len) if stats['all_names_used'] else canonical_name

        season_players_agg.append({
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
    season_players_sorted = sorted(season_players_agg, key=lambda x: x['final_score'], reverse=True)

    # Add ranks
    for i, player in enumerate(season_players_sorted, 1):
        player['rank'] = i

    # Save
    output_file = f'output/{season.lower()}_players_ranked.json'
    with open(output_file, 'w') as f:
        json.dump(season_players_sorted, f, indent=2)

    print(f"\n{season} Results:")
    print("-"*70)
    print(f"Unique players: {len(season_players_sorted)}")
    print(f"Saved to: {output_file}")

    # Show top 10
    print(f"\nTOP 10 {season} PLAYERS:")
    print(f"{'Rank':<5} {'Player':<30} {'Score':<10} {'Kills':<8} {'Games':<8}")
    print("-"*70)

    for p in season_players_sorted[:10]:
        print(f"{p['rank']:<5} {p['player_name'][:29]:<30} {p['final_score']:<10.2f} {p['total_kills']:<8} {p['games_played']:<8}")

# Save errors
if errors:
    with open('output/s4_s5_scrape_errors.json', 'w') as f:
        json.dump(errors, f, indent=2)
    print(f"\n⚠️  Errors saved to: output/s4_s5_scrape_errors.json")

print(f"\n{'='*70}")
print("✅ COMPLETE")
print(f"\nNext step: Combine with S11 + S12 data")
print("  python3 combine_all_seasons.py")
