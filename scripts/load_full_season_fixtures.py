#!/usr/bin/env python3
"""
Script to load ALL fixtures for the entire season for all enabled leagues

This script:
1. Fetches ALL fixtures for the current season (NS, FT, LIVE, CANCELLED, etc.)
2. Stores them permanently in the database
3. Extracts week/season info from round field
4. Maps all teams to FootyStats IDs

Run this once at the start of the season, then periodically to update status.
"""

import sys
import re
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import db_manager
from src.database.models import Fixture, Team, League
from src.api.api_football import APIFootballClient
from src.api.footystats_client import FootyStatsClient
from src.services.team_mapping_service import TeamMappingService
from src.utils.config import Config
from sqlalchemy import text
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_current_season(league_id: int) -> int:
    """
    Determine current season for a league based on calendar type

    European leagues (Aug-May): Season starts in Aug
    Split seasons (Liga MX): Current year
    """
    now = datetime.now()
    month = now.month
    year = now.year

    # Liga MX and similar leagues use current year
    if league_id == 262:
        return year

    # European leagues: If before August, season is previous year
    # e.g., April 2025 -> season 2024/2025 -> use 2024
    if month < 8:
        return year - 1
    else:
        return year


def extract_week_from_round(round_str: str) -> int:
    """
    Extract week/matchday number from round string

    Examples:
      "Regular Season - 15" -> 15
      "Matchday 10" -> 10
      "Week 5" -> 5
      "Championship Round - 2" -> 2
    """
    if not round_str:
        return None

    # Try to find first number in the string
    match = re.search(r'(\d+)', round_str)
    if match:
        return int(match.group(1))

    return None


def load_fixtures_for_league(api_client: APIFootballClient, league_id: int, season: int):
    """
    Load ALL fixtures for a league/season

    Args:
        api_client: API-Football client
        league_id: League ID
        season: Season year (e.g., 2025)
    """
    logger.info(f"📥 Fetching ALL fixtures for league {league_id} season {season}...")

    try:
        # Fetch ALL fixtures (no status filter = all statuses)
        # We'll make multiple calls with different statuses to ensure we get everything
        all_fixtures = []

        statuses = ["NS", "FT", "LIVE", "PST", "CANC", "SUSP", "ABD"]  # All possible statuses

        for status in statuses:
            fixtures = api_client.get_fixtures(
                league_id=league_id,
                season=season,
                status=status
            )
            all_fixtures.extend(fixtures)
            logger.info(f"  Found {len(fixtures)} fixtures with status '{status}'")

        logger.info(f"✅ Total fixtures fetched: {len(all_fixtures)}")

        return all_fixtures

    except Exception as e:
        logger.error(f"❌ Failed to fetch fixtures for league {league_id}: {e}")
        return []


def store_fixtures_with_metadata(fixtures: list, season: int):
    """
    Store fixtures in database with season/week metadata

    Args:
        fixtures: List of fixture data from API
        season: Season year
    """
    with db_manager.get_session() as session:
        stored = 0
        updated = 0

        for fixture_data in fixtures:
            fixture_info = fixture_data.get("fixture", {})
            fixture_id = fixture_info.get("id")

            if not fixture_id:
                continue

            # Extract all data
            teams = fixture_data.get("teams", {})
            league = fixture_data.get("league", {})

            home_team_id = teams.get("home", {}).get("id")
            away_team_id = teams.get("away", {}).get("id")
            league_id = league.get("id")
            round_str = league.get("round")

            # Extract week from round
            week = extract_week_from_round(round_str)

            # Validate timestamp
            timestamp = fixture_info.get("timestamp", 0)
            if timestamp <= 0:
                logger.warning(f"⚠️  Skipping fixture {fixture_id} - invalid timestamp")
                continue

            kickoff_time = datetime.fromtimestamp(timestamp)
            status = fixture_info.get("status", {}).get("short", "NS")
            venue = fixture_info.get("venue", {}).get("name")

            # Check if fixture exists
            existing = session.query(Fixture).filter_by(id=fixture_id).first()

            if existing:
                # Update existing fixture
                existing.status = status
                existing.kickoff_time = kickoff_time
                existing.round = round_str
                existing.season = season
                existing.week = week
                existing.last_updated = datetime.utcnow()

                # Archive if finished
                if status in ["FT", "AET", "PEN"]:
                    existing.is_archived = True

                updated += 1
            else:
                # Ensure teams exist
                _ensure_team_exists(session, home_team_id, teams.get("home", {}).get("name"),
                                   teams.get("home", {}).get("logo"), league_id)
                _ensure_team_exists(session, away_team_id, teams.get("away", {}).get("name"),
                                   teams.get("away", {}).get("logo"), league_id)

                # Create new fixture with metadata
                new_fixture = Fixture(
                    id=fixture_id,
                    league_id=league_id,
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    kickoff_time=kickoff_time,
                    status=status,
                    venue=venue,
                    round=round_str,
                    season=season,
                    week=week,
                    is_archived=(status in ["FT", "AET", "PEN"])
                )
                session.add(new_fixture)
                stored += 1

        session.commit()
        logger.info(f"💾 Stored {stored} new fixtures, updated {updated} existing")


def _ensure_team_exists(session, team_id: int, team_name: str, logo_url: str, league_id: int):
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
        session.flush()


def map_all_teams_to_footystats():
    """
    DEPRECATED: Use auto_map_all_teams.py script instead

    This function is kept for backward compatibility but should not be used.
    The new onboarding process uses:
    - scripts/auto_map_all_teams.py --save
    """
    logger.warning("⚠️  This function is deprecated. Use scripts/auto_map_all_teams.py instead")
    return

    # Initialize mapping service (fixes F821 bug even though code is unreachable)
    mapping_service = TeamMappingService()

    with db_manager.get_session() as session:
        teams = session.query(Team).all()
        logger.info(f"Found {len(teams)} teams to map")

        mapped = 0
        failed = 0

        for team in teams:
            try:
                # This will search and cache the mapping
                footystats_id = mapping_service.get_footystats_id(
                    api_football_id=team.id,
                    team_name=team.name,
                    league_id=team.league_id
                )

                if footystats_id:
                    mapped += 1
                else:
                    failed += 1
                    logger.warning(f"⚠️  Failed to map team: {team.name} (ID: {team.id})")

            except Exception as e:
                failed += 1
                logger.error(f"❌ Error mapping team {team.name}: {e}")

        logger.info(f"✅ Mapped {mapped} teams, {failed} failed")


def main():
    """Main execution"""
    logger.info("=" * 70)
    logger.info("🚀 LOADING FULL SEASON FIXTURES")
    logger.info("=" * 70)

    # Initialize database
    db_manager.initialize()

    # Initialize API client
    api_client = APIFootballClient()

    # Get enabled leagues from config
    enabled_leagues = Config.ENABLED_LEAGUES
    logger.info(f"📋 Enabled leagues: {enabled_leagues}")

    total_fixtures = 0

    # Load fixtures for each league
    for league_id in enabled_leagues:
        season = get_current_season(league_id)
        logger.info(f"\n{'=' * 70}")
        logger.info(f"Processing League {league_id} - Season {season}")
        logger.info(f"{'=' * 70}")

        fixtures = load_fixtures_for_league(api_client, league_id, season)

        if fixtures:
            store_fixtures_with_metadata(fixtures, season)
            total_fixtures += len(fixtures)

    logger.info(f"\n{'=' * 70}")
    logger.info(f"✅ COMPLETED: Loaded {total_fixtures} total fixtures")
    logger.info(f"{'=' * 70}\n")

    # Now map all teams to FootyStats
    logger.info(f"\n{'=' * 70}")
    logger.info("🗺️  MAPPING TEAMS TO FOOTYSTATS")
    logger.info(f"{'=' * 70}")
    map_all_teams_to_footystats()

    logger.info(f"\n{'=' * 70}")
    logger.info("✅ ALL OPERATIONS COMPLETED SUCCESSFULLY!")
    logger.info(f"{'=' * 70}\n")

    # Print summary statistics
    with db_manager.get_session() as session:
        fixture_count = session.query(Fixture).count()
        team_count = session.query(Team).count()
        league_count = session.query(League).count()

        logger.info("📊 DATABASE SUMMARY:")
        logger.info(f"  • Leagues: {league_count}")
        logger.info(f"  • Teams: {team_count}")
        logger.info(f"  • Fixtures: {fixture_count}")

        # Count by status
        for status in ["NS", "FT", "LIVE", "PST"]:
            count = session.query(Fixture).filter_by(status=status).count()
            logger.info(f"    - {status}: {count}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
