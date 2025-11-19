#!/usr/bin/env python3
"""
Automatic team mapping script - Maps ALL teams from database to FootyStats

This script:
1. Gets all teams from our database (by league)
2. Fetches all teams from FootyStats for that league
3. Uses smart fuzzy matching to find best matches
4. Shows results for MANUAL REVIEW before saving
5. Allows user to confirm or correct mappings
"""

import sys
from pathlib import Path
from difflib import SequenceMatcher

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import db_manager
from src.database.models import Team, TeamIDMapping
from src.api.footystats_client import FootyStatsClient
from src.utils.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# League mappings (API-Football → FootyStats)
LEAGUE_MAPPINGS = {
    39: 1625,    # Premier League
    140: 1869,   # La Liga
    78: 1845,    # Bundesliga
    135: 1729,   # Serie A
    262: 2037,   # Liga MX
}


def similarity(a: str, b: str) -> float:
    """Calculate string similarity (0-1)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_best_match(team_name: str, footystats_teams: list) -> tuple:
    """
    Find best FootyStats match for a team name

    Returns:
        (footystats_id, footystats_name, confidence_score)
    """
    best_match_id = None
    best_match_name = None
    best_similarity = 0

    # Normalize team name
    normalized_name = team_name.lower().strip()

    for fs_team in footystats_teams:
        fs_name = fs_team.get('name', '')
        fs_clean_name = fs_team.get('cleanName', '')
        fs_id = fs_team.get('id')

        # Try both name and cleanName
        similarity_score = max(
            similarity(normalized_name, fs_name.lower()),
            similarity(normalized_name, fs_clean_name.lower())
        )

        if similarity_score > best_similarity:
            best_similarity = similarity_score
            best_match_id = fs_id
            best_match_name = fs_name

    return (best_match_id, best_match_name, best_similarity)


def analyze_league_mappings(league_id: int, dry_run: bool = True):
    """
    Analyze and map all teams for a league

    Args:
        league_id: API-Football league ID
        dry_run: If True, only show results without saving
    """
    footystats_league_id = LEAGUE_MAPPINGS.get(league_id)

    if not footystats_league_id:
        logger.error(f"❌ No FootyStats mapping for league {league_id}")
        return

    logger.info(f"\n{'=' * 80}")
    logger.info(f"🏆 ANALYZING LEAGUE {league_id} → FootyStats {footystats_league_id}")
    logger.info(f"{'=' * 80}")

    # Get teams from our database (extract data while in session)
    with db_manager.get_session() as session:
        our_teams_data = []
        teams_query = session.query(Team).filter_by(league_id=league_id).all()

        for team in teams_query:
            our_teams_data.append({
                'id': team.id,
                'name': team.name,
                'league_id': team.league_id
            })

    logger.info(f"📊 Found {len(our_teams_data)} teams in our database")

    # Get teams from FootyStats
    client = FootyStatsClient()
    fs_teams = client.get_league_teams(footystats_league_id)

    logger.info(f"📊 Found {len(fs_teams)} teams in FootyStats")
    logger.info("")

    # Map each team
    mappings = []
    perfect_matches = 0
    good_matches = 0
    poor_matches = 0
    no_matches = 0

    for our_team in sorted(our_teams_data, key=lambda t: t['name']):
        fs_id, fs_name, confidence = find_best_match(our_team['name'], fs_teams)

        status_emoji = "✅"
        status_text = "PERFECT"

        if confidence >= 0.95:
            perfect_matches += 1
            status_emoji = "✅"
            status_text = "PERFECT"
        elif confidence >= 0.70:
            good_matches += 1
            status_emoji = "🟡"
            status_text = "GOOD"
        elif confidence >= 0.50:
            poor_matches += 1
            status_emoji = "⚠️"
            status_text = "POOR"
        else:
            no_matches += 1
            status_emoji = "❌"
            status_text = "NO MATCH"

        print(f"{status_emoji} {status_text:10} | Conf: {confidence:5.1%} | "
              f"API:{our_team['id']:4} {our_team['name']:30} → FS:{fs_id:4} {fs_name}")

        mappings.append({
            'api_id': our_team['id'],
            'api_name': our_team['name'],
            'fs_id': fs_id,
            'fs_name': fs_name,
            'confidence': confidence,
            'league_id': league_id
        })

    # Summary
    logger.info("")
    logger.info(f"{'=' * 80}")
    logger.info(f"📊 SUMMARY:")
    logger.info(f"  ✅ Perfect matches (>95%): {perfect_matches}")
    logger.info(f"  🟡 Good matches (70-95%): {good_matches}")
    logger.info(f"  ⚠️  Poor matches (50-70%): {poor_matches}")
    logger.info(f"  ❌ No matches (<50%): {no_matches}")
    logger.info(f"{'=' * 80}\n")

    # Save if not dry run
    if not dry_run:
        logger.info("💾 Saving mappings to database...")
        save_mappings(mappings)
        logger.info("✅ Mappings saved successfully!")
    else:
        logger.info("🧪 DRY RUN - No data saved. Run with --save to persist mappings.")

    return mappings


def save_mappings(mappings: list):
    """Save mappings to database"""
    with db_manager.get_session() as session:
        for mapping in mappings:
            # Check if mapping exists
            existing = session.query(TeamIDMapping).filter_by(
                api_football_id=mapping['api_id']
            ).first()

            if existing:
                # Update existing
                existing.footystats_id = mapping['fs_id']
                existing.team_name = mapping['api_name']
                existing.league_id = mapping['league_id']
                existing.confidence_score = mapping['confidence']
                existing.is_verified = (mapping['confidence'] >= 0.95)  # Auto-verify perfect matches
            else:
                # Create new
                new_mapping = TeamIDMapping(
                    api_football_id=mapping['api_id'],
                    footystats_id=mapping['fs_id'],
                    team_name=mapping['api_name'],
                    league_id=mapping['league_id'],
                    confidence_score=mapping['confidence'],
                    is_verified=(mapping['confidence'] >= 0.95)
                )
                session.add(new_mapping)

        logger.info(f"💾 Saved {len(mappings)} mappings")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Auto-map teams to FootyStats')
    parser.add_argument('--league', type=int, help='League ID to process (default: all)')
    parser.add_argument('--save', action='store_true', help='Save mappings to database (default: dry run)')

    args = parser.parse_args()

    db_manager.initialize()

    # Process leagues
    leagues_to_process = [args.league] if args.league else list(LEAGUE_MAPPINGS.keys())

    for league_id in leagues_to_process:
        try:
            analyze_league_mappings(league_id, dry_run=not args.save)
        except Exception as e:
            logger.error(f"❌ Error processing league {league_id}: {e}", exc_info=True)

    logger.info("\n" + "=" * 80)
    if args.save:
        logger.info("✅ ALL MAPPINGS SAVED TO DATABASE!")
    else:
        logger.info("🧪 DRY RUN COMPLETED - Review results above")
        logger.info("💡 To save mappings, run with --save flag:")
        logger.info(f"   python scripts/auto_map_all_teams.py --save")
    logger.info("=" * 80 + "\n")


if __name__ == "__main__":
    main()
