"""Value bet detection"""
from typing import Dict, Optional

from ..utils.config import Config
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ValueDetector:
    """
    Detects value betting opportunities

    Pure statistical analysis - compares calculated probabilities
    with bookmaker odds to find value
    """

    @staticmethod
    def calculate_implied_probability(odds: float) -> float:
        """
        Calculate implied probability from decimal odds

        Args:
            odds: Decimal odds (e.g., 2.50)

        Returns:
            Implied probability (0-1, NOT percentage)
        """
        # Validate odds before calculation
        if odds <= 0:
            logger.error(f"Invalid odds: {odds}, odds must be positive")
            raise ValueError(f"Odds must be positive, got {odds}")

        if odds <= 1.0:
            logger.warning(f"Unusual odds: {odds}, capping probability at 1.0")
            return 1.0

        implied_prob = 1 / odds
        return round(implied_prob, 4)

    @staticmethod
    def calculate_edge(calculated_probability: float, bookmaker_odds: float) -> float:
        """
        Calculate betting edge (value)

        Edge = (Calculated Probability × Odds) - 1

        Args:
            calculated_probability: Our calculated probability (0-1)
            bookmaker_odds: Bookmaker decimal odds

        Returns:
            Edge as decimal (0-1, NOT percentage)
        """
        edge = (calculated_probability * bookmaker_odds) - 1
        return round(edge, 4)

    @staticmethod
    def calculate_expected_value(
        calculated_probability: float,
        bookmaker_odds: float,
        stake: float = 100
    ) -> float:
        """
        Calculate expected value of bet

        EV = (Probability of Win × Profit) - (Probability of Loss × Stake)

        Args:
            calculated_probability: Our calculated probability (0-1)
            bookmaker_odds: Bookmaker decimal odds
            stake: Stake amount

        Returns:
            Expected value
        """
        prob_win = calculated_probability
        prob_loss = 1 - prob_win

        profit_if_win = (bookmaker_odds - 1) * stake
        loss_if_loss = stake

        ev = (prob_win * profit_if_win) - (prob_loss * loss_if_loss)

        return round(ev, 2)

    @staticmethod
    def detect_value_bet(
        calculated_probability: float,
        bookmaker_odds: float,
        minimum_edge: Optional[float] = None
    ) -> Dict:
        """
        Detect if there's a value betting opportunity

        Args:
            calculated_probability: Our calculated probability (0-1, NOT percentage)
            bookmaker_odds: Bookmaker decimal odds
            minimum_edge: Minimum edge required (0-1, default from config)

        Returns:
            Dictionary with value bet analysis
        """
        if minimum_edge is None:
            minimum_edge = Config.MINIMUM_EDGE  # Already 0-1 from config (e.g., 0.05)

        implied_prob = ValueDetector.calculate_implied_probability(bookmaker_odds)
        edge = ValueDetector.calculate_edge(calculated_probability, bookmaker_odds)
        expected_value = ValueDetector.calculate_expected_value(
            calculated_probability,
            bookmaker_odds
        )

        is_value = edge >= minimum_edge

        result = {
            "is_value_bet": is_value,
            "calculated_probability": calculated_probability,
            "implied_probability": implied_prob,
            "bookmaker_odds": bookmaker_odds,
            "edge": edge,
            "expected_value": expected_value,
            "probability_difference": round(calculated_probability - implied_prob, 4)
        }

        if is_value:
            logger.info(
                f"VALUE BET DETECTED! Edge: {edge*100:.1f}%, "
                f"Calc Prob: {calculated_probability*100:.1f}%, "
                f"Implied Prob: {implied_prob*100:.1f}%"
            )
        else:
            logger.debug(f"No value bet. Edge: {edge*100:.1f}% (minimum: {minimum_edge*100:.1f}%)")

        return result

    @staticmethod
    def calculate_kelly_stake(
        calculated_probability: float,
        bookmaker_odds: float,
        bankroll: float = 1000,
        kelly_fraction: float = 0.25,  # Use fractional Kelly for safety
        max_stake_pct: float = 0.05  # Max 5% of bankroll
    ) -> float:
        """
        Calculate optimal stake using Kelly Criterion

        Kelly % = (bp - q) / b
        where:
            b = decimal odds - 1
            p = probability of winning
            q = probability of losing (1 - p)

        Args:
            calculated_probability: Our calculated probability (0-1)
            bookmaker_odds: Bookmaker decimal odds
            bankroll: Total bankroll
            kelly_fraction: Fraction of Kelly to use (configurable, default 0.25)
            max_stake_pct: Maximum stake as % of bankroll (configurable, default 0.05)

        Returns:
            Suggested stake amount
        """
        p = calculated_probability
        q = 1 - p
        b = bookmaker_odds - 1

        # Handle edge case: odds of 1.0 or less (no profit)
        if b <= 0:
            logger.warning(f"Invalid odds for Kelly Criterion: {bookmaker_odds} (b={b})")
            return 0.0

        # Full Kelly percentage
        kelly_pct = (b * p - q) / b

        # Apply fractional Kelly for safety
        kelly_pct = kelly_pct * kelly_fraction

        # Don't bet if Kelly is negative or zero
        if kelly_pct <= 0:
            return 0.0

        # Calculate stake (with configurable max)
        stake = min(kelly_pct * bankroll, bankroll * max_stake_pct)

        return round(stake, 2)

    @staticmethod
    def get_confidence_rating(
        edge: float,
        sample_size: int = None,
        thresholds: Dict[str, float] = None,
        footystats_quality: float = 50.0
    ) -> int:
        """
        Get confidence rating (1-5 stars)

        Args:
            edge: Betting edge (0-1, NOT percentage)
            sample_size: Number of data points used
            thresholds: Custom thresholds dict (configurable)
            footystats_quality: Quality score from FootyStats (0-100)

        Returns:
            Confidence rating (1-5)
        """
        # Use config value if not provided
        if sample_size is None:
            sample_size = Config.FORM_MIN_SAMPLE_SIZE

        # Default thresholds (configurable)
        if thresholds is None:
            thresholds = {
                5: 0.15,  # >= 15% edge
                4: 0.10,  # >= 10% edge
                3: 0.07,  # >= 7% edge
                2: 0.05,  # >= 5% edge
            }

        # Base confidence on edge
        if edge >= thresholds[5]:
            base_confidence = 5
        elif edge >= thresholds[4]:
            base_confidence = 4
        elif edge >= thresholds[3]:
            base_confidence = 3
        elif edge >= thresholds[2]:
            base_confidence = 2
        else:
            base_confidence = 1

        # Adjust for sample size
        if sample_size < 3:
            base_confidence = max(1, base_confidence - 1)

        # ENHANCED: Boost confidence if FootyStats quality is high
        if footystats_quality >= 80 and base_confidence < 5:
            base_confidence = min(5, base_confidence + 1)
            logger.debug(f"Confidence boosted due to high FootyStats quality: {footystats_quality}")
        elif footystats_quality < 30 and base_confidence > 1:
            base_confidence = max(1, base_confidence - 1)
            logger.debug(f"Confidence reduced due to low FootyStats quality: {footystats_quality}")

        return base_confidence

    @staticmethod
    def remove_bookmaker_margin(odds_list: list) -> list:
        """
        Remove bookmaker margin (overround) from odds

        CORRECTED FORMULA:
        Fair probability = Individual implied prob / Total implied prob
        Fair odds = 1 / Fair probability

        Args:
            odds_list: List of decimal odds for all outcomes

        Returns:
            List of fair odds without margin
        """
        # Validate input
        if not odds_list or any(o <= 0 for o in odds_list):
            logger.error(f"Invalid odds list for margin removal: {odds_list}")
            return odds_list  # Return original if invalid

        # Calculate total implied probability (overround)
        # e.g., if odds are [2.0, 3.5, 4.0], total = 0.5 + 0.286 + 0.25 = 1.036
        total_implied_prob = sum(1 / odds for odds in odds_list)

        # Calculate fair odds by normalizing
        # Fair probability = (1 / odds) / total_implied_probability
        # Fair odds = 1 / Fair probability = total_implied_prob / (1 / odds)
        # Which simplifies to: total_implied_prob * odds
        fair_odds = [
            round(total_implied_prob / (1 / odds), 2)
            for odds in odds_list
        ]

        return fair_odds
