"""Main bot service orchestrating all components"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from ..api import APIFootballClient
from ..database import (
    db_manager, Fixture, Prediction, ValueBet,
    NotificationLog, TeamStatistics
)
from ..analyzers import PoissonAnalyzer, FormAnalyzer, ValueDetector
from ..notifications import TelegramNotifier
from ..utils.config import Config
from ..utils.logger import setup_logger
from .data_collector import DataCollector
from .fixtures_service import FixturesService

logger = setup_logger(__name__)


class BotService:
    """Main bot service"""

    def __init__(self):
        """Initialize bot service"""
        self.api_client = APIFootballClient()
        self.data_collector = DataCollector()
        self.fixtures_service = FixturesService(self.data_collector)
        self.telegram = TelegramNotifier()

        self.poisson_analyzer = PoissonAnalyzer()
        self.form_analyzer = FormAnalyzer()
        self.value_detector = ValueDetector()

        self.alerts_sent_today = 0

        logger.info("Bot service initialized")

    async def check_fixtures(self):
        """Main task: Check upcoming fixtures and analyze"""
        try:
            logger.info("Starting fixture check cycle...")

            # Collect upcoming fixtures
            fixtures = self.data_collector.collect_upcoming_fixtures(
                hours_ahead=Config.ALERT_TIME_MINUTES // 60 + 24
            )

            # Filter fixtures that need alerts
            fixtures_to_analyze = self._filter_fixtures_for_alert(fixtures)

            logger.info(f"Found {len(fixtures_to_analyze)} fixtures to analyze")

            # Analyze each fixture
            for fixture in fixtures_to_analyze:
                try:
                    await self._analyze_and_notify(fixture)
                except Exception as e:
                    logger.error(f"Error analyzing fixture: {e}")
                    continue

            logger.info("Fixture check cycle completed")

        except Exception as e:
            logger.error(f"Error in check_fixtures: {e}")
            await self.telegram.send_error_message(str(e))

    def _filter_fixtures_for_alert(self, fixtures: List[Dict]) -> List[Dict]:
        """
        Filter fixtures that are within alert window

        Args:
            fixtures: List of all fixtures

        Returns:
            Fixtures that should trigger alerts
        """
        # Use timezone-aware UTC datetime for consistency with API
        now = datetime.now(timezone.utc)
        alert_window_start = now + timedelta(minutes=Config.ALERT_TIME_MINUTES - 10)
        alert_window_end = now + timedelta(minutes=Config.ALERT_TIME_MINUTES + 10)

        filtered = []

        for fixture in fixtures:
            fixture_info = fixture.get("fixture", {})
            fixture_id = fixture_info.get("id")
            kickoff_timestamp = fixture_info.get("timestamp", 0)
            # Convert timestamp to timezone-aware datetime
            kickoff_time = datetime.fromtimestamp(kickoff_timestamp, tz=timezone.utc)

            # Check if in alert window
            if alert_window_start <= kickoff_time <= alert_window_end:
                # Check if already notified
                with db_manager.get_session() as session:
                    existing_notification = session.query(NotificationLog).join(
                        ValueBet
                    ).filter(
                        ValueBet.fixture_id == fixture_id,
                        NotificationLog.status == "sent"
                    ).first()

                    if not existing_notification:
                        filtered.append(fixture)

        return filtered

    async def _analyze_and_notify(self, fixture: Dict):
        """
        Analyze fixture and send notification if value bet found

        Args:
            fixture: Fixture data
        """
        fixture_info = fixture.get("fixture", {})
        fixture_id = fixture_info.get("id")
        teams = fixture.get("teams", {})

        logger.info(
            f"Analyzing: {teams.get('home', {}).get('name')} vs "
            f"{teams.get('away', {}).get('name')}"
        )

        # Collect odds
        odds_data = self.data_collector.collect_fixture_odds(fixture_id)

        if not odds_data:
            logger.warning(f"No odds data for fixture {fixture_id}")
            return

        # Get team statistics (mock for now - needs implementation)
        home_team_id = teams.get("home", {}).get("id")
        away_team_id = teams.get("away", {}).get("id")

        # Get league ID
        league_id = fixture.get("league", {}).get("id")

        # For MVP, use simplified stats
        home_stats = self._get_team_stats(home_team_id, league_id, is_home=True)
        away_stats = self._get_team_stats(away_team_id, league_id, is_home=False)

        # Calculate expected goals with real league average
        expected_home, expected_away = self.poisson_analyzer.calculate_expected_goals(
            home_stats,
            away_stats,
            league_id=league_id
        )

        # Calculate match probabilities
        probabilities = self.poisson_analyzer.calculate_match_probabilities(
            expected_home,
            expected_away
        )

        # Get REAL form analysis from recent matches
        logger.info(f"Calculating real form for teams {home_team_id} vs {away_team_id}")

        # Get recent matches for form analysis
        # For now, use a simplified approach with available data
        # TODO: In future, fetch actual recent matches from API
        try:
            # Try to get recent fixtures for each team
            # Using get_fixtures with team parameter would require API modification
            # For MVP, calculate based on season statistics
            home_stats_data = self.api_client.get_team_statistics(
                team_id=home_team_id,
                league_id=league_id,
                season=self._get_current_season(league_id)
            )
            away_stats_data = self.api_client.get_team_statistics(
                team_id=away_team_id,
                league_id=league_id,
                season=self._get_current_season(league_id)
            )

            # Extract form string from API (if available)
            home_form_string = home_stats_data.get("form", "N/A") if home_stats_data else "N/A"
            away_form_string = away_stats_data.get("form", "N/A") if away_stats_data else "N/A"

            # Calculate points from form string
            def calculate_points_from_form(form_string: str) -> int:
                """Calculate points from form string (W=3, D=1, L=0)"""
                if not form_string or form_string == "N/A":
                    return 0
                points = 0
                for result in form_string[-5:]:  # Last 5 matches
                    if result == 'W':
                        points += 3
                    elif result == 'D':
                        points += 1
                return points

            home_form = {
                "form_string": home_form_string[-5:] if len(home_form_string) >= 5 else home_form_string,
                "points": calculate_points_from_form(home_form_string)
            }
            away_form = {
                "form_string": away_form_string[-5:] if len(away_form_string) >= 5 else away_form_string,
                "points": calculate_points_from_form(away_form_string)
            }

            logger.info(f"Home form: {home_form}, Away form: {away_form}")

        except Exception as e:
            logger.error(f"Error getting real form data: {e}, using defaults")
            # Fallback to neutral values if API fails
            home_form = {"form_string": "N/A", "points": 0}
            away_form = {"form_string": "N/A", "points": 0}

        # Extract best odds for 1X2
        best_odds = self._extract_best_odds(odds_data)

        if not best_odds:
            logger.warning(f"No valid odds for fixture {fixture_id}")
            return

        # Check each outcome for value
        outcomes = [
            ("Home", probabilities["home_win"], best_odds.get("Home")),
            ("Draw", probabilities["draw"], best_odds.get("Draw")),
            ("Away", probabilities["away_win"], best_odds.get("Away"))
        ]

        for outcome, probability, odds in outcomes:
            if not odds:
                continue

            value_result = self.value_detector.detect_value_bet(
                calculated_probability=probability,
                bookmaker_odds=odds
            )

            if value_result["is_value_bet"]:
                # Value bet found!
                logger.info(f"VALUE BET FOUND: {outcome} - Edge {value_result['edge']}%")

                # Check daily limit
                if self.alerts_sent_today >= Config.MAX_ALERTS_PER_DAY:
                    logger.warning("Daily alert limit reached")
                    return

                # Save to database
                self._save_analysis(
                    fixture_id,
                    probabilities,
                    expected_home,
                    expected_away,
                    outcome,
                    value_result,
                    odds
                )

                # Send notification
                analysis = {
                    "home_probability": probabilities["home_win"],
                    "draw_probability": probabilities["draw"],
                    "away_probability": probabilities["away_win"],
                    "expected_home_goals": expected_home,
                    "expected_away_goals": expected_away,
                    "home_form": home_form,
                    "away_form": away_form,
                    "confidence": self.value_detector.get_confidence_rating(
                        value_result["edge"]
                    )
                }

                # Calculate optimal stake using Kelly Criterion
                kelly_stake = self.value_detector.calculate_kelly_stake(
                    calculated_probability=probability,
                    bookmaker_odds=odds,
                    bankroll=Config.BANKROLL,
                    kelly_fraction=Config.KELLY_FRACTION,
                    max_stake_pct=Config.MAX_STAKE_PERCENTAGE
                )

                # Convert to percentage for display
                suggested_stake_pct = kelly_stake / Config.BANKROLL * 100

                value_bet_data = {
                    "outcome": outcome,
                    "calculated_probability": probability,
                    "bookmaker_odds": odds,
                    "edge": value_result["edge"],
                    "implied_probability": value_result["implied_probability"],
                    "expected_value": value_result["expected_value"],
                    "suggested_stake": round(suggested_stake_pct, 2)  # Kelly Criterion %
                }

                message_id = await self.telegram.send_value_bet_alert(
                    fixture=fixture,
                    analysis=analysis,
                    value_bet=value_bet_data
                )

                if message_id:
                    self.alerts_sent_today += 1

                # Only send one alert per fixture
                break

    def _get_team_stats(self, team_id: int, league_id: int, is_home: bool) -> Dict:
        """
        Get team statistics from API

        Args:
            team_id: Team ID
            league_id: League ID
            is_home: Whether team is home

        Returns:
            Team stats dictionary
        """
        try:
            # Determine current season using timezone-aware datetime
            current_time = datetime.now(timezone.utc)
            current_month = current_time.month
            current_year = current_time.year
            current_season = current_year if current_month >= 8 else current_year - 1

            # Get stats from API
            stats_data = self.api_client.get_team_statistics(
                team_id=team_id,
                league_id=league_id,
                season=current_season
            )

            if not stats_data:
                logger.warning(f"No statistics found for team {team_id}, using defaults")
                return self._get_default_stats(is_home)

            # Extract relevant stats
            fixtures = stats_data.get("fixtures", {})
            goals_for = stats_data.get("goals", {}).get("for", {}).get("total", {})
            goals_against = stats_data.get("goals", {}).get("against", {}).get("total", {})

            if is_home:
                return {
                    "home_matches": fixtures.get("played", {}).get("home", 1) or 1,
                    "home_goals_scored": goals_for.get("home", 0) or 0,
                    "home_goals_conceded": goals_against.get("home", 0) or 0
                }
            else:
                return {
                    "away_matches": fixtures.get("played", {}).get("away", 1) or 1,
                    "away_goals_scored": goals_for.get("away", 0) or 0,
                    "away_goals_conceded": goals_against.get("away", 0) or 0
                }

        except Exception as e:
            logger.error(f"Error getting team stats for {team_id}: {e}")
            return self._get_default_stats(is_home)

    def _get_team_stats_with_form(self, team_id: int, league_id: int, is_home: bool) -> Dict:
        """
        Get team statistics AND form from API

        Args:
            team_id: Team ID
            league_id: League ID
            is_home: Whether team is home

        Returns:
            Dictionary with stats and form
        """
        try:
            # Determine current season using timezone-aware datetime
            current_time = datetime.now(timezone.utc)
            current_month = current_time.month
            current_year = current_time.year
            current_season = current_year if current_month >= 8 else current_year - 1

            # Get team statistics from API
            stats_data = self.api_client.get_team_statistics(
                team_id=team_id,
                league_id=league_id,
                season=current_season
            )

            logger.debug(f"Stats data for team {team_id}: {stats_data}")

            if not stats_data or not isinstance(stats_data, dict):
                logger.warning(f"No stats data for team {team_id}")
                return {
                    "stats": self._get_default_stats(is_home),
                    "form": "N/A"
                }

            # The API returns the response directly
            response = stats_data

            # Verify we have the expected data
            if "form" not in response and "fixtures" not in response:
                logger.warning(f"Stats data incomplete for team {team_id}: {list(response.keys())}")
                return {
                    "stats": self._get_default_stats(is_home),
                    "form": "N/A"
                }

            # Extract form (last 5 matches)
            form_full = response.get("form", "") or ""
            form_last_5 = form_full[-5:] if len(form_full) >= 5 else form_full

            # Extract stats
            fixtures = response.get("fixtures", {})
            goals_for = response.get("goals", {}).get("for", {}).get("total", {})
            goals_against = response.get("goals", {}).get("against", {}).get("total", {})

            if is_home:
                stats = {
                    "home_matches": fixtures.get("played", {}).get("home", 1) or 1,
                    "home_goals_scored": goals_for.get("home", 0) or 0,
                    "home_goals_conceded": goals_against.get("home", 0) or 0
                }
            else:
                stats = {
                    "away_matches": fixtures.get("played", {}).get("away", 1) or 1,
                    "away_goals_scored": goals_for.get("away", 0) or 0,
                    "away_goals_conceded": goals_against.get("away", 0) or 0
                }

            return {
                "stats": stats,
                "form": form_last_5 if form_last_5 else "N/A"
            }

        except Exception as e:
            logger.error(f"Error getting team stats with form: {e}")
            return {
                "stats": self._get_default_stats(is_home),
                "form": "N/A"
            }

    def _get_default_stats(self, is_home: bool) -> Dict:
        """Fallback stats if API fails"""
        if is_home:
            return {"home_matches": 10, "home_goals_scored": 15, "home_goals_conceded": 10}
        else:
            return {"away_matches": 10, "away_goals_scored": 12, "away_goals_conceded": 12}

    def _get_current_season(self, league_id: int) -> int:
        """
        Get current season year for a league based on calendar type

        Args:
            league_id: League ID

        Returns:
            Season year
        """
        from ..api.api_football import (
            LEAGUES_WITH_SPLIT_SEASONS,
            CALENDAR_YEAR_LEAGUES,
            SOUTHERN_HEMISPHERE_LEAGUES
        )

        current_time = datetime.now(timezone.utc)
        current_month = current_time.month
        current_year = current_time.year

        # Calculate season based on league calendar type
        if league_id in LEAGUES_WITH_SPLIT_SEASONS:
            # Liga MX (Apertura/Clausura): Both use current year
            return current_year

        elif league_id in CALENDAR_YEAR_LEAGUES:
            # Nordic leagues: Season = current year
            return current_year

        elif league_id in SOUTHERN_HEMISPHERE_LEAGUES:
            # Southern hemisphere: Jan-Jul = current year, Aug-Dec = next year
            return current_year if current_month <= 7 else current_year + 1

        else:
            # Default: European format (Aug-May)
            return current_year if current_month >= 8 else current_year - 1

    def _extract_best_odds(self, odds_data: List[Dict]) -> Dict:
        """
        Extract best available odds from odds data

        Args:
            odds_data: Odds data from API

        Returns:
            Dictionary with best odds for each outcome
        """
        best_odds = {}

        for bookmaker_data in odds_data:
            for bet in bookmaker_data.get("bets", []):
                if bet.get("name") == "Match Winner":
                    for value in bet.get("values", []):
                        outcome = value.get("value")
                        odds = float(value.get("odd", 0))

                        # Keep best (highest) odds
                        if outcome not in best_odds or odds > best_odds[outcome]:
                            best_odds[outcome] = odds

        return best_odds

    def _save_analysis(
        self,
        fixture_id: int,
        probabilities: Dict,
        expected_home: float,
        expected_away: float,
        outcome: str,
        value_result: Dict,
        odds: float
    ):
        """Save analysis to database"""
        with db_manager.get_session() as session:
            # Create prediction
            prediction = Prediction(
                fixture_id=fixture_id,
                home_probability=probabilities["home_win"],
                draw_probability=probabilities["draw"],
                away_probability=probabilities["away_win"],
                expected_goals_home=expected_home,
                expected_goals_away=expected_away,
                confidence_score=self.value_detector.get_confidence_rating(
                    value_result["edge"]
                )
            )
            session.add(prediction)
            session.flush()

            # Create value bet
            value_bet = ValueBet(
                fixture_id=fixture_id,
                prediction_id=prediction.id,
                recommended_outcome=outcome,
                calculated_probability=value_result["calculated_probability"],
                bookmaker_odds=odds,
                edge=value_result["edge"],
                expected_value=value_result["expected_value"],
                suggested_stake=3.0
            )
            session.add(value_bet)
            session.flush()

            # Create notification log
            notification = NotificationLog(
                value_bet_id=value_bet.id,
                status="sent"
            )
            session.add(notification)

            session.commit()

    async def send_daily_summary(self):
        """Send daily summary"""
        logger.info("Sending daily summary...")

        await self.telegram.send_daily_summary(
            opportunities_count=self.alerts_sent_today
        )

        # Reset counter
        self.alerts_sent_today = 0

    def analyze_fixture(self, fixture: Dict) -> Dict:
        """
        Analyze a single fixture (public method for /analizar command)

        Args:
            fixture: Fixture data from API

        Returns:
            Analysis results dictionary
        """
        try:
            fixture_info = fixture.get("fixture", {})
            fixture_id = fixture_info.get("id")
            teams = fixture.get("teams", {})

            # Get team IDs and league
            home_team_id = teams.get("home", {}).get("id")
            away_team_id = teams.get("away", {}).get("id")
            league_id = fixture.get("league", {}).get("id")

            # Get API predictions (their analysis)
            logger.info(f"Fetching API predictions for fixture {fixture_id}")
            api_predictions_raw = self.api_client.get_predictions(fixture_id)

            # Handle both list and dict responses (for compatibility)
            if isinstance(api_predictions_raw, list) and len(api_predictions_raw) > 0:
                logger.info(f"✅ Got predictions as list, extracting first element")
                api_predictions = api_predictions_raw[0]
            elif isinstance(api_predictions_raw, dict):
                logger.info(f"✅ Got predictions as dict")
                api_predictions = api_predictions_raw
            else:
                logger.warning(f"⚠️ No valid predictions data")
                api_predictions = {}

            # Get REAL team stats from API
            logger.info(f"Fetching real statistics for teams {home_team_id} vs {away_team_id}")
            home_stats_full = self._get_team_stats_with_form(home_team_id, league_id, is_home=True)
            away_stats_full = self._get_team_stats_with_form(away_team_id, league_id, is_home=False)

            # Extract stats for Poisson
            home_stats = home_stats_full["stats"]
            away_stats = away_stats_full["stats"]

            # Calculate expected goals with REAL league average
            expected_home, expected_away = self.poisson_analyzer.calculate_expected_goals(
                home_stats,
                away_stats,
                league_id=league_id  # Pass league ID for correct average
            )

            # Calculate match probabilities
            probabilities = self.poisson_analyzer.calculate_match_probabilities(
                expected_home,
                expected_away
            )

            # Get odds (try to get real odds, fallback to mock)
            odds_data = self.data_collector.collect_fixture_odds(fixture_id)
            best_odds = self._extract_best_odds(odds_data) if odds_data else {}

            # If no real odds, use mock odds for demo
            if not best_odds:
                best_odds = {
                    "Home": 1.85,
                    "Draw": 3.40,
                    "Away": 4.20
                }

            # Check for value bets
            has_value = False
            best_value = None
            best_edge = 0

            outcomes = [
                ("Local (1)", probabilities["home_win"], best_odds.get("Home")),
                ("Empate (X)", probabilities["draw"], best_odds.get("Draw")),
                ("Visitante (2)", probabilities["away_win"], best_odds.get("Away"))
            ]

            for outcome, probability, odds in outcomes:
                if not odds:
                    continue

                value_result = self.value_detector.detect_value_bet(
                    calculated_probability=probability,
                    bookmaker_odds=odds
                )

                if value_result["is_value_bet"] and value_result["edge"] > best_edge:
                    has_value = True
                    best_edge = value_result["edge"]

                    # Calculate optimal stake using Kelly Criterion
                    kelly_stake = self.value_detector.calculate_kelly_stake(
                        calculated_probability=probability,
                        bookmaker_odds=odds,
                        bankroll=Config.BANKROLL,
                        kelly_fraction=Config.KELLY_FRACTION,
                        max_stake_pct=Config.MAX_STAKE_PERCENTAGE
                    )

                    # Convert to decimal (0.03 = 3%)
                    suggested_stake_decimal = kelly_stake / Config.BANKROLL

                    best_value = {
                        "outcome": outcome,
                        "edge": value_result["edge"],
                        "confidence": self.value_detector.get_confidence_rating(value_result["edge"]),
                        "suggested_stake": round(suggested_stake_decimal, 4)  # Kelly Criterion as decimal
                    }

            # Extract API predictions (handle empty or missing data)
            api_pred = {}
            api_percent = {}

            if api_predictions and isinstance(api_predictions, dict):
                api_pred = api_predictions.get("predictions", {})
                api_percent = api_pred.get("percent", {}) if api_pred else {}
                logger.debug(f"API percent data: {api_percent}")

            # Helper function to safely parse percentage values
            def safe_parse_percent(value) -> float:
                """Safely parse percentage values from API"""
                if not value:
                    return 0.0
                try:
                    # Handle both numeric and string types
                    if isinstance(value, (int, float)):
                        return float(value) / 100
                    # Handle string type
                    return float(str(value).rstrip("%")) / 100
                except (ValueError, AttributeError, TypeError) as e:
                    logger.warning(f"Could not parse percentage value: {value}, error: {e}")
                    return 0.0

            # Build analysis result with BOTH predictions
            return {
                "has_value": has_value,
                "our_prediction": {
                    "home": probabilities["home_win"],
                    "draw": probabilities["draw"],
                    "away": probabilities["away_win"]
                },
                "api_prediction": {
                    "home": safe_parse_percent(api_percent.get("home")),
                    "draw": safe_parse_percent(api_percent.get("draw")),
                    "away": safe_parse_percent(api_percent.get("away")),
                    "winner": api_pred.get("winner", {}).get("name") if api_pred else None,
                    "advice": api_pred.get("advice") if api_pred else None
                },
                "statistics": {
                    "expected_goals_home": expected_home,
                    "expected_goals_away": expected_away,
                    "home_form": home_stats_full["form"],
                    "away_form": away_stats_full["form"],
                    "home_matches": home_stats.get("home_matches", 0),
                    "away_matches": away_stats.get("away_matches", 0)
                },
                "h2h": {
                    "last_5": api_predictions.get("h2h", [])[:5] if "h2h" in api_predictions else []
                },
                "value_bet": best_value if has_value else None
            }

        except Exception as e:
            logger.error(f"Error analyzing fixture {fixture_id}: {e}")
            return None

    def sync_leagues(self):
        """Sync leagues to database"""
        logger.info("Syncing leagues...")
        self.data_collector.sync_leagues()
