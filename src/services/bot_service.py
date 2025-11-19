"""Main bot service orchestrating all components"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from ..api import APIFootballClient
from ..api.footystats_client import FootyStatsClient
from ..database import (
    db_manager, Fixture, Prediction, ValueBet,
    NotificationLog, TeamStatistics
)
from ..analyzers import PoissonAnalyzer, FormAnalyzer, ValueDetector
from ..analyzers.enhanced_analyzer import EnhancedAnalyzer
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
        self.footystats_client = FootyStatsClient()
        self.data_collector = DataCollector()
        self.fixtures_service = FixturesService(self.data_collector)
        self.telegram = TelegramNotifier()

        self.poisson_analyzer = PoissonAnalyzer()
        self.form_analyzer = FormAnalyzer()
        self.value_detector = ValueDetector()

        # Initialize team mapping service and enhanced analyzer
        from .team_mapping_service import TeamMappingService
        self.team_mapping_service = TeamMappingService()  # No longer needs footystats_client
        self.enhanced_analyzer = EnhancedAnalyzer(self.footystats_client, self.team_mapping_service)

        self.alerts_sent_today = 0

        logger.info("Bot service initialized with FootyStats integration")

    async def check_fixtures(self):
        """Main task: Check upcoming fixtures and analyze"""
        try:
            logger.info("Starting fixture check cycle...")

            # Get upcoming fixtures (monitoring cycle: check freshness)
            fixtures = self.fixtures_service.get_upcoming_fixtures(
                hours_ahead=Config.ALERT_TIME_MINUTES // 60 + 24,
                check_freshness=True  # Only monitoring cycle checks data age
                # Refreshes from API if data > 3h old (~8 calls/day)
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
        Filter fixtures that need alerts

        IMPROVED LOGIC (per PM recommendation):
        - Find ALL fixtures starting in <= ALERT_TIME_MINUTES
        - That have NOT been notified yet
        - That have NOT started yet

        This ensures NO fixtures are missed due to narrow time windows.

        Args:
            fixtures: List of all fixtures

        Returns:
            Fixtures that should trigger alerts
        """
        # Use timezone-aware UTC datetime for consistency with API
        now = datetime.now(timezone.utc)
        alert_deadline = now + timedelta(minutes=Config.ALERT_TIME_MINUTES)

        filtered = []

        for fixture in fixtures:
            fixture_info = fixture.get("fixture", {})
            fixture_id = fixture_info.get("id")
            kickoff_timestamp = fixture_info.get("timestamp", 0)
            # Convert timestamp to timezone-aware datetime
            kickoff_time = datetime.fromtimestamp(kickoff_timestamp, tz=timezone.utc)

            # Calculate time until kickoff
            time_until_kickoff = (kickoff_time - now).total_seconds() / 60  # minutes

            # Check if fixture is:
            # 1. Not started yet (kickoff in the future)
            # 2. Starting within alert window (<=ALERT_TIME_MINUTES from now)
            if kickoff_time > now and time_until_kickoff <= Config.ALERT_TIME_MINUTES:
                # Check if already notified
                with db_manager.get_session() as session:
                    existing_notification = session.query(NotificationLog).join(
                        ValueBet
                    ).filter(
                        ValueBet.fixture_id == fixture_id,
                        NotificationLog.status == "sent"
                    ).first()

                    if not existing_notification:
                        logger.debug(
                            f"Fixture {fixture_id} ready for alert "
                            f"(starts in {time_until_kickoff:.1f} min)"
                        )
                        filtered.append(fixture)
                    else:
                        logger.debug(f"Fixture {fixture_id} already notified, skipping")

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

        # Calculate goal ranges probabilities (0-1, 2-3, 4+)
        goal_ranges = self.poisson_analyzer.calculate_goal_ranges_probabilities(
            expected_home,
            expected_away
        )

        # ENHANCED: Get FootyStats quality analysis
        footystats_analysis = None
        try:
            logger.info("Fetching FootyStats enhanced metrics...")
            footystats_analysis = self.enhanced_analyzer.analyze_match_quality(
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                home_team_name=teams.get('home', {}).get('name', 'Unknown'),
                away_team_name=teams.get('away', {}).get('name', 'Unknown'),
                league_id=league_id  # CRITICAL: Pass league for precise search
            )
            if footystats_analysis:
                logger.info(
                    f"FootyStats Quality Score: {footystats_analysis.get('quality_score', 0)}, "
                    f"BTTS Prob: {footystats_analysis.get('btts_probability', 0):.2%}"
                )
            else:
                logger.info("FootyStats data not available for this match")
        except Exception as e:
            logger.warning(f"FootyStats analysis failed (continuing with base prediction): {e}")

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

                # Prepare notification data BEFORE any DB operation
                analysis = {
                    "home_probability": probabilities["home_win"],
                    "draw_probability": probabilities["draw"],
                    "away_probability": probabilities["away_win"],
                    "expected_home_goals": expected_home,
                    "expected_away_goals": expected_away,
                    "home_form": home_form,
                    "away_form": away_form,
                    "goal_ranges": goal_ranges,
                    "footystats": footystats_analysis,  # Add FootyStats data
                    "confidence": self.value_detector.get_confidence_rating(
                        value_result["edge"],
                        footystats_quality=footystats_analysis.get('quality_score', 50) if footystats_analysis else 50
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

                # CRITICAL: Send notification FIRST, save to DB ONLY if successful
                logger.info("Sending notification to Telegram...")
                message_id = await self.telegram.send_value_bet_alert(
                    fixture=fixture,
                    analysis=analysis,
                    value_bet=value_bet_data
                )

                # Only save to database if notification was successfully sent
                if message_id:
                    logger.info(f"✅ Notification sent successfully (message_id: {message_id})")

                    # NOW save to database (notification confirmed)
                    self._save_analysis(
                        fixture_id,
                        probabilities,
                        expected_home,
                        expected_away,
                        outcome,
                        value_result,
                        odds,
                        message_id=message_id  # Save telegram message ID
                    )

                    self.alerts_sent_today += 1
                    logger.info(f"✅ Analysis saved to database")
                else:
                    # Notification failed - DO NOT save to DB, will retry next cycle
                    logger.error(f"❌ Failed to send notification, will retry in next cycle")

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

        API Response structure:
        [
          {
            "league": {...},
            "fixture": {...},
            "bookmakers": [  ← Array of bookmakers
              {
                "name": "Bet365",
                "bets": [
                  {
                    "name": "Match Winner",
                    "values": [
                      {"value": "Home", "odd": "1.33"},
                      {"value": "Draw", "odd": "5.25"},
                      {"value": "Away", "odd": "8.50"}
                    ]
                  }
                ]
              }
            ]
          }
        ]

        Args:
            odds_data: Odds data from API

        Returns:
            Dictionary with best odds for each outcome (Home, Draw, Away)
        """
        best_odds = {}

        # Iterate through response (usually single item)
        for odds_item in odds_data:
            # Access bookmakers array (CRITICAL FIX)
            bookmakers = odds_item.get("bookmakers", [])

            for bookmaker in bookmakers:
                bookmaker_name = bookmaker.get("name", "Unknown")

                for bet in bookmaker.get("bets", []):
                    if bet.get("name") == "Match Winner":
                        for value in bet.get("values", []):
                            outcome = value.get("value")
                            odd_str = value.get("odd", "0")

                            # Convert string to float (API returns strings)
                            try:
                                odds = float(odd_str)
                            except (ValueError, TypeError):
                                logger.warning(f"Invalid odd value: {odd_str} from {bookmaker_name}")
                                continue

                            # Keep best (highest) odds for better value
                            if outcome not in best_odds or odds > best_odds[outcome]:
                                best_odds[outcome] = odds
                                logger.debug(f"Best odd for {outcome}: {odds} ({bookmaker_name})")

        if best_odds:
            logger.info(f"✅ Extracted best odds: {best_odds}")
        else:
            logger.warning("⚠️ No valid odds extracted from API response")

        return best_odds

    def _save_analysis(
        self,
        fixture_id: int,
        probabilities: Dict,
        expected_home: float,
        expected_away: float,
        outcome: str,
        value_result: Dict,
        odds: float,
        message_id: int = None
    ):
        """
        Save analysis to database

        IMPORTANT: Only call this AFTER successfully sending the notification.
        This ensures we only mark as "sent" if the user actually received it.

        Args:
            message_id: Telegram message ID (required for notification log)
        """
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

            # Create notification log (only if notification was sent)
            notification = NotificationLog(
                value_bet_id=value_bet.id,
                telegram_message_id=message_id,
                status="sent"  # We know it was sent because message_id exists
            )
            session.add(notification)

            session.commit()
            logger.debug(f"Saved analysis for fixture {fixture_id} with notification status: sent")

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

            # Calculate goal ranges probabilities (0-1, 2-3, 4+)
            goal_ranges = self.poisson_analyzer.calculate_goal_ranges_probabilities(
                expected_home,
                expected_away
            )

            # ENHANCED: Get FootyStats quality analysis
            footystats_analysis = None
            try:
                logger.info("Fetching FootyStats enhanced metrics...")
                footystats_analysis = self.enhanced_analyzer.analyze_match_quality(
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    home_team_name=teams.get('home', {}).get('name', 'Unknown'),
                    away_team_name=teams.get('away', {}).get('name', 'Unknown')
                )
                if footystats_analysis:
                    logger.info(
                        f"FootyStats Quality Score: {footystats_analysis.get('quality_score', 0)}, "
                        f"BTTS Prob: {footystats_analysis.get('btts_probability', 0):.2%}"
                    )
                else:
                    logger.info("FootyStats data not available for this match")
            except Exception as e:
                logger.warning(f"FootyStats analysis failed (continuing with base prediction): {e}")

            # Get odds (MUST have real odds - no mocks in production)
            logger.info(f"📊 Fetching odds for fixture {fixture_id}")
            odds_data = self.data_collector.collect_fixture_odds(fixture_id)

            logger.info(f"📊 Odds data received: {type(odds_data)}, length: {len(odds_data) if odds_data else 0}")

            if odds_data:
                best_odds = self._extract_best_odds(odds_data)
            else:
                best_odds = {}
                logger.warning(f"⚠️ collect_fixture_odds returned None/empty for fixture {fixture_id}")

            # CRITICAL: If no real odds, continue analysis but WITHOUT value bet detection
            # Show Poisson predictions and stats, but mark that value bet is unavailable
            if not best_odds:
                logger.warning(
                    f"⚠️ No market odds found for fixture {fixture_id}. "
                    f"Will show statistical analysis but NO value bet detection."
                )
                # Set flag that odds are unavailable
                odds_unavailable = True
            else:
                odds_unavailable = False

            # Check for value bets (ONLY if we have real odds)
            has_value = False
            best_value = None
            best_edge = 0

            if not odds_unavailable:
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
            else:
                logger.info("⚠️ Skipping value bet detection (no market odds available)")

            # Extract API predictions (handle empty or missing data)
            api_pred = {}
            api_percent = {}

            if api_predictions and isinstance(api_predictions, dict):
                api_pred = api_predictions.get("predictions", {})
                api_percent = api_pred.get("percent", {}) if api_pred else {}
                logger.info(f"🔍 API predictions raw data for fixture {fixture_id}:")
                logger.info(f"   - Full predictions keys: {list(api_predictions.keys())}")
                logger.info(f"   - api_pred keys: {list(api_pred.keys()) if api_pred else 'None'}")
                logger.info(f"   - Percent data: {api_percent}")
                logger.info(f"   - Winner: {api_pred.get('winner', {})}")
                logger.info(f"   - Advice: {api_pred.get('advice', 'N/A')}")

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

            # Helper function to detect generic/unreliable API predictions
            def is_generic_prediction(home_pct: float, draw_pct: float, away_pct: float) -> bool:
                """
                Detect if API predictions are generic/unreliable

                Generic patterns:
                - 50-50-0 (no data)
                - 33-33-33 (equal probabilities)
                - 10-45-45 (common default pattern)
                - 45-45-10 (common default pattern)
                - Any pattern that seems like a default
                """
                # Pattern 1: 50-50-0 or similar
                if abs(home_pct - 0.50) < 0.01 and abs(draw_pct - 0.50) < 0.01 and away_pct < 0.01:
                    return True
                # Pattern 2: Equal probabilities (33-33-33)
                if abs(home_pct - 0.33) < 0.02 and abs(draw_pct - 0.33) < 0.02 and abs(away_pct - 0.33) < 0.02:
                    return True
                # Pattern 3: 10-45-45 or 45-45-10 (common default for Liga MX)
                if abs(home_pct - 0.10) < 0.01 and abs(draw_pct - 0.45) < 0.01 and abs(away_pct - 0.45) < 0.01:
                    return True
                if abs(home_pct - 0.45) < 0.01 and abs(draw_pct - 0.45) < 0.01 and abs(away_pct - 0.10) < 0.01:
                    return True
                # Pattern 4: All zeros
                if home_pct == 0 and draw_pct == 0 and away_pct == 0:
                    return True
                return False

            # Parse API predictions
            api_home = safe_parse_percent(api_percent.get("home"))
            api_draw = safe_parse_percent(api_percent.get("draw"))
            api_away = safe_parse_percent(api_percent.get("away"))

            # Check if predictions are generic/unreliable
            api_predictions_reliable = not is_generic_prediction(api_home, api_draw, api_away)

            if not api_predictions_reliable:
                logger.warning(f"⚠️ API predictions appear to be generic/unreliable: {api_home:.1%}, {api_draw:.1%}, {api_away:.1%}")

            # Build analysis result with BOTH predictions
            return {
                "has_value": has_value,
                "odds_unavailable": odds_unavailable,  # Flag if market odds not available
                "our_prediction": {
                    "home": probabilities["home_win"],
                    "draw": probabilities["draw"],
                    "away": probabilities["away_win"]
                },
                "api_prediction": {
                    "home": api_home,
                    "draw": api_draw,
                    "away": api_away,
                    "winner": api_pred.get("winner", {}).get("name") if api_pred else None,
                    "advice": api_pred.get("advice") if api_pred else None,
                    "reliable": api_predictions_reliable  # Flag to indicate if predictions are reliable
                },
                "statistics": {
                    "expected_goals_home": expected_home,
                    "expected_goals_away": expected_away,
                    "home_form": home_stats_full["form"],
                    "away_form": away_stats_full["form"],
                    "home_matches": home_stats.get("home_matches", 0),
                    "away_matches": away_stats.get("away_matches", 0)
                },
                "goal_ranges": goal_ranges,
                "footystats": footystats_analysis,  # Add FootyStats data
                "h2h": {
                    "last_5": api_predictions.get("h2h", [])[:5] if "h2h" in api_predictions else []
                },
                "value_bet": best_value if has_value else None
            }

        except Exception as e:
            logger.error(f"Error analyzing fixture {fixture_id}: {e}")
            return None

    def analyze_fixture_apifootball(self, fixture: Dict) -> Dict:
        """
        Analyze fixture using ONLY API-Football predictions

        Args:
            fixture: Fixture data

        Returns:
            API-Football analysis only
        """
        try:
            fixture_id = fixture.get("fixture", {}).get("id")
            teams = fixture.get("teams", {})

            logger.info("Fetching API-Football predictions...")
            api_predictions_raw = self.api_client.get_predictions(fixture_id)

            if isinstance(api_predictions_raw, list) and len(api_predictions_raw) > 0:
                api_predictions = api_predictions_raw[0]
            elif isinstance(api_predictions_raw, dict):
                api_predictions = api_predictions_raw
            else:
                api_predictions = {}

            api_pred = api_predictions.get("predictions", {})
            api_percent = api_pred.get("percent", {}) if api_pred else {}

            return {
                "source": "api_football",
                "teams": teams,
                "fixture_info": fixture.get("fixture", {}),
                "league": fixture.get("league", {}),
                "predictions": api_pred,
                "percent": api_percent,
                "h2h": api_predictions.get("h2h", [])[:5] if "h2h" in api_predictions else [],
                "comparison": api_predictions.get("comparison", {})
            }

        except Exception as e:
            logger.error(f"Error in API-Football analysis: {e}")
            return None

    def analyze_fixture_poisson(self, fixture: Dict) -> Dict:
        """
        Analyze fixture using ONLY Poisson model

        Args:
            fixture: Fixture data

        Returns:
            Poisson analysis only
        """
        try:
            teams = fixture.get("teams", {})
            home_team_id = teams.get("home", {}).get("id")
            away_team_id = teams.get("away", {}).get("id")
            league_id = fixture.get("league", {}).get("id")

            # Get team stats
            home_stats = self._get_team_stats(home_team_id, league_id, is_home=True)
            away_stats = self._get_team_stats(away_team_id, league_id, is_home=False)

            # Calculate expected goals
            expected_home, expected_away = self.poisson_analyzer.calculate_expected_goals(
                home_stats,
                away_stats,
                league_id=league_id
            )

            # Calculate probabilities
            probabilities = self.poisson_analyzer.calculate_match_probabilities(
                expected_home,
                expected_away
            )

            # Goal ranges
            goal_ranges = self.poisson_analyzer.calculate_goal_ranges_probabilities(
                expected_home,
                expected_away
            )

            # Get odds for value bet detection
            fixture_id = fixture.get("fixture", {}).get("id")
            odds_data = self.data_collector.collect_fixture_odds(fixture_id)
            best_odds = self._extract_best_odds(odds_data) if odds_data else {}

            return {
                "source": "poisson",
                "teams": teams,
                "fixture_info": fixture.get("fixture", {}),
                "league": fixture.get("league", {}),
                "probabilities": probabilities,
                "expected_goals": {
                    "home": expected_home,
                    "away": expected_away
                },
                "goal_ranges": goal_ranges,
                "best_odds": best_odds,
                "has_odds": bool(best_odds)
            }

        except Exception as e:
            logger.error(f"Error in Poisson analysis: {e}")
            return None

    def analyze_fixture_footystats(self, fixture: Dict) -> Dict:
        """
        Analyze fixture using ONLY FootyStats data

        Args:
            fixture: Fixture data

        Returns:
            FootyStats analysis only
        """
        try:
            teams = fixture.get("teams", {})
            home_team_id = teams.get("home", {}).get("id")
            away_team_id = teams.get("away", {}).get("id")
            home_team_name = teams.get("home", {}).get("name", "Unknown")
            away_team_name = teams.get("away", {}).get("name", "Unknown")

            logger.info("Fetching FootyStats data...")
            league_id = fixture.get("league", {}).get("id")
            footystats_analysis = self.enhanced_analyzer.analyze_match_quality(
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                home_team_name=home_team_name,
                away_team_name=away_team_name,
                league_id=league_id  # CRITICAL: Pass league for precise search
            )

            if not footystats_analysis:
                return {
                    "source": "footystats",
                    "available": False,
                    "message": "Datos de FootyStats no disponibles para estos equipos"
                }

            return {
                "source": "footystats",
                "available": True,
                "teams": teams,
                "fixture_info": fixture.get("fixture", {}),
                "league": fixture.get("league", {}),
                "analysis": footystats_analysis
            }

        except Exception as e:
            logger.error(f"Error in FootyStats analysis: {e}")
            return None

    def sync_leagues(self):
        """Sync leagues to database"""
        logger.info("Syncing leagues...")
        self.data_collector.sync_leagues()
