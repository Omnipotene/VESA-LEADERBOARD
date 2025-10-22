#!/usr/bin/env python3
"""
Diagnostic tool to identify players who might be missing season data
"""

import json

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
        'aliases': player['aliases'],
        'player_id': player['player_id']
    }

# Load each season's raw data
seasons_data = {}

for season in ['s4', 's5', 's6', 's8', 's11', 's12']:
    try:
        if season == 's12':
            with open(f'output/{season}_players_ranked_v2.json', 'r') as f:
                seasons_data[season] = json.load(f)
        else:
            with open(f'output/{season}_players_ranked.json', 'r') as f:
                seasons_data[season] = json.load(f)
    except FileNotFoundError:
        seasons_data[season] = []

print("VESA League - Missing Season Data Diagnostic")
print("="*80)
print()

# Focus on top 20 players
print("Top 20 Players - Season Coverage Analysis:")
print("-"*80)

for i, player in enumerate(combined[:20], 1):
    discord_id = player['canonical_id']
    player_name = player['player_name']

    # Get alias info
    alias_info = discord_to_player.get(discord_id, None)

    print(f"\n{i}. {player_name} (ID: {discord_id})")
    print(f"   Current seasons: {player['seasons_played']}")

    if alias_info:
        print(f"   Known aliases ({len(alias_info['aliases'])}): {', '.join(alias_info['aliases'][:5])}")
        if len(alias_info['aliases']) > 5:
            print(f"   ... and {len(alias_info['aliases']) - 5} more")

        # Check each season for potential matches
        missing_seasons = []
        for season in ['s4', 's5', 's6', 's8', 's11', 's12']:
            season_upper = season.upper()
            if season_upper not in player['seasons_played']:
                # Search this season for any of the player's aliases
                found_in_season = []
                for season_player in seasons_data[season]:
                    pname = season_player.get('player_name', '').lower().strip()
                    if pname in [a.lower().strip() for a in alias_info['aliases']]:
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
            print(f"   ⚠️  POTENTIAL MISSING SEASONS:")
            for ms in missing_seasons:
                print(f"      {ms['season']}: Found {len(ms['matches'])} match(es)")
                for match in ms['matches'][:2]:  # Show first 2 matches
                    print(f"         - {match['name']} (Rank {match['rank']}, Score {match['score']:.2f})")
    else:
        print(f"   ⚠️  NO ALIAS DATA FOUND - player might be missing from alias file")

print("\n" + "="*80)
print("SUMMARY: Review the warnings above to identify missing data")
print("="*80)
