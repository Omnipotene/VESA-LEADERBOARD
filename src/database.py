"""
Database management for VESA scraper.
Handles SQLite database creation, connections, and data operations.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import json


class Database:
    """Manages SQLite database operations for VESA player statistics."""

    def __init__(self, db_path: str = "data/vesa.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        self.cursor = self.conn.cursor()

    def _create_tables(self):
        """Create database tables if they don't exist."""

        # Matches table - stores raw scraped match data
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                day INTEGER NOT NULL,
                lobby TEXT NOT NULL,
                match_type TEXT NOT NULL,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data TEXT,
                UNIQUE(url)
            )
        """)

        # Player stats table - stores individual player performance per match
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL,
                player_name TEXT NOT NULL,
                team_name TEXT,
                score REAL NOT NULL,
                kills INTEGER NOT NULL,
                damage INTEGER NOT NULL,
                placement INTEGER,
                day INTEGER NOT NULL,
                lobby TEXT NOT NULL,
                FOREIGN KEY (match_id) REFERENCES matches(id),
                UNIQUE(match_id, player_name)
            )
        """)

        # Aggregated player stats - calculated weighted totals
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_aggregated (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT UNIQUE NOT NULL,
                total_weighted_score REAL NOT NULL,
                total_kills INTEGER NOT NULL,
                total_damage INTEGER NOT NULL,
                matches_played INTEGER NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Configuration tracking - stores which weights were used
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS config_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_type TEXT NOT NULL,
                config_data TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    def insert_match(self, url: str, day: int, lobby: str, match_type: str, raw_data: Dict) -> int:
        """
        Insert a match record.

        Args:
            url: Overstat.gg URL
            day: Day number (1-4)
            lobby: Lobby identifier (e.g., "1", "1.5", "2")
            match_type: "player" or "team"
            raw_data: Raw scraped data as dict

        Returns:
            Match ID
        """
        try:
            self.cursor.execute("""
                INSERT INTO matches (url, day, lobby, match_type, raw_data)
                VALUES (?, ?, ?, ?, ?)
            """, (url, day, lobby, match_type, json.dumps(raw_data)))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # Match already exists, return existing ID
            self.cursor.execute("SELECT id FROM matches WHERE url = ?", (url,))
            return self.cursor.fetchone()[0]

    def insert_player_stat(self, match_id: int, player_name: str, team_name: Optional[str],
                          score: float, kills: int, damage: int, day: int, lobby: str,
                          placement: Optional[int] = None):
        """
        Insert individual player statistics for a match.

        Args:
            match_id: Foreign key to matches table
            player_name: Player's in-game name
            team_name: Team name (if available)
            score: Match score (ALGS scoring)
            kills: Total kills
            damage: Total damage
            day: Day number
            lobby: Lobby identifier
            placement: Team placement (if available)
        """
        try:
            self.cursor.execute("""
                INSERT INTO player_stats
                (match_id, player_name, team_name, score, kills, damage, placement, day, lobby)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (match_id, player_name, team_name, score, kills, damage, placement, day, lobby))
            self.conn.commit()
        except sqlite3.IntegrityError:
            # Duplicate entry, skip or update
            pass

    def get_all_player_stats(self) -> List[sqlite3.Row]:
        """Retrieve all player statistics."""
        self.cursor.execute("""
            SELECT * FROM player_stats
            ORDER BY player_name, day, lobby
        """)
        return self.cursor.fetchall()

    def get_player_stats_by_name(self, player_name: str) -> List[sqlite3.Row]:
        """Get all stats for a specific player."""
        self.cursor.execute("""
            SELECT * FROM player_stats
            WHERE player_name = ?
            ORDER BY day, lobby
        """, (player_name,))
        return self.cursor.fetchall()

    def save_aggregated_stats(self, player_name: str, weighted_score: float,
                             total_kills: int, total_damage: int, matches_played: int):
        """
        Save or update aggregated player statistics.

        Args:
            player_name: Player's name
            weighted_score: Total weighted score across all matches
            total_kills: Total kills
            total_damage: Total damage
            matches_played: Number of matches played
        """
        self.cursor.execute("""
            INSERT OR REPLACE INTO player_aggregated
            (player_name, total_weighted_score, total_kills, total_damage, matches_played, last_updated)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (player_name, weighted_score, total_kills, total_damage, matches_played))
        self.conn.commit()

    def get_leaderboard(self, limit: Optional[int] = None) -> List[sqlite3.Row]:
        """
        Get player leaderboard sorted by weighted score.

        Args:
            limit: Maximum number of results (None = all)

        Returns:
            List of player records sorted by score
        """
        query = """
            SELECT
                ROW_NUMBER() OVER (ORDER BY total_weighted_score DESC) as rank,
                player_name,
                total_weighted_score,
                total_kills,
                total_damage,
                matches_played
            FROM player_aggregated
            ORDER BY total_weighted_score DESC
        """
        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query)
        return self.cursor.fetchall()

    def save_config(self, config_type: str, config_data: Dict):
        """Save configuration to history."""
        self.cursor.execute("""
            INSERT INTO config_history (config_type, config_data)
            VALUES (?, ?)
        """, (config_type, json.dumps(config_data)))
        self.conn.commit()

    def clear_all_data(self):
        """Clear all data from tables (useful for fresh runs)."""
        tables = ['player_stats', 'matches', 'player_aggregated']
        for table in tables:
            self.cursor.execute(f"DELETE FROM {table}")
        self.conn.commit()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
