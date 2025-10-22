#!/usr/bin/env python3
"""
VESA League - SQL Query Examples
Demonstrates how to query the database
"""

import sqlite3

# Connect to database
conn = sqlite3.connect('vesa_league.db')
conn.row_factory = sqlite3.Row  # Access columns by name
cursor = conn.cursor()

print("VESA League - SQL Query Examples")
print("="*70)

# =============================================================================
# QUERY 1: Get Lau's team and teammates
# =============================================================================
print("\n1️⃣  LAU'S TEAM:")
print("-"*70)

query = '''
    SELECT
        t.team_name,
        t.tier,
        t.team_rating,
        p.canonical_name,
        pr.total_rating,
        pr.lobby_bonus_total
    FROM teams t
    JOIN team_rosters tr ON t.team_id = tr.team_id
    JOIN players p ON tr.player_id = p.player_id
    JOIN player_ratings pr ON p.player_id = pr.player_id AND t.season_id = pr.season_id
    WHERE t.team_name IN (
        SELECT DISTINCT teams.team_name
        FROM teams
        JOIN team_rosters ON teams.team_id = team_rosters.team_id
        JOIN players ON team_rosters.player_id = players.player_id
        WHERE players.canonical_name = 'lau'
    )
    ORDER BY pr.total_rating DESC
'''

results = cursor.execute(query).fetchall()
if results:
    team_name = results[0]['team_name']
    tier = results[0]['tier']
    team_rating = results[0]['team_rating']

    print(f"Team: {team_name}")
    print(f"Tier: {tier} | Team Rating: {team_rating:.2f}\n")
    print(f"{'Player':<25} {'Rating':<12} {'Lobby Bonus'}")
    print("-"*70)

    for row in results:
        bonus_pct = row['lobby_bonus_total'] * 100
        print(f"{row['canonical_name']:<25} {row['total_rating']:<12.2f} +{bonus_pct:.0f}%")

# =============================================================================
# QUERY 2: Players with 1000%+ bonuses
# =============================================================================
print("\n\n2️⃣  PLAYERS WITH 1000%+ LOBBY BONUSES:")
print("-"*70)

query = '''
    SELECT
        p.canonical_name,
        pr.lobby_bonus_total,
        pr.total_rating,
        GROUP_CONCAT(plp.lobby_number, ', ') as lobbies
    FROM players p
    JOIN player_ratings pr ON p.player_id = pr.player_id
    JOIN player_lobby_performances plp ON p.player_id = plp.player_id AND pr.season_id = plp.season_id
    WHERE pr.lobby_bonus_total >= 10.0
    GROUP BY p.player_id
    ORDER BY pr.lobby_bonus_total DESC
    LIMIT 10
'''

results = cursor.execute(query).fetchall()
print(f"{'Player':<25} {'Bonus':<10} {'Rating':<12} {'Lobbies'}")
print("-"*70)

for row in results:
    bonus_pct = row['lobby_bonus_total'] * 100
    print(f"{row['canonical_name']:<25} +{bonus_pct:<9.0f}% {row['total_rating']:<12.2f} {row['lobbies']}")

# =============================================================================
# QUERY 3: Top 10 teams by rating
# =============================================================================
print("\n\n3️⃣  TOP 10 TEAMS:")
print("-"*70)

query = '''
    SELECT
        t.team_name,
        t.team_rating,
        t.tier,
        d.division_number,
        d.division_day
    FROM teams t
    LEFT JOIN division_assignments da ON t.team_id = da.team_id
    LEFT JOIN divisions d ON da.division_id = d.division_id
    ORDER BY t.team_rating DESC
    LIMIT 10
'''

results = cursor.execute(query).fetchall()
print(f"{'Rank':<6} {'Team':<30} {'Rating':<12} {'Tier':<6} {'Division'}")
print("-"*70)

for idx, row in enumerate(results, 1):
    div_info = f"Div {row['division_number']} ({row['division_day']})" if row['division_number'] else "N/A"
    print(f"{idx:<6} {row['team_name']:<30} {row['team_rating']:<12.2f} {row['tier']:<6} {div_info}")

# =============================================================================
# QUERY 4: Division 1 teams
# =============================================================================
print("\n\n4️⃣  DIVISION 1 TEAMS:")
print("-"*70)

query = '''
    SELECT
        da.rank_in_division,
        t.team_name,
        t.team_rating,
        t.tier
    FROM divisions d
    JOIN division_assignments da ON d.division_id = da.division_id
    JOIN teams t ON da.team_id = t.team_id
    WHERE d.division_number = 1
    ORDER BY da.rank_in_division
'''

results = cursor.execute(query).fetchall()
print(f"{'Rank':<6} {'Team':<30} {'Rating':<12} {'Tier'}")
print("-"*70)

for row in results:
    print(f"{row['rank_in_division']:<6} {row['team_name']:<30} {row['team_rating']:<12.2f} {row['tier']}")

# =============================================================================
# QUERY 5: Lobby performance summary
# =============================================================================
print("\n\n5️⃣  LOBBY PERFORMANCE DISTRIBUTION:")
print("-"*70)

query = '''
    SELECT
        ld.lobby_number,
        ld.bonus_percentage,
        COUNT(DISTINCT plp.player_id) as unique_players,
        COUNT(*) as total_appearances,
        AVG(plp.score) as avg_score
    FROM lobby_definitions ld
    LEFT JOIN player_lobby_performances plp ON ld.lobby_number = plp.lobby_number
    GROUP BY ld.lobby_number
    ORDER BY ld.bonus_percentage DESC
'''

results = cursor.execute(query).fetchall()
print(f"{'Lobby':<8} {'Bonus':<10} {'Players':<10} {'Appearances':<15} {'Avg Score'}")
print("-"*70)

for row in results:
    bonus_pct = row['bonus_percentage'] * 100
    avg_score = row['avg_score'] if row['avg_score'] else 0
    print(f"{row['lobby_number']:<8} +{bonus_pct:<9.0f}% {row['unique_players']:<10} {row['total_appearances']:<15} {avg_score:.2f}")

# =============================================================================
# QUERY 6: Search player by alias
# =============================================================================
print("\n\n6️⃣  SEARCH BY ALIAS (Example: 'tragic'):")
print("-"*70)

search_term = 'tragic'
query = '''
    SELECT
        p.canonical_name,
        p.discord_name,
        pa.alias_name,
        pr.total_rating
    FROM player_aliases pa
    JOIN players p ON pa.player_id = p.player_id
    LEFT JOIN player_ratings pr ON p.player_id = pr.player_id
    WHERE pa.alias_name LIKE ?
    LIMIT 5
'''

results = cursor.execute(query, (f'%{search_term}%',)).fetchall()
for row in results:
    rating = row['total_rating'] if row['total_rating'] else 'N/A'
    print(f"Alias: {row['alias_name']} → Canonical: {row['canonical_name']} (Rating: {rating})")

print("\n" + "="*70)
print("✅ Query examples complete!")
print("\nDatabase location: vesa_league.db")
print("You can run: sqlite3 vesa_league.db")

conn.close()
