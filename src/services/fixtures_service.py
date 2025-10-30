"""Service for managing fixtures with smart caching"""
from datetime import datetime, timedelta
from typing import List, Dict

from ..database import db_manager, Fixture, Team, League
from ..utils.logger import setup_logger
from .data_collector import DataCollector

logger = setup_logger(__name__)


class FixturesService:
    """Manages fixtures with BD-first approach"""

    def __init__(self, data_collector: DataCollector):
        """Initialize fixtures service"""
        self.data_collector = data_collector
        logger.debug("Fixtures service initialized")

    def get_upcoming_fixtures(
        self,
        hours_ahead: int = 168,
        force_refresh: bool = False,
        check_freshness: bool = False
    ) -> List[Dict]:
        """
        Get upcoming fixtures with flexible caching strategy

        Strategy based on caller:
        1. User interactions (check_freshness=False, default):
           → Always return from BD (instant response)

        2. Monitoring cycle (check_freshness=True):
           → Check data age, refresh if > 3h old

        3. Manual refresh (force_refresh=True):
           → Always call API

        Args:
            hours_ahead: Hours to look ahead
            force_refresh: Force API call even if BD data is fresh
            check_freshness: Check data age and refresh if stale (for monitoring)

        Returns:
            List of fixtures
        """
        # Force refresh: always call API (manual user refresh)
        if force_refresh:
            logger.info("🔄 Force refresh requested, fetching from API...")
            api_fixtures = self.data_collector.collect_upcoming_fixtures(hours_ahead)
            logger.info(f"✅ Fetched {len(api_fixtures)} fixtures from API and stored in BD")
            return api_fixtures

        # Monitoring cycle: check freshness (refresh if > 3h old)
        if check_freshness:
            db_fixtures = self._get_fixtures_from_db_with_freshness(hours_ahead, max_age_hours=3)

            if db_fixtures:
                logger.info(f"📚 Returning {len(db_fixtures)} fixtures from database (fresh)")
                return db_fixtures

            # Stale data: fetch from API
            logger.info("🌐 Fetching fixtures from API (stale or missing data)...")
            api_fixtures = self.data_collector.collect_upcoming_fixtures(hours_ahead)
            logger.info(f"✅ Fetched {len(api_fixtures)} fixtures from API and stored in BD")
            return api_fixtures

        # User interaction: always return from BD (instant, no freshness check)
        db_fixtures = self._get_fixtures_from_db_simple(hours_ahead)

        if db_fixtures:
            logger.info(f"📚 Returning {len(db_fixtures)} fixtures from database")
            return db_fixtures

        # No data in BD at all: fetch from API (first run)
        logger.info("🌐 No fixtures in database, fetching from API...")
        api_fixtures = self.data_collector.collect_upcoming_fixtures(hours_ahead)
        logger.info(f"✅ Fetched {len(api_fixtures)} fixtures from API and stored in BD")
        return api_fixtures

    def _get_fixtures_from_db_with_freshness(self, hours_ahead: int, max_age_hours: float = 3.0) -> List[Dict]:
        """
        Get fixtures from database WITH freshness check

        Args:
            hours_ahead: Hours to look ahead
            max_age_hours: Maximum age of data in hours (default 3h)

        Returns:
            List of fixtures if fresh, empty list if stale
        """
        try:
            with db_manager.get_session() as session:
                now = datetime.now()
                future_time = now + timedelta(hours=hours_ahead)

                # Get fixtures from BD
                fixtures = session.query(Fixture).filter(
                    Fixture.kickoff_time >= now,
                    Fixture.kickoff_time <= future_time,
                    Fixture.status == "NS"  # Not Started
                ).all()

                if not fixtures:
                    return []

                # Check if data is fresh
                newest_fixture = max(fixtures, key=lambda f: f.created_at)
                time_delta = (now - newest_fixture.created_at).total_seconds()

                # Clock skew tolerance
                CLOCK_SKEW_TOLERANCE = 300  # 5 minutes
                if time_delta < -CLOCK_SKEW_TOLERANCE:
                    logger.warning("Fixture timestamp significantly in future, invalidating cache")
                    return []

                if time_delta < 0:
                    time_delta = 0

                data_age_hours = time_delta / 3600

                # Check if data is too old
                if data_age_hours >= max_age_hours:
                    logger.info(f"Database fixtures are {data_age_hours:.1f}h old (max: {max_age_hours}h), need refresh")
                    return []

                # Data is fresh, convert to API format
                api_format_fixtures = self._convert_to_api_format(fixtures, session)
                logger.debug(f"Found {len(api_format_fixtures)} fixtures in database (age: {data_age_hours:.1f}h)")
                return api_format_fixtures

        except Exception as e:
            logger.error(f"Error getting fixtures from database: {e}")
            return []

    def _convert_to_api_format(self, fixtures: list, session) -> List[Dict]:
        """
        Convert database fixtures to API format

        Args:
            fixtures: List of Fixture objects from database
            session: Database session

        Returns:
            List of fixtures in API-compatible format
        """
        api_format_fixtures = []

        for fixture in fixtures:
            # Get related data
            home_team = session.query(Team).filter_by(id=fixture.home_team_id).first()
            away_team = session.query(Team).filter_by(id=fixture.away_team_id).first()
            league = session.query(League).filter_by(id=fixture.league_id).first()

            if not home_team or not away_team or not league:
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
                    "country": league.country
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
                }
            })

        return api_format_fixtures

    def _get_fixtures_from_db_simple(self, hours_ahead: int) -> List[Dict]:
        """
        Get fixtures from database WITHOUT checking data age

        Simply queries BD for upcoming fixtures within the time window.
        Fast and efficient for user interactions.

        Args:
            hours_ahead: Hours to look ahead

        Returns:
            List of fixtures in API format
        """
        try:
            with db_manager.get_session() as session:
                now = datetime.now()
                future_time = now + timedelta(hours=hours_ahead)

                # Get fixtures from BD
                fixtures = session.query(Fixture).filter(
                    Fixture.kickoff_time >= now,
                    Fixture.kickoff_time <= future_time,
                    Fixture.status == "NS"  # Not Started
                ).all()

                if not fixtures:
                    return []

                # Convert to API format
                return self._convert_to_api_format(fixtures, session)

        except Exception as e:
            logger.error(f"Error getting fixtures from database: {e}")
            return []

    def _get_fixtures_from_db(self, hours_ahead: int) -> List[Dict]:
        """
        DEPRECATED: Use _get_fixtures_from_db_with_freshness instead

        Kept for backward compatibility during migration
        """
        return self._get_fixtures_from_db_with_freshness(hours_ahead, max_age_hours=1.0)
