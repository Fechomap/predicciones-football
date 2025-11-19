#!/usr/bin/env python3
"""
DRY RUN - Test full season fixture loading WITHOUT storing to database

This script simulates the full season load to validate:
1. API calls are working correctly
2. Data extraction is correct
3. Week/season calculation is accurate
4. Team mapping would succeed

NO DATA IS WRITTEN TO DATABASE - Safe to run multiple times
"""

import sys
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.api_football import APIFootballClient
from src.services.team_mapping_service import TeamMappingService
from src.utils.config import Config
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_current_season(league_id: int) -> int:
    """Determine current season for a league"""
    now = datetime.now()
    month = now.month
    year = now.year

    # Liga MX uses current year
    if league_id == 262:
        return year

    # European leagues: If before August, season is previous year
    if month < 8:
        return year - 1
    else:
        return year


def extract_week_from_round(round_str: str) -> int:
    """Extract week/matchday from round string"""
    if not round_str:
        return None

    match = re.search(r'(\d+)', round_str)
    if match:
        return int(match.group(1))

    return None


def analyze_fixtures(fixtures: list, league_id: int, season: int):
    """
    Analyze fixtures WITHOUT storing them
    Returns statistics about what would be stored
    """
    stats = {
        'total': len(fixtures),
        'by_status': defaultdict(int),
        'by_week': defaultdict(int),
        'teams': set(),
        'venues': set(),
        'rounds': set(),
        'date_range': {'earliest': None, 'latest': None},
        'invalid_timestamps': 0,
        'missing_teams': 0
    }

    sample_fixtures = []

    for fixture_data in fixtures:
        fixture_info = fixture_data.get("fixture", {})
        teams = fixture_data.get("teams", {})
        league = fixture_data.get("league", {})

        # Status
        status = fixture_info.get("status", {}).get("short", "NS")
        stats['by_status'][status] += 1

        # Round and week
        round_str = league.get("round")
        stats['rounds'].add(round_str)
        week = extract_week_from_round(round_str)
        if week:
            stats['by_week'][week] += 1

        # Teams
        home_team = teams.get("home", {})
        away_team = teams.get("away", {})
        home_id = home_team.get("id")
        away_id = away_team.get("id")

        if home_id:
            stats['teams'].add((home_id, home_team.get("name")))
        else:
            stats['missing_teams'] += 1

        if away_id:
            stats['teams'].add((away_id, away_team.get("name")))
        else:
            stats['missing_teams'] += 1

        # Venue
        venue = fixture_info.get("venue", {}).get("name")
        if venue:
            stats['venues'].add(venue)

        # Date range
        timestamp = fixture_info.get("timestamp", 0)
        if timestamp > 0:
            kickoff = datetime.fromtimestamp(timestamp)

            if stats['date_range']['earliest'] is None or kickoff < stats['date_range']['earliest']:
                stats['date_range']['earliest'] = kickoff

            if stats['date_range']['latest'] is None or kickoff > stats['date_range']['latest']:
                stats['date_range']['latest'] = kickoff
        else:
            stats['invalid_timestamps'] += 1

        # Collect samples for display
        if len(sample_fixtures) < 3:
            sample_fixtures.append({
                'id': fixture_info.get("id"),
                'home': home_team.get("name"),
                'away': away_team.get("name"),
                'date': datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M") if timestamp > 0 else "Invalid",
                'round': round_str,
                'week': week,
                'status': status,
                'venue': venue
            })

    return stats, sample_fixtures


def print_league_report(league_id: int, league_name: str, stats: dict, sample_fixtures: list):
    """Print detailed report for a league"""
    logger.info(f"\n{'=' * 80}")
    logger.info(f"📊 LEAGUE ANALYSIS: {league_name} (ID: {league_id})")
    logger.info(f"{'=' * 80}")

    logger.info(f"\n📈 FIXTURE STATISTICS:")
    logger.info(f"  • Total fixtures: {stats['total']}")
    logger.info(f"  • Unique teams: {len(stats['teams'])}")
    logger.info(f"  • Unique venues: {len(stats['venues'])}")
    logger.info(f"  • Unique rounds: {len(stats['rounds'])}")

    if stats['date_range']['earliest'] and stats['date_range']['latest']:
        logger.info(f"\n📅 DATE RANGE:")
        logger.info(f"  • Earliest: {stats['date_range']['earliest'].strftime('%Y-%m-%d %H:%M')}")
        logger.info(f"  • Latest: {stats['date_range']['latest'].strftime('%Y-%m-%d %H:%M')}")
        duration_days = (stats['date_range']['latest'] - stats['date_range']['earliest']).days
        logger.info(f"  • Duration: {duration_days} days (~{duration_days // 7} weeks)")

    logger.info(f"\n🏆 BY STATUS:")
    for status, count in sorted(stats['by_status'].items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  • {status:6s}: {count:3d} fixtures")

    if stats['by_week']:
        weeks = sorted(stats['by_week'].keys())
        logger.info(f"\n📆 BY WEEK:")
        logger.info(f"  • Week range: {min(weeks)} - {max(weeks)}")
        logger.info(f"  • Total weeks: {len(weeks)}")
        # Show first 5 weeks
        for week in weeks[:5]:
            logger.info(f"    - Week {week:2d}: {stats['by_week'][week]} fixtures")
        if len(weeks) > 5:
            logger.info(f"    ... ({len(weeks) - 5} more weeks)")

    if stats['invalid_timestamps'] > 0:
        logger.info(f"\n⚠️  WARNINGS:")
        logger.info(f"  • Invalid timestamps: {stats['invalid_timestamps']}")
    if stats['missing_teams'] > 0:
        logger.info(f"  • Missing team IDs: {stats['missing_teams']}")

    logger.info(f"\n📋 SAMPLE FIXTURES (first 3):")
    for i, fixture in enumerate(sample_fixtures, 1):
        logger.info(f"\n  [{i}] Fixture ID: {fixture['id']}")
        logger.info(f"      {fixture['home']} vs {fixture['away']}")
        logger.info(f"      Date: {fixture['date']}")
        logger.info(f"      Round: {fixture['round']} (Week {fixture['week']})")
        logger.info(f"      Status: {fixture['status']}")
        logger.info(f"      Venue: {fixture['venue']}")

    logger.info(f"\n✅ This league would contribute {stats['total']} fixtures to the database")


def test_team_mapping_sample(teams: set, league_id: int):
    """
    Test team mapping for a sample of teams (first 5)
    Shows if FootyStats mapping would work
    """
    logger.info(f"\n{'=' * 80}")
    logger.info(f"🗺️  TESTING TEAM MAPPING (sample of 5 teams)")
    logger.info(f"{'=' * 80}")

    mapping_service = TeamMappingService()

    sample_teams = list(teams)[:5]
    success = 0
    failed = 0

    for team_id, team_name in sample_teams:
        try:
            logger.info(f"\n🔍 Testing: {team_name} (API ID: {team_id})")

            footystats_id = mapping_service.get_footystats_id(
                api_football_id=team_id,
                team_name=team_name,
                league_id=league_id
            )

            if footystats_id:
                logger.info(f"   ✅ Mapped to FootyStats ID: {footystats_id}")
                success += 1
            else:
                logger.info(f"   ❌ Mapping failed (no match found)")
                failed += 1

        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            failed += 1

    logger.info(f"\n📊 MAPPING TEST RESULTS:")
    logger.info(f"  • Successful: {success}/{len(sample_teams)}")
    logger.info(f"  • Failed: {failed}/{len(sample_teams)}")

    if success >= 3:
        logger.info(f"  ✅ Mapping looks good! Should work for full dataset")
    else:
        logger.warning(f"  ⚠️  Low success rate - review team mapping logic")


def main():
    """Main dry run execution"""
    logger.info("=" * 80)
    logger.info("🧪 DRY RUN - FULL SEASON FIXTURE LOADING")
    logger.info("=" * 80)
    logger.info("\n⚠️  NO DATA WILL BE WRITTEN TO DATABASE")
    logger.info("This is a validation run to check API responses and data quality\n")

    # Initialize API client
    api_client = APIFootballClient()

    # Get enabled leagues from config
    enabled_leagues = Config.ENABLED_LEAGUES
    logger.info(f"📋 Enabled leagues: {enabled_leagues}")

    # League names for better reporting
    league_names = {
        262: "Liga MX",
        39: "Premier League",
        140: "La Liga",
        78: "Bundesliga",
        135: "Serie A"
    }

    total_fixtures = 0
    total_teams = set()

    # Test each league
    for league_id in enabled_leagues:
        season = get_current_season(league_id)
        league_name = league_names.get(league_id, f"League {league_id}")

        logger.info(f"\n{'=' * 80}")
        logger.info(f"🔍 FETCHING: {league_name} - Season {season}")
        logger.info(f"{'=' * 80}")

        try:
            # Fetch fixtures for different statuses
            all_fixtures = []
            statuses = ["NS", "FT", "PST"]  # Most common statuses for dry run

            for status in statuses:
                logger.info(f"\n📡 Fetching status '{status}'...")
                fixtures = api_client.get_fixtures(
                    league_id=league_id,
                    season=season,
                    status=status
                )
                all_fixtures.extend(fixtures)
                logger.info(f"   → Found {len(fixtures)} fixtures")

            if all_fixtures:
                # Analyze fixtures
                stats, sample_fixtures = analyze_fixtures(all_fixtures, league_id, season)

                # Print report
                print_league_report(league_id, league_name, stats, sample_fixtures)

                # Accumulate totals
                total_fixtures += stats['total']
                total_teams.update(stats['teams'])

                # Test team mapping for this league (sample only)
                if stats['teams']:
                    test_team_mapping_sample(stats['teams'], league_id)
            else:
                logger.warning(f"⚠️  No fixtures found for {league_name}")

        except Exception as e:
            logger.error(f"❌ Error fetching {league_name}: {e}", exc_info=True)

    # Final summary
    logger.info(f"\n{'=' * 80}")
    logger.info(f"📊 FINAL SUMMARY")
    logger.info(f"{'=' * 80}")
    logger.info(f"\n✅ DRY RUN COMPLETED SUCCESSFULLY!")
    logger.info(f"\n📈 TOTALS THAT WOULD BE STORED:")
    logger.info(f"  • Total fixtures: {total_fixtures}")
    logger.info(f"  • Unique teams: {len(total_teams)}")
    logger.info(f"  • Leagues processed: {len(enabled_leagues)}")

    logger.info(f"\n💡 NEXT STEPS:")
    logger.info(f"  1. Review the reports above")
    logger.info(f"  2. Verify week extraction is working correctly")
    logger.info(f"  3. Check team mapping success rate")
    logger.info(f"  4. If everything looks good, run the real script:")
    logger.info(f"     python scripts/load_full_season_fixtures.py")

    logger.info(f"\n{'=' * 80}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Dry run cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
