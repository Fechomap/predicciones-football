"""Poisson distribution analyzer for expected goals"""
import numpy as np
from scipy.stats import poisson
from typing import Dict, Tuple

from ..utils.logger import setup_logger

logger = setup_logger(__name__)

# Real league averages (goals per match) - Updated from actual data
LEAGUE_AVG_GOALS = {
    262: 2.3,   # Liga MX
    39: 2.8,    # Premier League
    140: 2.6,   # La Liga
    78: 3.0,    # Bundesliga
    135: 2.7,   # Serie A
    61: 2.6,    # Ligue 1
}

DEFAULT_LEAGUE_AVG = 2.5  # Fallback if league not in dict


class PoissonAnalyzer:
    """
    Analyzes expected goals using Poisson distribution

    This is a statistical method (NOT AI/ML) that uses probability theory
    to calculate expected goals based on team performance
    """

    @staticmethod
    def calculate_expected_goals(
        home_team_stats: Dict,
        away_team_stats: Dict,
        league_id: int = None,
        league_avg_goals: float = None
    ) -> Tuple[float, float]:
        """
        Calculate expected goals for both teams using Poisson distribution

        Args:
            home_team_stats: Home team statistics
            away_team_stats: Away team statistics
            league_id: League ID (to get real average)
            league_avg_goals: Manual override for league average

        Returns:
            Tuple of (expected_home_goals, expected_away_goals)
        """
        # Get league average (real data based on league)
        if league_avg_goals is None:
            league_avg_goals = LEAGUE_AVG_GOALS.get(league_id, DEFAULT_LEAGUE_AVG)
            logger.debug(f"Using league avg goals: {league_avg_goals} for league {league_id}")
        # Extract stats
        home_matches = home_team_stats.get("home_matches", 1)
        home_scored = home_team_stats.get("home_goals_scored", 0)
        home_conceded = home_team_stats.get("home_goals_conceded", 0)

        away_matches = away_team_stats.get("away_matches", 1)
        away_scored = away_team_stats.get("away_goals_scored", 0)
        away_conceded = away_team_stats.get("away_goals_conceded", 0)

        # Calculate averages (avoid division by zero)
        home_attack_avg = home_scored / max(home_matches, 1)
        home_defense_avg = home_conceded / max(home_matches, 1)

        away_attack_avg = away_scored / max(away_matches, 1)
        away_defense_avg = away_conceded / max(away_matches, 1)

        # Calculate attack and defense strengths relative to league average
        home_attack_strength = home_attack_avg / league_avg_goals
        home_defense_strength = home_defense_avg / league_avg_goals

        away_attack_strength = away_attack_avg / league_avg_goals
        away_defense_strength = away_defense_avg / league_avg_goals

        # Calculate expected goals
        expected_home_goals = (
            home_attack_strength * away_defense_strength * league_avg_goals
        )
        expected_away_goals = (
            away_attack_strength * home_defense_strength * league_avg_goals
        )

        logger.debug(
            f"Expected goals calculated: Home={expected_home_goals:.2f}, "
            f"Away={expected_away_goals:.2f}"
        )

        return round(expected_home_goals, 2), round(expected_away_goals, 2)

    @staticmethod
    def calculate_match_probabilities(
        expected_home_goals: float,
        expected_away_goals: float,
        max_goals: int = 10
    ) -> Dict[str, float]:
        """
        Calculate match outcome probabilities using Poisson distribution

        Args:
            expected_home_goals: Expected goals for home team
            expected_away_goals: Expected goals for away team
            max_goals: Maximum goals to consider in simulation

        Returns:
            Dictionary with probabilities for home_win, draw, away_win
        """
        home_win_prob = 0.0
        draw_prob = 0.0
        away_win_prob = 0.0

        # Calculate probability for each possible score combination
        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):
                # Probability of this exact score using Poisson distribution
                prob = (
                    poisson.pmf(home_goals, expected_home_goals) *
                    poisson.pmf(away_goals, expected_away_goals)
                )

                if home_goals > away_goals:
                    home_win_prob += prob
                elif home_goals == away_goals:
                    draw_prob += prob
                else:
                    away_win_prob += prob

        # Return as probabilities (0-1), not percentages
        result = {
            "home_win": round(home_win_prob, 4),
            "draw": round(draw_prob, 4),
            "away_win": round(away_win_prob, 4)
        }

        logger.debug(f"Match probabilities: {result}")

        return result

    @staticmethod
    def calculate_over_under_probabilities(
        expected_home_goals: float,
        expected_away_goals: float,
        threshold: float = 2.5
    ) -> Dict[str, float]:
        """
        Calculate over/under goal probabilities

        Args:
            expected_home_goals: Expected home team goals
            expected_away_goals: Expected away team goals
            threshold: Goal threshold (e.g., 2.5)

        Returns:
            Dictionary with over and under probabilities
        """
        total_expected_goals = expected_home_goals + expected_away_goals

        # Calculate probability of each total goals outcome
        over_prob = 0.0

        for goals in range(0, 20):  # Check up to 20 total goals
            prob = poisson.pmf(goals, total_expected_goals)
            if goals > threshold:
                over_prob += prob

        under_prob = 1 - over_prob

        result = {
            f"over_{threshold}": round(over_prob, 4),
            f"under_{threshold}": round(under_prob, 4)
        }

        logger.debug(f"Over/Under {threshold} probabilities: {result}")

        return result

    @staticmethod
    def calculate_btts_probability(
        expected_home_goals: float,
        expected_away_goals: float
    ) -> float:
        """
        Calculate Both Teams To Score (BTTS) probability

        Args:
            expected_home_goals: Expected home team goals
            expected_away_goals: Expected away team goals

        Returns:
            BTTS probability as percentage
        """
        # Probability that home team scores 0 goals
        home_no_score = poisson.pmf(0, expected_home_goals)

        # Probability that away team scores 0 goals
        away_no_score = poisson.pmf(0, expected_away_goals)

        # BTTS probability = 1 - (either team doesn't score)
        btts_prob = 1 - (home_no_score + away_no_score - home_no_score * away_no_score)

        result = round(btts_prob, 4)

        logger.debug(f"BTTS probability: {result}")

        return result
