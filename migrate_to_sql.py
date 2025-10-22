#!/usr/bin/env python3
"""
VESA League - JSON to SQLite Migration Script
Converts all JSON data into an optimized relational database
"""

import sqlite3
import json
from collections import defaultdict
from datetime import datetime

print("VESA League - Database Migration Tool")
print("="*70)

# Connect to database (creates if doesn't exist)
db_path = 'vesa_league.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print(f"📁 Creating database: {db_path}\n")

# ============================================================================
# STEP 1: CREATE SCHEMA
# ============================================================================

print("🏗️  Creating database schema...")

# Drop existing tables if they exist (for clean migration)
cursor.executescript('''
    DROP TABLE IF EXISTS audit_log;
    DROP TABLE IF EXISTS division_assignments;
    DROP TABLE IF EXISTS divisions;
    DROP TABLE IF EXISTS team_rosters;
    DROP TABLE IF EXISTS teams;
    DROP TABLE IF EXISTS player_ratings;
    DROP TABLE IF EXISTS player_lobby_performances;
    DROP TABLE IF EXISTS lobby_definitions;
    DROP TABLE IF EXISTS player_aliases;
    DROP TABLE IF EXISTS players;
    DROP TABLE IF EXISTS seasons;
''')

# Create tables with optimized schema
cursor.executescript('''
    -- PLAYERS TABLE
    CREATE TABLE players (
        player_id INTEGER PRIMARY KEY AUTOINCREMENT,
        canonical_name VARCHAR(100) NOT NULL UNIQUE,
        discord_name VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- PLAYER ALIASES TABLE
    CREATE TABLE player_aliases (
        player_id INTEGER NOT NULL,
        alias_name VARCHAR(100) NOT NULL,
        PRIMARY KEY (player_id, alias_name),
        FOREIGN KEY (player_id) REFERENCES players(player_id)
    );

    -- SEASONS TABLE
    CREATE TABLE seasons (
        season_id INTEGER PRIMARY KEY AUTOINCREMENT,
        season_name VARCHAR(20) NOT NULL UNIQUE,
        start_date DATE,
        end_date DATE
    );

    -- LOBBY DEFINITIONS (static reference data)
    CREATE TABLE lobby_definitions (
        lobby_number VARCHAR(10) PRIMARY KEY,
        bonus_percentage DECIMAL(5,2) NOT NULL,
        description TEXT
    );

    -- PLAYER LOBBY PERFORMANCES
    CREATE TABLE player_lobby_performances (
        player_id INTEGER NOT NULL,
        season_id INTEGER NOT NULL,
        day_number INTEGER NOT NULL,
        lobby_number VARCHAR(10) NOT NULL,
        score DECIMAL(10,2),
        kills INTEGER,
        damage INTEGER,
        rank_in_lobby INTEGER,
        PRIMARY KEY (player_id, season_id, day_number),
        FOREIGN KEY (player_id) REFERENCES players(player_id),
        FOREIGN KEY (season_id) REFERENCES seasons(season_id),
        FOREIGN KEY (lobby_number) REFERENCES lobby_definitions(lobby_number)
    );

    -- PLAYER RATINGS (composite primary key)
    CREATE TABLE player_ratings (
        player_id INTEGER NOT NULL,
        season_id INTEGER NOT NULL,
        base_rating DECIMAL(10,2) NOT NULL CHECK (base_rating >= 0),
        lobby_bonus_total DECIMAL(10,2) DEFAULT 0 CHECK (lobby_bonus_total >= 0),
        total_rating DECIMAL(10,2) NOT NULL CHECK (total_rating >= 0),
        rank INTEGER CHECK (rank > 0),
        PRIMARY KEY (player_id, season_id),
        FOREIGN KEY (player_id) REFERENCES players(player_id),
        FOREIGN KEY (season_id) REFERENCES seasons(season_id)
    );

    -- TEAMS TABLE
    CREATE TABLE teams (
        team_id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_name VARCHAR(100) NOT NULL,
        season_id INTEGER NOT NULL,
        tier VARCHAR(10),
        team_rating DECIMAL(10,2),
        schedule_constraint TEXT,
        FOREIGN KEY (season_id) REFERENCES seasons(season_id)
    );

    -- TEAM ROSTERS
    CREATE TABLE team_rosters (
        team_id INTEGER NOT NULL,
        player_id INTEGER NOT NULL,
        position INTEGER NOT NULL CHECK (position BETWEEN 1 AND 3),
        PRIMARY KEY (team_id, player_id),
        UNIQUE (team_id, position),
        FOREIGN KEY (team_id) REFERENCES teams(team_id),
        FOREIGN KEY (player_id) REFERENCES players(player_id)
    );

    -- DIVISIONS TABLE
    CREATE TABLE divisions (
        division_id INTEGER PRIMARY KEY AUTOINCREMENT,
        season_id INTEGER NOT NULL,
        division_number INTEGER NOT NULL,
        division_day VARCHAR(20) NOT NULL,
        UNIQUE (season_id, division_number),
        FOREIGN KEY (season_id) REFERENCES seasons(season_id)
    );

    -- DIVISION ASSIGNMENTS
    CREATE TABLE division_assignments (
        division_id INTEGER NOT NULL,
        team_id INTEGER NOT NULL,
        rank_in_division INTEGER,
        PRIMARY KEY (division_id, team_id),
        FOREIGN KEY (division_id) REFERENCES divisions(division_id),
        FOREIGN KEY (team_id) REFERENCES teams(team_id)
    );

    -- INDEXES for performance
    CREATE INDEX idx_player_ratings_total ON player_ratings(total_rating DESC);
    CREATE INDEX idx_teams_rating ON teams(team_rating DESC);
    CREATE INDEX idx_lobby_perf_player ON player_lobby_performances(player_id);
    CREATE INDEX idx_aliases_name ON player_aliases(alias_name);
    CREATE INDEX idx_team_rosters_team ON team_rosters(team_id);
    CREATE INDEX idx_team_rosters_player ON team_rosters(player_id);
''')

print("✅ Schema created successfully\n")

# ============================================================================
# STEP 2: INSERT STATIC DATA
# ============================================================================

print("📊 Inserting static reference data...")

# Insert lobby definitions
lobby_bonuses = [
    ('1', 81.92, 'Pinnacle - 8192% bonus'),
    ('1.5', 40.96, 'High tier - 4096% bonus'),
    ('2', 20.48, 'Upper mid - 2048% bonus'),
    ('2.5', 10.24, 'Upper-mid tier - 1024% bonus'),
    ('3', 5.12, 'Mid tier - 512% bonus'),
    ('3.5', 2.56, 'Mid tier - 256% bonus'),
    ('4', 1.28, 'Lower-mid tier - 128% bonus'),
    ('4.5', 0.64, 'Lower-mid tier - 64% bonus'),
    ('5', 0.32, 'Lower tier - 32% bonus'),
    ('5.5', 0.16, 'Lower tier - 16% bonus'),
    ('6', 0.08, 'Low tier - 8% bonus'),
    ('6.5', 0.04, 'Low tier - 4% bonus'),
    ('7', 0.02, 'Lowest tier - 2% bonus'),
]

cursor.executemany(
    'INSERT INTO lobby_definitions (lobby_number, bonus_percentage, description) VALUES (?, ?, ?)',
    lobby_bonuses
)

print(f"  ✓ Inserted {len(lobby_bonuses)} lobby definitions")

# Insert seasons
seasons = [
    ('S11', None, None),
    ('S12', None, None),
]

cursor.executemany(
    'INSERT INTO seasons (season_name, start_date, end_date) VALUES (?, ?, ?)',
    seasons
)

print(f"  ✓ Inserted {len(seasons)} seasons\n")

# ============================================================================
# STEP 3: LOAD AND INSERT PLAYER DATA
# ============================================================================

print("👥 Loading player data...")

# Load player aliases
with open('data/player_aliases.json', 'r') as f:
    aliases_data = json.load(f)

# Build player ID mapping
player_id_map = {}  # canonical_name -> player_id

for player_data in aliases_data:
    discord = player_data['discord_name'].strip()
    canonical_lower = discord.lower()

    # Check if player already exists
    existing = cursor.execute(
        'SELECT player_id FROM players WHERE canonical_name = ?',
        (canonical_lower,)
    ).fetchone()

    if existing:
        player_id = existing[0]
    else:
        # Insert new player
        cursor.execute(
            'INSERT INTO players (canonical_name, discord_name) VALUES (?, ?)',
            (canonical_lower, discord)
        )
        player_id = cursor.lastrowid

    player_id_map[canonical_lower] = player_id

    # Insert aliases
    for alias in player_data['aliases']:
        alias_clean = alias.strip()
        if alias_clean:
            cursor.execute(
                'INSERT OR IGNORE INTO player_aliases (player_id, alias_name) VALUES (?, ?)',
                (player_id, alias_clean.lower())
            )

print(f"  ✓ Inserted {len(player_id_map)} players")
print(f"  ✓ Inserted {cursor.execute('SELECT COUNT(*) FROM player_aliases').fetchone()[0]} aliases\n")

# ============================================================================
# STEP 4: LOAD S12 PLACEMENT DATA
# ============================================================================

print("🎮 Loading S12 placement data...")

with open('output/s12_placements_raw.json', 'r') as f:
    s12_raw = json.load(f)

s12_season_id = cursor.execute("SELECT season_id FROM seasons WHERE season_name = 'S12'").fetchone()[0]

performance_count = 0
for entry in s12_raw:
    player_name = entry.get('player_name', '').lower().strip()
    lobby = str(entry.get('lobby', ''))
    day = entry.get('day', 0)
    score = entry.get('score', 0)
    kills = entry.get('kills', 0)
    damage = entry.get('damage', 0)

    if not player_name or not lobby:
        continue

    # Find player ID
    player_id = player_id_map.get(player_name)
    if not player_id:
        # Try to find by alias
        result = cursor.execute(
            'SELECT player_id FROM player_aliases WHERE alias_name = ?',
            (player_name,)
        ).fetchone()
        if result:
            player_id = result[0]

    if player_id:
        cursor.execute('''
            INSERT OR REPLACE INTO player_lobby_performances
            (player_id, season_id, day_number, lobby_number, score, kills, damage)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (player_id, s12_season_id, day, lobby, score, kills, damage))
        performance_count += 1

print(f"  ✓ Inserted {performance_count} lobby performances\n")

# ============================================================================
# STEP 5: LOAD PLAYER RATINGS
# ============================================================================

print("📈 Loading player ratings...")

with open('output/combined_all_seasons_ratings_with_bonus.json', 'r') as f:
    ratings_data = json.load(f)

s11_season_id = cursor.execute("SELECT season_id FROM seasons WHERE season_name = 'S11'").fetchone()[0]

ratings_inserted = 0
for player in ratings_data:
    canonical = player.get('canonical_id', '').lower()

    # Find player ID
    player_id = player_id_map.get(canonical)
    if not player_id:
        result = cursor.execute(
            'SELECT player_id FROM player_aliases WHERE alias_name = ?',
            (player.get('player_name', '').lower(),)
        ).fetchone()
        if result:
            player_id = result[0]

    if not player_id:
        continue

    # S12 rating
    s12_rating = player.get('s12_rating')
    if s12_rating is not None:
        lobby_bonus = player.get('consistency_bonus', 0.0)
        base_rating = s12_rating / (1 + lobby_bonus) if lobby_bonus > 0 else s12_rating

        cursor.execute('''
            INSERT OR REPLACE INTO player_ratings
            (player_id, season_id, base_rating, lobby_bonus_total, total_rating, rank)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (player_id, s12_season_id, base_rating, lobby_bonus, player.get('combined_rating', s12_rating), player.get('rank', 999)))
        ratings_inserted += 1

    # S11 rating
    s11_rating = player.get('s11_rating')
    if s11_rating is not None:
        cursor.execute('''
            INSERT OR REPLACE INTO player_ratings
            (player_id, season_id, base_rating, lobby_bonus_total, total_rating, rank)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (player_id, s11_season_id, s11_rating, 0.0, s11_rating, 999))
        ratings_inserted += 1

print(f"  ✓ Inserted {ratings_inserted} player ratings\n")

# ============================================================================
# STEP 6: LOAD TEAMS AND ROSTERS
# ============================================================================

print("🏆 Loading teams and rosters...")

with open('output/team_ratings_combined.json', 'r') as f:
    teams_data = json.load(f)

teams_inserted = 0
rosters_inserted = 0

for team in teams_data:
    team_name = team.get('team_name', '')
    tier = team.get('tier', '')
    team_rating = team.get('team_rating', 0)
    schedule = team.get('schedule_constraint', '')

    # Insert team
    cursor.execute('''
        INSERT INTO teams (team_name, season_id, tier, team_rating, schedule_constraint)
        VALUES (?, ?, ?, ?, ?)
    ''', (team_name, s12_season_id, tier, team_rating, schedule))
    team_id = cursor.lastrowid
    teams_inserted += 1

    # Insert roster
    for pos in range(1, 4):
        player_name_key = f'player{pos}'
        discord_key = f'discord{pos}'

        player_name = team.get(player_name_key, '').lower()
        if not player_name:
            continue

        # Find player ID
        player_id = player_id_map.get(player_name)
        if not player_id:
            result = cursor.execute(
                'SELECT player_id FROM player_aliases WHERE alias_name = ?',
                (player_name,)
            ).fetchone()
            if result:
                player_id = result[0]

        if player_id:
            cursor.execute('''
                INSERT OR IGNORE INTO team_rosters (team_id, player_id, position)
                VALUES (?, ?, ?)
            ''', (team_id, player_id, pos))
            rosters_inserted += 1

print(f"  ✓ Inserted {teams_inserted} teams")
print(f"  ✓ Inserted {rosters_inserted} roster entries\n")

# ============================================================================
# STEP 7: LOAD DIVISION ASSIGNMENTS
# ============================================================================

print("🎯 Loading division assignments...")

with open('output/division_assignments.json', 'r') as f:
    divisions_data = json.load(f)

divisions_inserted = 0
assignments_inserted = 0

for div_num, div_data in divisions_data['divisions'].items():
    # Insert division
    cursor.execute('''
        INSERT INTO divisions (season_id, division_number, division_day)
        VALUES (?, ?, ?)
    ''', (s12_season_id, int(div_num), div_data['day']))
    division_id = cursor.lastrowid
    divisions_inserted += 1

    # Insert team assignments
    for idx, team_data in enumerate(div_data['teams'], 1):
        team_name = team_data['team_name']

        # Find team ID
        result = cursor.execute(
            'SELECT team_id FROM teams WHERE team_name = ? AND season_id = ?',
            (team_name, s12_season_id)
        ).fetchone()

        if result:
            team_id = result[0]
            cursor.execute('''
                INSERT INTO division_assignments (division_id, team_id, rank_in_division)
                VALUES (?, ?, ?)
            ''', (division_id, team_id, idx))
            assignments_inserted += 1

print(f"  ✓ Inserted {divisions_inserted} divisions")
print(f"  ✓ Inserted {assignments_inserted} division assignments\n")

# ============================================================================
# STEP 8: COMMIT AND VERIFY
# ============================================================================

conn.commit()
print("💾 Changes committed to database\n")

print("="*70)
print("📊 DATABASE STATISTICS")
print("="*70)

stats_queries = [
    ("Players", "SELECT COUNT(*) FROM players"),
    ("Player Aliases", "SELECT COUNT(*) FROM player_aliases"),
    ("Seasons", "SELECT COUNT(*) FROM seasons"),
    ("Lobby Definitions", "SELECT COUNT(*) FROM lobby_definitions"),
    ("Lobby Performances", "SELECT COUNT(*) FROM player_lobby_performances"),
    ("Player Ratings", "SELECT COUNT(*) FROM player_ratings"),
    ("Teams", "SELECT COUNT(*) FROM teams"),
    ("Roster Entries", "SELECT COUNT(*) FROM team_rosters"),
    ("Divisions", "SELECT COUNT(*) FROM divisions"),
    ("Division Assignments", "SELECT COUNT(*) FROM division_assignments"),
]

for name, query in stats_queries:
    count = cursor.execute(query).fetchone()[0]
    print(f"  {name:<25} {count:>6}")

print("\n" + "="*70)
print("✅ MIGRATION COMPLETE!")
print("="*70)
print(f"\nDatabase saved to: {db_path}")
print("\nYou can now query the database using SQL:")
print("  sqlite3 vesa_league.db")
print("\nOr use Python with sqlite3 module")

conn.close()
