#!/usr/bin/env python3
"""
Scrape individual match/game data from Overstat API
This gives us game-by-game team placements and player stats
Enables advanced metrics: Elo, consistency, clutch performance, etc.
"""

import json
import subprocess
import time

# Tournament IDs extracted from URLs
tournaments = {
    # Season 4
    'S4_Pinnacle': 3184,
    'S4_Challengers': 3098,
    'S4_Contenders': 3077,

    # Season 5
    'S5_Pinnacle': 4076,
    'S5_Ascendant': 4624,
    'S5_Challengers': 4623,
    'S5_Contenders': 4077,

    # Season 6
    'S6_Pinnacle': 6146,
    'S6_Ascendant': 6145,
    'S6_Challengers': 6144,
    'S6_Contenders': 6143,

    # Season 8 (labeled as S3 in URLs but is actually S8)
    'S8_Pinnacle': 12656,
    'S8_Ascendant': 12654,
    'S8_Emergent': 12652,
    'S8_Challengers': 12650,
    'S8_Tendies': 12648,

    # Season 11
    'S11_Pinnacle': 13938,
    # S11 other divisions share IDs with S8 (12656, 12654, 12652, 12650, 12648)
    # Skipping to avoid duplicates - will capture from S8 data

    # Season 12 - No "all weeks" tournaments found, only placement lobbies
    # Match data not available via API for S12
}

print("VESA League - Match Data Scraper")
print("="*70)
print(f"\nFetching match data for {len(tournaments)} tournaments...\n")

all_match_data = {}
failed = []

for name, tournament_id in tournaments.items():
    print(f"Fetching {name} (ID: {tournament_id})...")

    try:
        # Use curl to fetch the API endpoint
        url = f'https://overstat.gg/api/stats/{tournament_id}/overall'
        result = subprocess.run(
            ['curl', '-s', url],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)

            # Validate we got games data
            if 'games' in data and len(data['games']) > 0:
                all_match_data[name] = data
                print(f"  ✓ {len(data['games'])} games fetched")
            else:
                print(f"  ⚠️  No games found")
                failed.append(name)
        else:
            print(f"  ❌ Fetch failed")
            failed.append(name)

        time.sleep(1)  # Be nice to the API

    except Exception as e:
        print(f"  ❌ Error: {e}")
        failed.append(name)

# Save all match data
output_file = 'output/match_data_all_tournaments.json'
with open(output_file, 'w') as f:
    json.dump(all_match_data, f, indent=2)

# Statistics
print("\n" + "="*70)
print("SUMMARY:")
print("-"*70)
print(f"Total tournaments: {len(tournaments)}")
print(f"Successfully fetched: {len(all_match_data)}")
print(f"Failed: {len(failed)}")

if failed:
    print(f"\nFailed tournaments: {', '.join(failed)}")

total_games = sum(len(data['games']) for data in all_match_data.values())
print(f"\nTotal games collected: {total_games}")

# Show games per tournament
print("\nGames per tournament:")
for name, data in all_match_data.items():
    print(f"  {name}: {len(data['games'])} games")

print(f"\n✓ Match data saved to: {output_file}")

# Show what we can do with this data
print("\n" + "="*70)
print("WHAT WE CAN BUILD WITH THIS DATA:")
print("-"*70)
print("""
✓ Elo Rating System: Update ratings after each game based on placement
✓ Consistency Metrics: Variance in placement across games
✓ Clutch Performance: Late-game performance when eliminated teams < 5
✓ Head-to-Head Records: Direct competition history between teams
✓ Hot Streaks: Recent form weighting (last 10 games vs full season)
✓ Player-Level Analysis: Individual performance independent of team
✓ Character Meta: Most successful legend compositions
✓ Damage Efficiency: Damage per kill, damage per placement point
✓ Combat Metrics: Knock rate, assist rate, headshot accuracy
""")
