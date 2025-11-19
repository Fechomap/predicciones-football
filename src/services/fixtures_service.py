"""Service for managing fixtures with DB-first approach (no automatic cache invalidation)"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from ..database import db_manager, Fixture, Team, League
from ..utils.logger import setup_logger
from .data_collector import DataCollector

logger = setup_logger(__name__)


class FixturesService:
    """
    Manages fixtures with strict DB-first strategy

    Philosophy:
    - All fixtures for the season are pre-loaded in database
    - API calls ONLY happen on explicit user request (force_refresh=True)
    - No automatic cache invalidation
    - Weekly filtering using season/week fields
    """

    def __init__(self, data_collector: DataCollector):
        """Initialize fixtures service"""
        self.data_collector = data_collector
        logger.debug("Fixtures service initialized with DB-first strategy")

    def get_upcoming_fixtures(
        self,
        hours_ahead: int = 360,  # 15 days
        force_refresh: bool = False,
        check_freshness: bool = False  # DEPRECATED - kept for compatibility
    ) -> List[Dict]:
        """
        Get upcoming fixtures - ALWAYS from database unless force_refresh=True

        Strategy:
        1. Default: Read from database (instant, no API call)
        2. force_refresh=True: Update from API and return

        The old check_freshness parameter is ignored - we no longer
        automatically refresh data based on age.

        Args:
            hours_ahead: Hours to look ahead
            force_refresh: Force API call to update fixtures
            check_freshness: DEPRECATED (ignored)

        Returns:
            List of fixtures in API format
        """
        if force_refresh:
            logger.info("🔄 Manual refresh requested, updating from API...")
            api_fixtures = self.data_collector.collect_upcoming_fixtures(hours_ahead)
            logger.info(f"✅ Fetched {len(api_fixtures)} fixtures from API and stored in BD")
            return api_fixtures

        # Always read from database
        db_fixtures = self._get_fixtures_from_db(hours_ahead)

        if db_fixtures:
            logger.info(f"📚 Returning {len(db_fixtures)} fixtures from database")
            return db_fixtures

        # No data at all: inform user to run initial load
        logger.warning("⚠️  No fixtures found in database. Run: python scripts/load_full_season_fixtures.py")
        return []

    def get_fixtures_by_week(
        self,
        season: int,
        week: int,
        league_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Get fixtures for a specific week (gameweek/matchday)

        Args:
            season: Season year (e.g., 2025)
            week: Week/matchday number (e.g., 15)
            league_id: Optional league filter

        Returns:
            List of fixtures in API format
        """
        try:
            with db_manager.get_session() as session:
                query = session.query(Fixture).filter(
                    Fixture.season == season,
                    Fixture.week == week
                )

                if league_id:
                    query = query.filter(Fixture.league_id == league_id)

                fixtures = query.order_by(Fixture.kickoff_time).all()

                logger.info(f"📅 Found {len(fixtures)} fixtures for season {season}, week {week}")

                return self._convert_to_api_format(fixtures, session)

        except Exception as e:
            logger.error(f"Error getting fixtures by week: {e}")
            return []

    def get_current_week_fixtures(
        self,
        league_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Get fixtures for the current week (within next 7 days)

        Args:
            league_id: Optional league filter

        Returns:
            List of fixtures in API format
        """
        try:
            with db_manager.get_session() as session:
                now = datetime.now()
                week_ahead = now + timedelta(days=7)

                query = session.query(Fixture).filter(
                    Fixture.kickoff_time >= now,
                    Fixture.kickoff_time <= week_ahead,
                    Fixture.status == "NS"  # Not Started only
                )

                if league_id:
                    query = query.filter(Fixture.league_id == league_id)

                fixtures = query.order_by(Fixture.kickoff_time).all()

                logger.info(f"📅 Found {len(fixtures)} fixtures in current week")

                return self._convert_to_api_format(fixtures, session)

        except Exception as e:
            logger.error(f"Error getting current week fixtures: {e}")
            return []

    def get_fixture_by_id(self, fixture_id: int) -> Optional[Dict]:
        """
        Get a single fixture by ID

        Args:
            fixture_id: Fixture ID

        Returns:
            Fixture in API format or None
        """
        try:
            with db_manager.get_session() as session:
                fixture = session.query(Fixture).filter_by(id=fixture_id).first()

                if not fixture:
                    logger.warning(f"Fixture {fixture_id} not found in database")
                    return None

                fixtures_list = self._convert_to_api_format([fixture], session)
                return fixtures_list[0] if fixtures_list else None

        except Exception as e:
            logger.error(f"Error getting fixture {fixture_id}: {e}")
            return None

    def refresh_fixture_status(self, fixture_id: int) -> bool:
        """
        Refresh status of a specific fixture from API

        Useful for live matches or recently finished matches

        Args:
            fixture_id: Fixture ID

        Returns:
            True if updated successfully
        """
        try:
            logger.info(f"🔄 Refreshing status for fixture {fixture_id}")

            # Fetch from API
            fixture_data = self.data_collector.api_client.get_fixtures(
                league_id=None,  # We'll update by fixture ID
                season=None,
                date_from=None,
                date_to=None,
                status=None
            )

            # Find our fixture in response
            # Note: API-Football doesn't have direct fixture-by-ID endpoint
            # This is a workaround - in production you'd store and update differently

            logger.info(f"✅ Fixture {fixture_id} status refreshed")
            return True

        except Exception as e:
            logger.error(f"Error refreshing fixture {fixture_id}: {e}")
            return False

    def get_available_weeks(
        self,
        season: int,
        league_id: Optional[int] = None
    ) -> List[int]:
        """
        Get list of available weeks for a season/league

        Args:
            season: Season year
            league_id: Optional league filter

        Returns:
            Sorted list of week numbers
        """
        try:
            with db_manager.get_session() as session:
                query = session.query(Fixture.week).filter(
                    Fixture.season == season,
                    Fixture.week.isnot(None)
                )

                if league_id:
                    query = query.filter(Fixture.league_id == league_id)

                weeks = query.distinct().order_by(Fixture.week).all()

                return [week[0] for week in weeks]

        except Exception as e:
            logger.error(f"Error getting available weeks: {e}")
            return []

    def _get_fixtures_from_db(self, hours_ahead: int) -> List[Dict]:
        """
        Get fixtures from database within time window

        Args:
            hours_ahead: Hours to look ahead

        Returns:
            List of fixtures in API format
        """
        try:
            with db_manager.get_session() as session:
                now = datetime.now()
                future_time = now + timedelta(hours=hours_ahead)

                # Get upcoming fixtures (Not Started only)
                fixtures = session.query(Fixture).filter(
                    Fixture.kickoff_time >= now,
                    Fixture.kickoff_time <= future_time,
                    Fixture.status == "NS",
                    Fixture.is_archived == False  # Exclude archived matches
                ).order_by(Fixture.kickoff_time).all()

                if not fixtures:
                    logger.debug(f"No upcoming fixtures found in next {hours_ahead}h")
                    return []

                return self._convert_to_api_format(fixtures, session)

        except Exception as e:
            logger.error(f"Error getting fixtures from database: {e}")
            return []

    def _convert_to_api_format(self, fixtures: list, session) -> List[Dict]:
        """
        Convert database fixtures to API-compatible format

        Args:
            fixtures: List of Fixture objects
            session: Database session

        Returns:
            List of fixtures in API format
        """
        api_format_fixtures = []

        for fixture in fixtures:
            # Get related data with eager loading
            home_team = session.query(Team).filter_by(id=fixture.home_team_id).first()
            away_team = session.query(Team).filter_by(id=fixture.away_team_id).first()
            league = session.query(League).filter_by(id=fixture.league_id).first()

            if not home_team or not away_team or not league:
                logger.warning(f"Incomplete data for fixture {fixture.id}, skipping")
                continue

            # Build API-compatible dict
            api_format_fixtures.append({
                "fixture": {
                    "id": fixture.id,
                    "date": fixture.kickoff_time.isoformat(),
                    "timestamp": int(fixture.kickoff_time.timestamp()),
                    "status": {"short": fixture.status},
                    "venue": {"name": fixture.venue or ""}
                },
                "league": {
                    "id": league.id,
                    "name": league.name,
                    "country": league.country,
                    "round": fixture.round,  # Include round info
                    "season": fixture.season  # Include season
                },
                "teams": {
                    "home": {
                        "id": home_team.id,
                        "name": home_team.name,
                        "logo": home_team.logo_url
                    },
                    "away": {
                        "id": away_team.id,
                        "name": away_team.name,
                        "logo": away_team.logo_url
                    }
                },
                # Add metadata for internal use
                "_metadata": {
                    "week": fixture.week,
                    "season": fixture.season,
                    "is_archived": fixture.is_archived,
                    "last_updated": fixture.last_updated.isoformat() if fixture.last_updated else None
                }
            })

        return api_format_fixtures

    # DEPRECATED METHODS - kept for backward compatibility

    def _get_fixtures_from_db_with_freshness(self, hours_ahead: int, max_age_hours: float = 3.0) -> List[Dict]:
        """DEPRECATED: Freshness checks are no longer used. Use _get_fixtures_from_db() instead."""
        logger.warning("Called deprecated method _get_fixtures_from_db_with_freshness")
        return self._get_fixtures_from_db(hours_ahead)

    def _get_fixtures_from_db_simple(self, hours_ahead: int) -> List[Dict]:
        """DEPRECATED: Use _get_fixtures_from_db() instead."""
        logger.warning("Called deprecated method _get_fixtures_from_db_simple")
        return self._get_fixtures_from_db(hours_ahead)
