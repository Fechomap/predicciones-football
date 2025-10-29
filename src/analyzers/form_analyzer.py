"""Team form analyzer"""
from typing import List, Dict
from datetime import datetime

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class FormAnalyzer:
    """
    Analyzes team form based on recent matches

    Statistical analysis (NOT AI/ML) of recent performance
    """

    @staticmethod
    def calculate_form_score(recent_matches: List[Dict], is_home: bool = True) -> Dict:
        """
        Calculate form score from recent matches

        Args:
            recent_matches: List of recent match results
            is_home: Whether analyzing home team

        Returns:
            Dictionary with form analysis
        """
        if not recent_matches:
            return {
                "score": 0,
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

        for match in recent_matches[-5:]:  # Last 5 matches
            # Determine if team was home or away
            teams = match.get("teams", {})
            goals = match.get("goals", {})

            home_goals = goals.get("home", 0)
            away_goals = goals.get("away", 0)

            if is_home:
                scored = home_goals
                conceded = away_goals
            else:
                scored = away_goals
                conceded = home_goals

            goals_scored += scored
            goals_conceded += conceded

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
        max_points = len(recent_matches[-5:]) * 3
        form_score = round((points / max_points) * 100, 2) if max_points > 0 else 0

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

        logger.debug(f"Form analysis: {result}")

        return result

    @staticmethod
    def compare_forms(home_form: Dict, away_form: Dict) -> Dict:
        """
        Compare two teams' forms

        Args:
            home_form: Home team form data
            away_form: Away team form data

        Returns:
            Comparison analysis
        """
        home_score = home_form.get("score", 0)
        away_score = away_form.get("score", 0)

        score_diff = home_score - away_score

        # Determine advantage
        if score_diff > 20:
            advantage = "strong_home"
        elif score_diff > 10:
            advantage = "moderate_home"
        elif score_diff < -20:
            advantage = "strong_away"
        elif score_diff < -10:
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
    def calculate_momentum(recent_matches: List[Dict], is_home: bool = True) -> float:
        """
        Calculate team momentum (improving or declining form)

        Args:
            recent_matches: List of recent matches (chronological)
            is_home: Whether analyzing home team

        Returns:
            Momentum score (-100 to +100, positive = improving)
        """
        if len(recent_matches) < 3:
            return 0.0

        # Take last 6 matches and split into two halves
        last_6 = recent_matches[-6:]
        first_half = last_6[:3]
        second_half = last_6[3:]

        # Calculate form score for each half
        first_half_form = FormAnalyzer.calculate_form_score(first_half, is_home)
        second_half_form = FormAnalyzer.calculate_form_score(second_half, is_home)

        # Momentum is the difference
        momentum = second_half_form["score"] - first_half_form["score"]

        logger.debug(f"Momentum calculated: {momentum}")

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
