"""
Weighting system for lobby difficulty and day progression.
Implements the hybrid scoring approach from the design document.
"""

import json
from pathlib import Path
from typing import Dict


class WeightingSystem:
    """Manages lobby and day weights for calculating adjusted scores."""

    def __init__(self, config_path: str = "config/weights.json"):
        """
        Load weighting configuration from JSON file.

        Args:
            config_path: Path to weights configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.lobby_weights = self.config['lobby_weights']['weights']
        self.day_weights = self.config['day_weights']['weights']

    def _load_config(self) -> Dict:
        """Load configuration from JSON file."""
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def get_lobby_weight(self, lobby: str) -> float:
        """
        Get weight for a specific lobby.

        Args:
            lobby: Lobby identifier (e.g., "1", "1.5", "7")

        Returns:
            Weight multiplier for the lobby

        Raises:
            ValueError: If lobby not found in configuration
        """
        lobby_str = str(lobby)
        if lobby_str not in self.lobby_weights:
            raise ValueError(f"Lobby '{lobby}' not found in configuration")
        return self.lobby_weights[lobby_str]

    def get_day_weight(self, day: int) -> float:
        """
        Get weight for a specific day.

        Args:
            day: Day number (1-4)

        Returns:
            Weight multiplier for the day

        Raises:
            ValueError: If day not found in configuration
        """
        day_str = str(day)
        if day_str not in self.day_weights:
            raise ValueError(f"Day {day} not found in configuration")
        return self.day_weights[day_str]

    def calculate_weighted_score(self, raw_score: float, day: int, lobby: str) -> float:
        """
        Calculate weighted score applying both lobby and day multipliers.

        Formula: weighted_score = raw_score × lobby_weight × day_weight

        Args:
            raw_score: Original match score
            day: Day number (1-4)
            lobby: Lobby identifier

        Returns:
            Weighted score

        Example:
            >>> ws = WeightingSystem()
            >>> ws.calculate_weighted_score(50, day=3, lobby="2")
            54.0  # 50 × 0.80 (lobby 2) × 1.35 (day 3) = 54.0
        """
        lobby_weight = self.get_lobby_weight(lobby)
        day_weight = self.get_day_weight(day)

        weighted = raw_score * lobby_weight * day_weight

        return weighted

    def get_weight_info(self, day: int, lobby: str) -> Dict:
        """
        Get detailed weight information for a day/lobby combination.

        Args:
            day: Day number
            lobby: Lobby identifier

        Returns:
            Dictionary with weight details
        """
        lobby_weight = self.get_lobby_weight(lobby)
        day_weight = self.get_day_weight(day)
        combined_weight = lobby_weight * day_weight

        return {
            "day": day,
            "lobby": lobby,
            "lobby_weight": lobby_weight,
            "day_weight": day_weight,
            "combined_weight": combined_weight,
            "explanation": f"Points are multiplied by {combined_weight:.3f} "
                          f"(lobby: {lobby_weight}, day: {day_weight})"
        }

    def print_weight_table(self):
        """Print a formatted table of all weights (for debugging/documentation)."""
        print("\n=== LOBBY WEIGHTS ===")
        print(f"System: {self.config['lobby_weights']['system']}")
        print(f"Decay Factor: {self.config['lobby_weights']['decay_factor']}")
        print("\nLobby | Weight")
        print("-" * 20)
        for lobby, weight in sorted(self.lobby_weights.items(), key=lambda x: float(x[0])):
            print(f"{lobby:>5} | {weight:.3f}")

        print("\n=== DAY WEIGHTS ===")
        print(f"System: {self.config['day_weights']['system']}")
        print(f"Description: {self.config['day_weights']['description']}")
        print("\nDay | Weight")
        print("-" * 20)
        for day, weight in sorted(self.day_weights.items(), key=lambda x: int(x[0])):
            print(f"{day:>3} | {weight:.2f}")

        print("\n=== COMBINED WEIGHT EXAMPLES ===")
        print("Day | Lobby | Combined Weight")
        print("-" * 35)
        for day in ["1", "2", "3", "4"]:
            for lobby in ["1", "2", "5", "7"]:
                combined = self.get_lobby_weight(lobby) * self.get_day_weight(int(day))
                print(f"{day:>3} | {lobby:>5} | {combined:.3f}")
