"""
CSV export functionality for player leaderboards.
"""

import csv
from pathlib import Path
from typing import List, Dict
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSVExporter:
    """Exports player leaderboard data to CSV format."""

    def __init__(self, output_dir: str = "output"):
        """
        Initialize CSV exporter.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_leaderboard(self, players: List[Dict], filename: str = None) -> str:
        """
        Export player leaderboard to CSV.

        Args:
            players: List of player stat dictionaries (sorted by rank)
            filename: Output filename (auto-generated if None)

        Returns:
            Path to exported CSV file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"player_leaderboard_{timestamp}.csv"

        output_path = self.output_dir / filename

        logger.info(f"Exporting leaderboard to: {output_path}")

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow([
                'Rank',
                'Player Name',
                'Total Points',
                'Total Kills',
                'Total Damage',
                'Matches Played',
                'Avg Points/Match'
            ])

            # Write player data
            for rank, player in enumerate(players, start=1):
                writer.writerow([
                    rank,
                    player['player_name'],
                    f"{player['total_weighted_score']:.2f}",
                    player['total_kills'],
                    player['total_damage'],
                    player['matches_played'],
                    f"{player['average_weighted_score']:.2f}"
                ])

        logger.info(f"Exported {len(players)} players to {output_path}")
        return str(output_path)

    def export_detailed_leaderboard(self, players: List[Dict], filename: str = None) -> str:
        """
        Export detailed leaderboard with per-match breakdown.

        Args:
            players: List of player stat dictionaries with match history
            filename: Output filename (auto-generated if None)

        Returns:
            Path to exported CSV file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"player_leaderboard_detailed_{timestamp}.csv"

        output_path = self.output_dir / filename

        logger.info(f"Exporting detailed leaderboard to: {output_path}")

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow([
                'Rank',
                'Player Name',
                'Total Points',
                'Total Kills',
                'Total Damage',
                'Matches Played',
                'Day',
                'Lobby',
                'Raw Score',
                'Weighted Score',
                'Match Kills',
                'Match Damage'
            ])

            # Write player data with match details
            for rank, player in enumerate(players, start=1):
                # First row with totals
                first_match = player['matches'][0] if player['matches'] else {}

                writer.writerow([
                    rank,
                    player['player_name'],
                    f"{player['total_weighted_score']:.2f}",
                    player['total_kills'],
                    player['total_damage'],
                    player['matches_played'],
                    first_match.get('day', ''),
                    first_match.get('lobby', ''),
                    first_match.get('raw_score', ''),
                    f"{first_match.get('weighted_score', 0):.2f}",
                    first_match.get('kills', ''),
                    first_match.get('damage', '')
                ])

                # Additional rows for remaining matches
                for match in player['matches'][1:]:
                    writer.writerow([
                        '',  # Rank (blank for continuation)
                        '',  # Player name (blank for continuation)
                        '',  # Total points (blank for continuation)
                        '',  # Total kills (blank for continuation)
                        '',  # Total damage (blank for continuation)
                        '',  # Matches played (blank for continuation)
                        match['day'],
                        match['lobby'],
                        match['raw_score'],
                        f"{match['weighted_score']:.2f}",
                        match['kills'],
                        match['damage']
                    ])

        logger.info(f"Exported detailed leaderboard for {len(players)} players")
        return str(output_path)

    def export_summary_stats(self, players: List[Dict], filename: str = None) -> str:
        """
        Export summary statistics about the dataset.

        Args:
            players: List of player stat dictionaries
            filename: Output filename (auto-generated if None)

        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"summary_stats_{timestamp}.txt"

        output_path = self.output_dir / filename

        total_players = len(players)
        total_matches = sum(p['matches_played'] for p in players)
        total_kills = sum(p['total_kills'] for p in players)
        total_damage = sum(p['total_damage'] for p in players)

        avg_score = sum(p['total_weighted_score'] for p in players) / total_players if total_players > 0 else 0
        avg_kills = total_kills / total_players if total_players > 0 else 0
        avg_damage = total_damage / total_players if total_players > 0 else 0

        with open(output_path, 'w') as f:
            f.write("VESA LEAGUE PLAYER STATISTICS SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("OVERVIEW\n")
            f.write("-" * 60 + "\n")
            f.write(f"Total Players:           {total_players}\n")
            f.write(f"Total Matches Recorded:  {total_matches}\n")
            f.write(f"Total Kills:             {total_kills:,}\n")
            f.write(f"Total Damage:            {total_damage:,}\n\n")

            f.write("AVERAGES\n")
            f.write("-" * 60 + "\n")
            f.write(f"Avg Weighted Score:      {avg_score:.2f}\n")
            f.write(f"Avg Kills per Player:    {avg_kills:.2f}\n")
            f.write(f"Avg Damage per Player:   {avg_damage:,.0f}\n\n")

            if total_players > 0:
                f.write("TOP 10 PLAYERS\n")
                f.write("-" * 60 + "\n")
                f.write(f"{'Rank':<6}{'Player':<25}{'Points':<12}{'Kills':<10}{'Damage'}\n")
                f.write("-" * 60 + "\n")

                for rank, player in enumerate(players[:10], start=1):
                    f.write(f"{rank:<6}{player['player_name']:<25}"
                           f"{player['total_weighted_score']:<12.2f}"
                           f"{player['total_kills']:<10}"
                           f"{player['total_damage']:,}\n")

        logger.info(f"Exported summary statistics to {output_path}")
        return str(output_path)
