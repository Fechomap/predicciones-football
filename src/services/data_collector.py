"""Data collection service"""
from datetime import datetime
from typing import List, Dict, Optional

from ..api import APIFootballClient
from ..database import db_manager, Team, Fixture, League, OddsHistory
from ..utils.config import Config, LEAGUE_CONFIG
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class DataCollector:
    """Collects and stores data from API-Football"""

    def __init__(self):
        """Initialize data collector"""
        self.api_client = APIFootballClient()
        logger.debug("Data collector initialized")

    def sync_leagues(self):
        """Sync configured leagues to database"""
        with db_manager.get_session() as session:
            for league_id in Config.ENABLED_LEAGUES:
                league_info = LEAGUE_CONFIG.get(league_id, {})

                # Check if league exists
                league = session.query(League).filter_by(id=league_id).first()

                if not league:
                    # Create new league
                    league = League(
                        id=league_id,
                        name=league_info.get("name", f"League {league_id}"),
                        country=league_info.get("country", "Unknown"),
                        enabled=True
                    )
                    session.add(league)
                    logger.info(f"Added league: {league.name}")

            session.commit()

    def collect_upcoming_fixtures(self, hours_ahead: int = 360) -> List[Dict]:  # 15 días
        """
        Collect upcoming fixtures from API

        Args:
            hours_ahead: Hours to look ahead

        Returns:
            List of upcoming fixtures
        """
        logger.info(f"Collecting upcoming fixtures ({hours_ahead}h ahead)...")

        fixtures = self.api_client.get_upcoming_fixtures(
            league_ids=Config.ENABLED_LEAGUES,
            hours_ahead=hours_ahead
        )

        logger.info(f"Collected {len(fixtures)} upcoming fixtures")

        # Store in database
        self._store_fixtures(fixtures)

        return fixtures

    def _store_fixtures(self, fixtures: List[Dict]):
        """
        Store fixtures in database

        Args:
            fixtures: List of fixture data from API
        """
        with db_manager.get_session() as session:
            for fixture_data in fixtures:
                fixture_info = fixture_data.get("fixture", {})
                fixture_id = fixture_info.get("id")

                if not fixture_id:
                    continue

                # Check if fixture already exists
                existing = session.query(Fixture).filter_by(id=fixture_id).first()

                if existing:
                    # Update existing fixture with timestamp validation
                    timestamp = fixture_info.get("timestamp", 0)
                    if timestamp <= 0:
                        logger.error(f"Invalid timestamp for fixture {fixture_id}: {timestamp}")
                        continue

                    existing.status = fixture_info.get("status", {}).get("short", "NS")
                    existing.kickoff_time = datetime.fromtimestamp(timestamp)
                else:
                    # Extract data
                    teams = fixture_data.get("teams", {})
                    league = fixture_data.get("league", {})

                    home_team_id = teams.get("home", {}).get("id")
                    away_team_id = teams.get("away", {}).get("id")
                    league_id = league.get("id")

                    # Ensure teams exist
                    self._ensure_team_exists(
                        session,
                        home_team_id,
                        teams.get("home", {}).get("name"),
                        teams.get("home", {}).get("logo"),
                        league_id
                    )
                    self._ensure_team_exists(
                        session,
                        away_team_id,
                        teams.get("away", {}).get("name"),
                        teams.get("away", {}).get("logo"),
                        league_id
                    )

                    # Validate timestamp before creating fixture
                    timestamp = fixture_info.get("timestamp", 0)
                    if timestamp <= 0:
                        logger.error(f"Invalid timestamp for new fixture {fixture_id}: {timestamp}")
                        continue

                    # Create new fixture
                    new_fixture = Fixture(
                        id=fixture_id,
                        league_id=league_id,
                        home_team_id=home_team_id,
                        away_team_id=away_team_id,
                        kickoff_time=datetime.fromtimestamp(timestamp),
                        status=fixture_info.get("status", {}).get("short", "NS"),
                        venue=fixture_info.get("venue", {}).get("name"),
                        round=league.get("round")
                    )
                    session.add(new_fixture)

            session.commit()
            logger.info("Fixtures stored in database")

    def _ensure_team_exists(
        self,
        session,
        team_id: int,
        team_name: str,
        logo_url: str,
        league_id: int
    ):
        """Ensure team exists in database"""
        if not team_id:
            return

        team = session.query(Team).filter_by(id=team_id).first()

        if not team:
            team = Team(
                id=team_id,
                name=team_name,
                logo_url=logo_url,
                league_id=league_id
            )
            session.add(team)
            session.flush()  # Flush immediately to avoid duplicates in same transaction
            logger.debug(f"Added team: {team_name}")

    def collect_fixture_odds(self, fixture_id: int) -> Optional[Dict]:
        """
        Collect odds for a specific fixture

        Args:
            fixture_id: Fixture ID

        Returns:
            Odds data
        """
        try:
            logger.info(f"Collecting odds for fixture {fixture_id}")
            odds_data = self.api_client.get_odds(fixture_id)

            if odds_data:
                self._store_odds(fixture_id, odds_data)

            return odds_data

        except Exception as e:
            logger.error(f"Failed to collect odds for fixture {fixture_id}: {e}")
            return None

    def _store_odds(self, fixture_id: int, odds_data: List[Dict]):
        """
        Store odds in database

        Args:
            fixture_id: Fixture ID
            odds_data: Odds data from API
        """
        with db_manager.get_session() as session:
            for bookmaker_data in odds_data:
                bookmaker_name = bookmaker_data.get("bookmaker", {}).get("name")

                for bet in bookmaker_data.get("bets", []):
                    market_type = bet.get("name")

                    for value in bet.get("values", []):
                        outcome = value.get("value")
                        odds_raw = value.get("odd")

                        # Validate and convert odds to float
                        try:
                            odds = float(odds_raw)
                            if odds <= 0:
                                logger.warning(f"Invalid odds value: {odds}, skipping")
                                continue
                        except (ValueError, TypeError) as e:
                            logger.error(f"Cannot convert odds to float: {odds_raw}, error: {e}")
                            continue

                        # Create odds record
                        odds_record = OddsHistory(
                            fixture_id=fixture_id,
                            bookmaker=bookmaker_name,
                            market_type=market_type,
                            outcome=outcome,
                            odds=odds
                        )
                        session.add(odds_record)

            session.commit()
            logger.debug(f"Odds stored for fixture {fixture_id}")

    def collect_team_statistics(self, team_id: int, league_id: int, season: int):
        """
        Collect team statistics

        Args:
            team_id: Team ID
            league_id: League ID
            season: Season year
        """
        try:
            logger.info(f"Collecting stats for team {team_id}")
            stats = self.api_client.get_team_statistics(team_id, league_id, season)
            return stats

        except Exception as e:
            logger.error(f"Failed to collect stats for team {team_id}: {e}")
            return None
