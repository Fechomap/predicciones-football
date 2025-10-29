"""Team form analyzer"""
from typing import List, Dict, Optional
from datetime import datetime

from ..utils.config import Config
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

# Configurable thresholds for form comparison
FORM_COMPARISON_THRESHOLDS = {
    "strong": 20,      # > 20 points difference = strong advantage
    "moderate": 10,    # > 10 points difference = moderate advantage
}


class FormAnalyzer:
    """
    Analyzes team form based on recent matches

    Statistical analysis (NOT AI/ML) of recent performance
    """

    @staticmethod
    def calculate_form_score(
        recent_matches: List[Dict],
        team_id: int,
        max_matches: int = 5
    ) -> Dict:
        """
        Calculate form score from recent matches

        CORRECTED: Now checks which team we're analyzing in EACH match

        Args:
            recent_matches: List of recent match results
            team_id: ID of the team to analyze
            max_matches: Number of recent matches to consider

        Returns:
            Dictionary with form analysis
        """
        if not recent_matches:
            logger.warning(f"No recent matches data for team {team_id}")
            return {
                "score": None,  # None indicates no data available
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_scored": 0,
                "goals_conceded": 0,
                "form_string": "",
                "points": 0
            }

        wins = 0
        draws = 0
        losses = 0
        goals_scored = 0
        goals_conceded = 0
        form_string = ""
        matches_processed = 0  # Track actually processed matches

        # Take last N matches
        last_matches = recent_matches[-max_matches:]

        for match in last_matches:
            teams = match.get("teams", {})
            goals = match.get("goals", {})

            home_team_id = teams.get("home", {}).get("id")
            away_team_id = teams.get("away", {}).get("id")
            home_goals = goals.get("home", 0)
            away_goals = goals.get("away", 0)

            # CORRECTED: Determine if our team was home or away IN THIS SPECIFIC MATCH
            if team_id == home_team_id:
                # Our team was home in this match
                scored = home_goals
                conceded = away_goals
            elif team_id == away_team_id:
                # Our team was away in this match
                scored = away_goals
                conceded = home_goals
            else:
                # Team not in this match - skip
                logger.warning(f"Team {team_id} not found in match")
                continue

            goals_scored += scored
            goals_conceded += conceded
            matches_processed += 1  # Increment only for successfully processed matches

            # Determine result
            if scored > conceded:
                wins += 1
                form_string += "W"
            elif scored == conceded:
                draws += 1
                form_string += "D"
            else:
                losses += 1
                form_string += "L"

        # Calculate form score (weighted points)
        points = (wins * 3) + (draws * 1)
        # Use actually processed matches count, not input count
        matches_analyzed = matches_processed
        max_points = matches_analyzed * 3

        # Calculate form score or return None if no valid data
        if max_points == 0:
            logger.warning(f"No matches processed for team {team_id}, cannot calculate form score")
            form_score = None  # None indicates no data, distinct from 0 (very poor form)
        else:
            form_score = round((points / max_points) * 100, 2)

        result = {
            "score": form_score,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_scored": goals_scored,
            "goals_conceded": goals_conceded,
            "form_string": form_string,
            "points": points,
            "goal_difference": goals_scored - goals_conceded
        }

        logger.debug(f"Form analysis for team {team_id}: {result}")

        return result

    @staticmethod
    def compare_forms(
        home_form: Dict,
        away_form: Dict,
        thresholds: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        Compare two teams' forms

        CORRECTED: Thresholds now configurable

        Args:
            home_form: Home team form data
            away_form: Away team form data
            thresholds: Custom thresholds (configurable)

        Returns:
            Comparison analysis
        """
        # Use default thresholds if not provided (configurable)
        if thresholds is None:
            thresholds = FORM_COMPARISON_THRESHOLDS

        home_score = home_form.get("score", 0)
        away_score = away_form.get("score", 0)

        score_diff = home_score - away_score

        # Determine advantage using configurable thresholds
        strong_threshold = thresholds.get("strong", 20)
        moderate_threshold = thresholds.get("moderate", 10)

        if score_diff > strong_threshold:
            advantage = "strong_home"
        elif score_diff > moderate_threshold:
            advantage = "moderate_home"
        elif score_diff < -strong_threshold:
            advantage = "strong_away"
        elif score_diff < -moderate_threshold:
            advantage = "moderate_away"
        else:
            advantage = "balanced"

        result = {
            "home_score": home_score,
            "away_score": away_score,
            "score_difference": score_diff,
            "advantage": advantage,
            "home_form_string": home_form.get("form_string", ""),
            "away_form_string": away_form.get("form_string", "")
        }

        logger.debug(f"Form comparison: {result}")

        return result

    @staticmethod
    def calculate_momentum(
        recent_matches: List[Dict],
        team_id: int,
        min_matches: int = None
    ) -> float:
        """
        Calculate team momentum (improving or declining form)

        CORRECTED: Now determines home/away for each match individually

        Args:
            recent_matches: List of recent matches (chronological)
            team_id: ID of team to analyze
            min_matches: Minimum matches needed for momentum calculation

        Returns:
            Momentum score (-100 to +100, positive = improving)
        """
        # Use config value if not provided
        if min_matches is None:
            min_matches = Config.MOMENTUM_MIN_MATCHES

        if len(recent_matches) < min_matches:
            logger.debug(f"Not enough matches for momentum ({len(recent_matches)} < {min_matches})")
            return 0.0

        # Take last N matches and split into two halves
        last_n = recent_matches[-min_matches:]
        mid_point = len(last_n) // 2
        first_half = last_n[:mid_point]
        second_half = last_n[mid_point:]

        # Calculate form score for each half (CORRECTED: using team_id)
        first_half_form = FormAnalyzer.calculate_form_score(first_half, team_id)
        second_half_form = FormAnalyzer.calculate_form_score(second_half, team_id)

        # Momentum is the difference
        momentum = second_half_form["score"] - first_half_form["score"]

        logger.debug(f"Momentum for team {team_id}: {momentum} (improving)" if momentum > 0 else f"Momentum for team {team_id}: {momentum} (declining)")

        return round(momentum, 2)

    @staticmethod
    def get_form_rating(form_score: float) -> str:
        """
        Get textual rating from form score

        Args:
            form_score: Form score (0-100)

        Returns:
            Rating string
        """
        if form_score >= 80:
            return "Excellent"
        elif form_score >= 60:
            return "Good"
        elif form_score >= 40:
            return "Average"
        elif form_score >= 20:
            return "Poor"
        else:
            return "Very Poor"
