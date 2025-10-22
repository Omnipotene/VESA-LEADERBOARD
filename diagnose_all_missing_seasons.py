#!/usr/bin/env python3
"""
Comprehensive diagnostic to identify ALL players who might be missing season data
"""

import json
from collections import defaultdict

# Load combined ratings
with open('output/combined_all_seasons_ratings_with_bonus.json', 'r') as f:
    combined = json.load(f)

# Load alias mappings
with open('data/player_aliases.json', 'r') as f:
    aliases_data = json.load(f)

# Build discord -> aliases map
discord_to_player = {}
for player in aliases_data:
    discord = player['discord_name'].lower().strip()
    discord_to_player[discord] = {
        'discord_name': player['discord_name'],
        'aliases': [a.lower().strip() for a in player['aliases']],
        'player_id': player['player_id']
    }

# Load each season's raw data
seasons_data = {}

print("Loading season data...")
for season in ['s4', 's5', 's6', 's8', 's11', 's12']:
    try:
        if season == 's12':
            with open(f'output/{season}_players_ranked_v2.json', 'r') as f:
                seasons_data[season] = json.load(f)
        else:
            with open(f'output/{season}_players_ranked.json', 'r') as f:
                seasons_data[season] = json.load(f)
        print(f"  Loaded {season}: {len(seasons_data[season])} players")
    except FileNotFoundError:
        seasons_data[season] = []
        print(f"  ⚠️  {season} not found")

print("\n" + "="*80)
print("COMPREHENSIVE MISSING SEASON ANALYSIS")
print("="*80)

# Statistics
missing_alias_data = []
players_with_missing_seasons = []
no_issues = []

for player in combined:
    discord_id = player['canonical_id']
    player_name = player['player_name']
    current_seasons = set(player['seasons_played'].split('+'))

    # Get alias info
    alias_info = discord_to_player.get(discord_id, None)

    if not alias_info:
        missing_alias_data.append({
            'name': player_name,
            'discord_id': discord_id,
            'current_seasons': player['seasons_played'],
            'rank': player.get('rank', 999)
        })
        continue

    # Check each season for potential matches
    missing_seasons = []
    for season in ['s4', 's5', 's6', 's8', 's11', 's12']:
        season_upper = season.upper()
        if season_upper not in current_seasons:
            # Search this season for any of the player's aliases
            found_in_season = []
            for season_player in seasons_data[season]:
                pname = season_player.get('player_name', '').lower().strip()
                if pname in alias_info['aliases']:
                    found_in_season.append({
                        'name': season_player.get('player_name'),
                        'rank': season_player.get('rank'),
                        'score': season_player.get('final_score')
                    })

            if found_in_season:
                missing_seasons.append({
                    'season': season_upper,
                    'matches': found_in_season
                })

    if missing_seasons:
        players_with_missing_seasons.append({
            'name': player_name,
            'discord_id': discord_id,
            'current_seasons': player['seasons_played'],
            'missing_seasons': missing_seasons,
            'rank': player.get('rank', 999),
            'rating': player.get('combined_rating', 0)
        })
    else:
        no_issues.append(player_name)

# Report: Players missing from alias file
print(f"\n1. PLAYERS NOT IN ALIAS FILE: {len(missing_alias_data)}")
print("-"*80)
if missing_alias_data:
    print("These players exist in season data but have no alias mapping:")
    print()
    for p in sorted(missing_alias_data, key=lambda x: x['rank'])[:50]:
        print(f"  Rank {p['rank']:<4} {p['name']:<30} (ID: {p['discord_id']})")
        print(f"           Current: {p['current_seasons']}")
    if len(missing_alias_data) > 50:
        print(f"\n  ... and {len(missing_alias_data) - 50} more")
else:
    print("  ✓ All players have alias data")

# Report: Players with missing season data
print(f"\n\n2. PLAYERS WITH POTENTIAL MISSING SEASONS: {len(players_with_missing_seasons)}")
print("-"*80)
if players_with_missing_seasons:
    print("These players have aliases found in seasons they're not credited for:")
    print()

    # Sort by rank (most important players first)
    sorted_missing = sorted(players_with_missing_seasons, key=lambda x: x['rank'])

    for p in sorted_missing[:100]:  # Show top 100 with issues
        print(f"\nRank {p['rank']:<4} {p['name']:<30} Rating: {p['rating']:.2f}")
        print(f"       Current: {p['current_seasons']}")
        print(f"       Missing:")
        for ms in p['missing_seasons']:
            print(f"         {ms['season']}: {len(ms['matches'])} match(es)")
            for match in ms['matches'][:2]:  # Show first 2 matches per season
                print(f"            └─ {match['name']} (Rank {match['rank']}, Score {match['score']:.2f})")

    if len(sorted_missing) > 100:
        print(f"\n  ... and {len(sorted_missing) - 100} more players with missing seasons")
else:
    print("  ✓ No missing season data detected")

# Summary statistics
print(f"\n\n{'='*80}")
print("SUMMARY STATISTICS")
print("="*80)
print(f"Total players analyzed: {len(combined)}")
print(f"  Players with complete data: {len(no_issues)} ({len(no_issues)/len(combined)*100:.1f}%)")
print(f"  Players missing from alias file: {len(missing_alias_data)} ({len(missing_alias_data)/len(combined)*100:.1f}%)")
print(f"  Players with missing seasons: {len(players_with_missing_seasons)} ({len(players_with_missing_seasons)/len(combined)*100:.1f}%)")

# Count total missing season instances
total_missing_instances = sum(len(p['missing_seasons']) for p in players_with_missing_seasons)
print(f"\nTotal missing season instances: {total_missing_instances}")

# Export detailed report
report_file = 'output/missing_seasons_report.json'
with open(report_file, 'w') as f:
    json.dump({
        'missing_alias_data': missing_alias_data,
        'players_with_missing_seasons': players_with_missing_seasons,
        'summary': {
            'total_players': len(combined),
            'complete_data': len(no_issues),
            'missing_alias': len(missing_alias_data),
            'missing_seasons': len(players_with_missing_seasons),
            'total_missing_instances': total_missing_instances
        }
    }, f, indent=2)

print(f"\n✓ Detailed report saved to: {report_file}")
print("="*80)
