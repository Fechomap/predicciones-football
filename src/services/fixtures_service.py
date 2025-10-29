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

    def get_upcoming_fixtures(self, hours_ahead: int = 168, force_refresh: bool = False) -> List[Dict]:
        """
        Get upcoming fixtures with smart caching

        Strategy:
        1. Check if we have fresh data in BD (< 1 hour old)
        2. If yes: return from BD (fast)
        3. If no or force_refresh: call API and update BD

        Args:
            hours_ahead: Hours to look ahead
            force_refresh: Force API call even if BD has data

        Returns:
            List of fixtures
        """
        # Check if we have recent fixtures in BD
        if not force_refresh:
            db_fixtures = self._get_fixtures_from_db(hours_ahead)

            if db_fixtures:
                logger.info(f"Returning {len(db_fixtures)} fixtures from database (cached)")
                return db_fixtures

        # No fresh data in BD or force_refresh: call API
        logger.info("Fetching fixtures from API...")
        api_fixtures = self.data_collector.collect_upcoming_fixtures(hours_ahead)

        logger.info(f"Fetched {len(api_fixtures)} fixtures from API and stored in BD")
        return api_fixtures

    def _get_fixtures_from_db(self, hours_ahead: int) -> List[Dict]:
        """
        Get fixtures from database

        Args:
            hours_ahead: Hours to look ahead

        Returns:
            List of fixtures in API format, or empty list if data is stale
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
                    logger.info("No fixtures found in database")
                    return []

                # Check if data is fresh (last update < 1 hour ago)
                # We check the newest created_at timestamp
                newest_fixture = max(fixtures, key=lambda f: f.created_at)
                time_delta = (now - newest_fixture.created_at).total_seconds()

                # Validate time delta with tolerance for clock differences
                # Allow up to 5 minutes of future timestamp (clock skew tolerance)
                CLOCK_SKEW_TOLERANCE = 300  # 5 minutes in seconds

                if time_delta < -CLOCK_SKEW_TOLERANCE:
                    # Only invalidate if timestamp is more than 5 min in the future
                    logger.warning(
                        f"Fixture timestamp significantly in future: "
                        f"{newest_fixture.created_at} > {now} (delta: {-time_delta:.0f}s)"
                    )
                    logger.info("Invalidating cache due to timestamp inconsistency")
                    return []

                # If time_delta is slightly negative (within tolerance), treat as 0
                if time_delta < 0:
                    logger.debug(
                        f"Minor clock skew detected ({-time_delta:.0f}s), within tolerance"
                    )
                    time_delta = 0

                data_age_hours = time_delta / 3600

                if data_age_hours > 1:
                    logger.info(f"Database fixtures are {data_age_hours:.1f}h old, will refresh from API")
                    return []

                # Convert to API format
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

                logger.info(f"Found {len(api_format_fixtures)} fixtures in database (age: {data_age_hours:.1f}h)")
                return api_format_fixtures

        except Exception as e:
            logger.error(f"Error getting fixtures from database: {e}")
            return []
