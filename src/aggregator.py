"""
Player statistics aggregation engine.
Calculates weighted totals across all matches for each player.
"""

from typing import Dict, List
from collections import defaultdict
import logging
from .database import Database
from .weights import WeightingSystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlayerAggregator:
    """Aggregates player statistics across multiple matches with weighting."""

    def __init__(self, db: Database, weighting: WeightingSystem):
        """
        Initialize aggregator.

        Args:
            db: Database instance
            weighting: WeightingSystem instance
        """
        self.db = db
        self.weighting = weighting

    def aggregate_all_players(self) -> Dict[str, Dict]:
        """
        Aggregate statistics for all players across all matches.

        Returns:
            Dictionary mapping player_name to aggregated stats
        """
        logger.info("Aggregating player statistics...")

        # Get all player stats from database
        all_stats = self.db.get_all_player_stats()

        if not all_stats:
            logger.warning("No player stats found in database")
            return {}

        # Group stats by player
        player_data = defaultdict(lambda: {
            'weighted_scores': [],
            'total_kills': 0,
            'total_damage': 0,
            'matches': []
        })

        for stat in all_stats:
            player_name = stat['player_name']
            raw_score = stat['score']
            kills = stat['kills']
            damage = stat['damage']
            day = stat['day']
            lobby = stat['lobby']

            # Calculate weighted score for this match
            weighted_score = self.weighting.calculate_weighted_score(
                raw_score=raw_score,
                day=day,
                lobby=lobby
            )

            # Accumulate data
            player_data[player_name]['weighted_scores'].append(weighted_score)
            player_data[player_name]['total_kills'] += kills
            player_data[player_name]['total_damage'] += damage
            player_data[player_name]['matches'].append({
                'day': day,
                'lobby': lobby,
                'raw_score': raw_score,
                'weighted_score': weighted_score,
                'kills': kills,
                'damage': damage
            })

        # Calculate final aggregated stats
        aggregated = {}
        for player_name, data in player_data.items():
            total_weighted_score = sum(data['weighted_scores'])
            matches_played = len(data['matches'])

            aggregated[player_name] = {
                'player_name': player_name,
                'total_weighted_score': total_weighted_score,
                'total_kills': data['total_kills'],
                'total_damage': data['total_damage'],
                'matches_played': matches_played,
                'average_weighted_score': total_weighted_score / matches_played if matches_played > 0 else 0,
                'matches': data['matches']
            }

        logger.info(f"Aggregated stats for {len(aggregated)} players")
        return aggregated

    def save_aggregated_stats(self, aggregated: Dict[str, Dict]):
        """
        Save aggregated statistics to database.

        Args:
            aggregated: Dictionary of aggregated player stats
        """
        logger.info("Saving aggregated statistics to database...")

        for player_name, stats in aggregated.items():
            self.db.save_aggregated_stats(
                player_name=player_name,
                weighted_score=stats['total_weighted_score'],
                total_kills=stats['total_kills'],
                total_damage=stats['total_damage'],
                matches_played=stats['matches_played']
            )

        logger.info("Aggregated statistics saved successfully")

    def get_player_summary(self, player_name: str) -> Dict:
        """
        Get detailed summary for a specific player.

        Args:
            player_name: Player's name

        Returns:
            Dictionary with player's aggregated stats and match history
        """
        aggregated = self.aggregate_all_players()
        return aggregated.get(player_name, {})

    def get_top_players(self, limit: int = 20) -> List[Dict]:
        """
        Get top N players by weighted score.

        Args:
            limit: Number of top players to return

        Returns:
            List of player stat dictionaries, sorted by score
        """
        aggregated = self.aggregate_all_players()

        # Sort by total weighted score
        sorted_players = sorted(
            aggregated.values(),
            key=lambda x: x['total_weighted_score'],
            reverse=True
        )

        return sorted_players[:limit]

    def print_player_summary(self, player_name: str):
        """
        Print detailed summary for a player (for debugging).

        Args:
            player_name: Player's name
        """
        summary = self.get_player_summary(player_name)

        if not summary:
            print(f"No data found for player: {player_name}")
            return

        print(f"\n{'='*60}")
        print(f"PLAYER SUMMARY: {player_name}")
        print(f"{'='*60}")
        print(f"Total Weighted Score: {summary['total_weighted_score']:.2f}")
        print(f"Total Kills: {summary['total_kills']}")
        print(f"Total Damage: {summary['total_damage']:,}")
        print(f"Matches Played: {summary['matches_played']}")
        print(f"Average Weighted Score: {summary['average_weighted_score']:.2f}")
        print(f"\n{'Match History':^60}")
        print(f"{'-'*60}")
        print(f"{'Day':<6}{'Lobby':<8}{'Raw Score':<12}{'Weighted':<12}{'Kills':<8}{'Damage':<10}")
        print(f"{'-'*60}")

        for match in summary['matches']:
            print(f"{match['day']:<6}{match['lobby']:<8}{match['raw_score']:<12.1f}"
                  f"{match['weighted_score']:<12.2f}{match['kills']:<8}{match['damage']:<10,}")

        print(f"{'='*60}\n")
