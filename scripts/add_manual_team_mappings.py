#!/usr/bin/env python3
"""
Add manual team mappings for teams that fail fuzzy matching
Run this once to fix common problematic teams
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import db_manager
from src.database.models import TeamIDMapping
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Manual mappings for problematic teams (verified by comparing both APIs)
# Format: (api_football_id, footystats_id, team_name, league_id, confidence)
# Based on auto_map_all_teams.py analysis results

MANUAL_MAPPINGS = [
    # Premier League (API: 39, FootyStats: 12325)
    # CORRECCIONES BASADAS EN auto_map_all_teams.py --save

    # ✅ Ya mapeados correctamente por auto_map (100% confianza):
    # Arsenal, Aston Villa, Brentford, Chelsea, Crystal Palace, Everton,
    # Fulham, Liverpool, Man City, Man United, Nottingham Forest

    # 🔧 CORRECCIONES NECESARIAS (baja confianza o erróneas):
    (51, 209, "Brighton", 39, 1.0),  # CORRECCIÓN: Brighton → Brighton & Hove Albion FC
    (44, 145, "Burnley", 39, 1.0),  # CORRECCIÓN: Burnley → Burnley FC
    (63, None, "Leeds", 39, 0.0),  # Leeds no está en FootyStats (descendido)
    (746, None, "Sunderland", 39, 0.0),  # Sunderland no está en FootyStats (Championship)
    (47, 92, "Tottenham", 39, 1.0),  # Tottenham → Tottenham Hotspur FC (verificado)
    (48, 153, "West Ham", 39, 1.0),  # West Ham → West Ham United FC (verificado)
    (39, 223, "Wolves", 39, 1.0),  # Wolves → Wolverhampton Wanderers FC (verificado)

    # La Liga (API: 140, FootyStats: 12316)
    # Ya mapeados automáticamente con buena confianza

    # Bundesliga (API: 78, FootyStats: 12529)
    # Ya mapeados automáticamente con buena confianza

    # Serie A (API: 135, FootyStats: 12530)
    (505, 470, "Inter", 135, 1.0),  # CORRECCIÓN: Inter → FC Internazionale Milano
    (504, 473, "Verona", 135, 1.0),  # CORRECCIÓN: Verona → Hellas Verona FC

    # Liga MX (API: 262, FootyStats: 12136)
    # ✅ Ya mapeados correctamente por auto_map:
    # Atlas, Atlético San Luis, Club América, Cruz Azul, FC Juárez,
    # Guadalajara Chivas, León, Mazatlán, Monterrey, Necaxa,
    # Pachuca, Puebla, Santos Laguna, Tigres UANL, Toluca

    # 🔧 CORRECCIÓN CRÍTICA:
    (2286, 1422, "U.N.A.M. - Pumas", 262, 1.0),  # CORRECCIÓN: Pumas → Club Universidad Nacional
    (2290, 1427, "Club Queretaro", 262, 1.0),  # CORRECCIÓN: Querétaro FC (verificado)
    (2280, 1418, "Club Tijuana", 262, 1.0),  # CORRECCIÓN: Tijuana (verificado)

    # NOTE: Teams with None for footystats_id are NOT in FootyStats database
    # This is EXPECTED for newly promoted or smaller teams
]


def add_manual_mappings():
    """Add manual team mappings to database"""
    logger.info("🔧 Adding manual team mappings...")

    db_manager.initialize()

    with db_manager.get_session() as session:
        added = 0
        updated = 0
        skipped = 0

        for mapping_data in MANUAL_MAPPINGS:
            api_id, fs_id, team_name, league_id, confidence = mapping_data

            # Skip teams that don't exist in FootyStats
            if fs_id is None:
                logger.info(f"⏭️  Skipped: {team_name} (not in FootyStats)")
                skipped += 1
                continue

            # Check if mapping already exists
            existing = session.query(TeamIDMapping).filter_by(
                api_football_id=api_id
            ).first()

            if existing:
                # Update existing
                existing.footystats_id = fs_id
                existing.team_name = team_name
                existing.league_id = league_id
                existing.confidence_score = confidence if confidence > 0 else 1.0
                existing.is_verified = True
                logger.info(f"📝 Updated: {team_name} (API:{api_id} → FS:{fs_id}, conf:{confidence:.0%})")
                updated += 1
            else:
                # Create new
                new_mapping = TeamIDMapping(
                    api_football_id=api_id,
                    footystats_id=fs_id,
                    team_name=team_name,
                    league_id=league_id,
                    confidence_score=confidence if confidence > 0 else 1.0,
                    is_verified=True
                )
                session.add(new_mapping)
                logger.info(f"✅ Added: {team_name} (API:{api_id} → FS:{fs_id}, conf:{confidence:.0%})")
                added += 1

    logger.info(f"\n📊 Summary:")
    logger.info(f"  • Added: {added}")
    logger.info(f"  • Updated: {updated}")
    logger.info(f"  • Skipped (not in FootyStats): {skipped}")
    logger.info(f"  • Total processed: {added + updated + skipped}")


def find_footystats_id(team_name: str):
    """
    Helper function to find FootyStats ID for a team
    Use this to discover the correct ID before adding to MANUAL_MAPPINGS
    """
    from src.api.footystats_client import FootyStatsClient

    client = FootyStatsClient()

    # Search in Premier League
    teams = client.get_league_teams(1625)  # Premier League FootyStats ID

    logger.info(f"\n🔍 Searching for: {team_name}")
    logger.info("=" * 60)

    for team in teams:
        name = team.get('name', '')
        if team_name.lower() in name.lower() or name.lower() in team_name.lower():
            logger.info(f"✅ Found: {name}")
            logger.info(f"   FootyStats ID: {team.get('id')}")
            logger.info(f"   Clean name: {team.get('cleanName')}")

    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Manage manual team mappings')
    parser.add_argument('--find', type=str, help='Search for a team in FootyStats')
    parser.add_argument('--add', action='store_true', help='Add manual mappings')

    args = parser.parse_args()

    if args.find:
        find_footystats_id(args.find)
    elif args.add:
        add_manual_mappings()
    else:
        print("Usage:")
        print("  Find team ID:    python scripts/add_manual_team_mappings.py --find 'Nottingham Forest'")
        print("  Add mappings:    python scripts/add_manual_team_mappings.py --add")
