"""Enhanced analyzer combining API-Football and FootyStats data"""
from typing import Dict, Optional, List
from ..api.footystats_client import FootyStatsClient
from ..services.team_mapping_service import TeamMappingService
from ..database import db_manager
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class EnhancedAnalyzer:
    """
    Enhanced analyzer that combines:
    - Poisson predictions (API-Football)
    - FootyStats detailed metrics
    - Form analysis
    - Intelligent team ID mapping
    """

    def __init__(self, footystats_client: FootyStatsClient, team_mapping_service: TeamMappingService):
        """
        Initialize enhanced analyzer

        Args:
            footystats_client: FootyStats API client
            team_mapping_service: Service for mapping team IDs between APIs
        """
        self.footystats_client = footystats_client
        self.team_mapping_service = team_mapping_service

    def analyze_match_quality(
        self,
        home_team_id: int,
        away_team_id: int,
        home_team_name: str,
        away_team_name: str,
        league_id: int = None,
        num_recent_matches: int = 5
    ) -> Optional[Dict[str, any]]:
        """
        Analyze match quality using FootyStats data

        Args:
            home_team_id: Home team API-Football ID
            away_team_id: Away team API-Football ID
            home_team_name: Home team name
            away_team_name: Away team name
            league_id: League ID from API-Football (for precise search)
            num_recent_matches: Number of recent matches to analyze

        Returns:
            Dictionary with quality metrics or None if data unavailable
        """
        try:
            # Step 1: Map API-Football IDs to FootyStats IDs (WITH league context)
            home_footystats_id = self.team_mapping_service.get_footystats_id(
                api_football_id=home_team_id,
                team_name=home_team_name,
                league_id=league_id  # CRITICAL: Pass league for precise search
            )
            away_footystats_id = self.team_mapping_service.get_footystats_id(
                api_football_id=away_team_id,
                team_name=away_team_name,
                league_id=league_id  # CRITICAL: Pass league for precise search
            )

            # If either team not found, return None (no data available)
            if not home_footystats_id or not away_footystats_id:
                logger.warning(
                    f"FootyStats IDs not found - Home: {home_team_name} ({home_footystats_id}), "
                    f"Away: {away_team_name} ({away_footystats_id})"
                )
                return None

            logger.info(
                f"FootyStats mapping - {home_team_name}: {home_footystats_id}, "
                f"{away_team_name}: {away_footystats_id}"
            )

            # Step 2: Get FootyStats league ID for match data
            footystats_league_id = None
            if league_id:
                from ..database import LeagueIDMapping
                with db_manager.get_session() as session:
                    league_mapping = session.query(LeagueIDMapping).filter_by(
                        api_football_id=league_id
                    ).first()
                    if league_mapping:
                        footystats_league_id = league_mapping.footystats_id

            # Step 3: Get team statistics from /team endpoint
            home_stats_data = self.footystats_client.get_team_stats(home_footystats_id)
            away_stats_data = self.footystats_client.get_team_stats(away_footystats_id)

            # If no stats found, return None
            if not home_stats_data or not away_stats_data:
                logger.warning(f"No FootyStats team data for {home_team_name} vs {away_team_name}")
                return None

            # Extract base statistics from team data
            home_stats_raw = home_stats_data.get('stats', {})
            away_stats_raw = away_stats_data.get('stats', {})

            # Step 4: Get recent matches for corners/shots data (if league available)
            home_matches = []
            away_matches = []

            if footystats_league_id:
                logger.info(f"Fetching recent matches for detailed stats (league: {footystats_league_id})")
                home_matches = self.footystats_client.get_team_recent_matches(
                    home_footystats_id,
                    footystats_league_id,
                    limit=num_recent_matches
                )
                away_matches = self.footystats_client.get_team_recent_matches(
                    away_footystats_id,
                    footystats_league_id,
                    limit=num_recent_matches
                )

            # Step 5: Convert FootyStats data to our format
            home_stats = self._extract_team_metrics(home_stats_raw, home_stats_data, home_matches, home_footystats_id)
            away_stats = self._extract_team_metrics(away_stats_raw, away_stats_data, away_matches, away_footystats_id)

            # Calculate quality score (0-100)
            quality_score = self._calculate_quality_score(home_stats, away_stats)

            return {
                'quality_score': quality_score,
                'home_stats': home_stats,
                'away_stats': away_stats,
                'btts_probability': self._calculate_btts_probability(home_stats, away_stats),
                'over_25_probability': self._calculate_over_25_probability(home_stats, away_stats),
                'match_intensity': self._calculate_match_intensity(home_stats, away_stats)
            }

        except Exception as e:
            logger.error(f"Failed to analyze match quality: {e}")
            # Return None to indicate no data available (not an error with defaults)
            return None

    def _calculate_quality_score(
        self,
        home_stats: Dict,
        away_stats: Dict
    ) -> float:
        """
        Calculate overall match quality score based on FootyStats data

        Args:
            home_stats: Home team statistics
            away_stats: Away team statistics

        Returns:
            Quality score (0-100)
        """
        # Factors that indicate high-quality match
        home_goals_avg = home_stats.get('avg_goals_scored', 0)
        away_goals_avg = away_stats.get('avg_goals_scored', 0)
        home_ppg = home_stats.get('ppg', 0)  # Points per game
        away_ppg = away_stats.get('ppg', 0)

        # Higher goals average = more attacking quality (max 3 goals avg)
        goals_score = min((home_goals_avg + away_goals_avg) / 3.0 * 100, 100)

        # Higher PPG = better team quality (max 2.5 ppg = good team)
        ppg_score = min((home_ppg + away_ppg) / 5.0 * 100, 100)

        # BTTS and Over 2.5 indicate exciting matches
        btts_avg = (home_stats.get('btts_percentage', 0) + away_stats.get('btts_percentage', 0)) / 2
        over_25_avg = (home_stats.get('over_25_percentage', 0) + away_stats.get('over_25_percentage', 0)) / 2

        excitement_score = (btts_avg + over_25_avg) / 2

        # Weighted average
        quality = (
            goals_score * 0.35 +
            ppg_score * 0.30 +
            excitement_score * 0.35
        )

        return round(quality, 2)

    def _calculate_btts_probability(
        self,
        home_stats: Dict,
        away_stats: Dict
    ) -> float:
        """
        Calculate Both Teams To Score probability

        Args:
            home_stats: Home team statistics
            away_stats: Away team statistics

        Returns:
            BTTS probability (0-1)
        """
        home_btts_pct = home_stats.get('btts_percentage', 50) / 100
        away_btts_pct = away_stats.get('btts_percentage', 50) / 100

        # Average of both teams' BTTS percentages
        btts_prob = (home_btts_pct + away_btts_pct) / 2

        return round(btts_prob, 3)

    def _calculate_over_25_probability(
        self,
        home_stats: Dict,
        away_stats: Dict
    ) -> float:
        """
        Calculate Over 2.5 Goals probability

        Args:
            home_stats: Home team statistics
            away_stats: Away team statistics

        Returns:
            Over 2.5 probability (0-1)
        """
        home_over_pct = home_stats.get('over_25_percentage', 50) / 100
        away_over_pct = away_stats.get('over_25_percentage', 50) / 100

        # Consider both teams' tendencies
        avg_goals = (
            home_stats.get('avg_goals_scored', 0) +
            away_stats.get('avg_goals_scored', 0)
        )

        # Combine historical percentage with expected goals
        historical_prob = (home_over_pct + away_over_pct) / 2
        goals_prob = min(avg_goals / 3.0, 1.0)  # 3+ goals = high probability

        over_25_prob = (historical_prob * 0.6 + goals_prob * 0.4)

        return round(over_25_prob, 3)

    def _calculate_match_intensity(
        self,
        home_stats: Dict,
        away_stats: Dict
    ) -> str:
        """
        Calculate expected match intensity based on goals and attacking stats

        Args:
            home_stats: Home team statistics
            away_stats: Away team statistics

        Returns:
            Intensity level: 'low', 'medium', 'high'
        """
        # Use goals scored as proxy for intensity (since shots not available)
        avg_goals = (
            home_stats.get('avg_goals_scored', 0) +
            away_stats.get('avg_goals_scored', 0)
        )

        # Also consider BTTS percentage (both teams attacking)
        btts_avg = (
            home_stats.get('btts_percentage', 0) +
            away_stats.get('btts_percentage', 0)
        ) / 2

        # Combine factors
        intensity_score = (avg_goals * 20) + (btts_avg * 0.3)

        if intensity_score >= 50:
            return 'high'
        elif intensity_score >= 25:
            return 'medium'
        else:
            return 'low'

    def _extract_team_metrics(
        self,
        stats_raw: Dict,
        team_data: Dict,
        recent_matches: List[Dict],
        team_id: int
    ) -> Dict[str, float]:
        """
        Extract and normalize metrics from FootyStats team data

        Args:
            stats_raw: Raw stats from API
            team_data: Full team data object
            recent_matches: Recent match data for corners/shots
            team_id: FootyStats team ID

        Returns:
            Normalized metrics dictionary
        """
        matches_played = stats_raw.get('seasonMatchesPlayed_overall', 1) or 1

        # Calculate corners/shots from recent matches if available
        avg_corners = 0
        avg_shots = 0
        avg_shots_on_target = 0
        avg_possession = 0

        if recent_matches:
            match_averages = self.footystats_client.calculate_team_averages(recent_matches, team_id)
            avg_corners = match_averages.get('avg_corners', 0)
            avg_shots = match_averages.get('avg_shots', 0)
            avg_shots_on_target = match_averages.get('avg_shots_on_target', 0)
            avg_possession = match_averages.get('avg_possession', 0)

        return {
            'avg_goals_scored': stats_raw.get('seasonScoredAVG_overall', 0),
            'avg_goals_conceded': stats_raw.get('seasonConcededAVG_overall', 0),
            'avg_corners': avg_corners,
            'avg_shots': avg_shots,
            'avg_shots_on_target': avg_shots_on_target,
            'avg_possession': avg_possession,
            'btts_percentage': stats_raw.get('seasonBTTSPercentage_overall', 0),
            'over_25_percentage': stats_raw.get('seasonOver25Percentage_overall', 0),
            'clean_sheet_percentage': stats_raw.get('seasonCSPercentage_overall', 0),
            'matches_played': matches_played,
            'wins': stats_raw.get('seasonWinsNum_overall', 0),
            'draws': stats_raw.get('seasonDrawsNum_overall', 0),
            'losses': stats_raw.get('seasonLossesNum_overall', 0),
            'ppg': stats_raw.get('seasonPPG_overall', 0),
        }

    def enhance_prediction(
        self,
        base_probabilities: Dict[str, float],
        home_team_id: int,
        away_team_id: int
    ) -> Dict[str, float]:
        """
        Enhance Poisson-based predictions with FootyStats data

        Args:
            base_probabilities: Base probabilities from Poisson
            home_team_id: Home team FootyStats ID
            away_team_id: Away team FootyStats ID

        Returns:
            Enhanced probabilities
        """
        try:
            quality_analysis = self.analyze_match_quality(
                home_team_id,
                away_team_id
            )

            # Adjust base probabilities based on FootyStats insights
            enhanced = base_probabilities.copy()

            # If quality score is high, increase confidence in predictions
            confidence_multiplier = quality_analysis['quality_score'] / 100

            logger.debug(
                f"Enhanced prediction - Quality: {quality_analysis['quality_score']}, "
                f"BTTS: {quality_analysis['btts_probability']}, "
                f"Over 2.5: {quality_analysis['over_25_probability']}"
            )

            return {
                **enhanced,
                'confidence_multiplier': confidence_multiplier,
                'footystats_quality': quality_analysis
            }

        except Exception as e:
            logger.error(f"Failed to enhance prediction: {e}")
            return base_probabilities
