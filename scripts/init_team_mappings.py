#!/usr/bin/env python3
"""
Initialize team ID mappings for top teams

This script adds manual verified mappings for the most important teams
to ensure FootyStats integration works immediately.

Run once after database setup.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.team_mapping_service import TeamMappingService
from src.api.footystats_client import FootyStatsClient
from src.database.connection import db_manager

# Manual mappings for top teams
# Format: (API-Football ID, FootyStats ID, Team Name)
TOP_TEAM_MAPPINGS = [
    # Premier League (VERIFIED)
    (35, 148, "Bournemouth"),  # ✅ Verified
    (48, 153, "West Ham"),     # ✅ Verified

    # Premier League (TODO: Verify FootyStats IDs)
    (49, 8, "Chelsea"),
    (40, 10, "Liverpool"),
    (33, 11, "Manchester United"),
    (50, 12, "Manchester City"),
    (42, 13, "Arsenal"),
    (47, 14, "Tottenham"),

    # La Liga
    (529, 45, "Barcelona"),
    (541, 46, "Real Madrid"),
    (530, 47, "Atletico Madrid"),

    # Bundesliga
    (157, 82, "Bayern Munich"),
    (165, 83, "Borussia Dortmund"),

    # Serie A
    (489, 105, "AC Milan"),
    (496, 106, "Juventus"),
    (487, 107, "Inter Milan"),

    # Liga MX
    (2448, 1234, "America"),  # TODO: Find actual FootyStats IDs
    (2283, 1235, "Chivas"),
    (2282, 1236, "Cruz Azul"),
    (2299, 1237, "Tigres"),
    (2280, 1238, "Monterrey"),

    # Ligue 1
    (85, 140, "Paris Saint Germain"),
]


def init_team_mappings():
    """Initialize team mappings in database"""
    print("\n" + "="*60)
    print("🔧 INITIALIZING TEAM ID MAPPINGS")
    print("="*60 + "\n")

    # Initialize database
    try:
        db_manager.initialize()
        db_manager.create_tables()
        print("✅ Database initialized\n")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

    # Initialize mapping service
    try:
        footystats_client = FootyStatsClient()
        mapping_service = TeamMappingService(footystats_client)
        print("✅ Mapping service initialized\n")
    except Exception as e:
        print(f"❌ Error initializing service: {e}")
        return False

    # Add manual mappings
    print(f"📝 Adding {len(TOP_TEAM_MAPPINGS)} manual team mappings...\n")

    success_count = 0
    for api_id, footystats_id, team_name in TOP_TEAM_MAPPINGS:
        try:
            mapping_service.add_manual_mapping(
                api_football_id=api_id,
                footystats_id=footystats_id,
                team_name=team_name
            )
            print(f"  ✅ {team_name:30s} API:{api_id:6d} → FS:{footystats_id}")
            success_count += 1
        except Exception as e:
            print(f"  ❌ {team_name:30s} Error: {e}")

    # Show stats
    stats = mapping_service.get_mapping_stats()
    print("\n" + "="*60)
    print("📊 MAPPING STATISTICS")
    print("="*60)
    print(f"Total mappings:      {stats['total_mappings']}")
    print(f"Verified mappings:   {stats['verified_mappings']}")
    print(f"Successful mappings: {stats['successful_mappings']}")
    print(f"Failed mappings:     {stats['failed_mappings']}")
    print("="*60 + "\n")

    print(f"✅ Successfully added {success_count}/{len(TOP_TEAM_MAPPINGS)} mappings\n")
    print("💡 NOTE: FootyStats IDs in this script are PLACEHOLDERS.")
    print("   You need to research actual FootyStats team IDs and update them.\n")
    print("   For now, the system will gracefully handle missing mappings.\n")

    return True


if __name__ == "__main__":
    success = init_team_mappings()
    sys.exit(0 if success else 1)
