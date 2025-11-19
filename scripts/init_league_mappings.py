#!/usr/bin/env python3
"""
Initialize league ID mappings between API-Football and FootyStats

This script maps league IDs to enable precise team searches.
Run once after database setup.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import db_manager, LeagueIDMapping

# Verified league mappings - TEMPORADA 2024-2025
# Format: (API-Football ID, FootyStats Season ID, League Name, Country)
LEAGUE_MAPPINGS = [
    # TEMPORADA 2024-2025 (IDs actualizados)
    (39, 12325, "Premier League", "England"),       # 2024-2025
    (140, 12316, "La Liga", "Spain"),               # 2024-2025
    (78, 12529, "Bundesliga", "Germany"),           # 2024-2025
    (135, 12530, "Serie A", "Italy"),               # 2024-2025
    (262, 12136, "Liga MX", "Mexico"),              # 2024-2025

    # NOTA: FootyStats usa IDs por temporada
    # Actualizar cada año con los nuevos IDs de temporada
]


def init_league_mappings():
    """Initialize league mappings in database"""
    print("\n" + "="*60)
    print("🏆 INITIALIZING LEAGUE ID MAPPINGS")
    print("="*60 + "\n")

    try:
        db_manager.initialize()
        db_manager.create_tables()
        print("✅ Database initialized\n")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

    print(f"📝 Adding {len(LEAGUE_MAPPINGS)} league mappings...\n")

    success_count = 0

    with db_manager.get_session() as session:
        for api_id, fs_id, name, country in LEAGUE_MAPPINGS:
            try:
                # Check if mapping exists
                existing = session.query(LeagueIDMapping).filter_by(
                    api_football_id=api_id
                ).first()

                if existing:
                    # Update
                    existing.footystats_id = fs_id
                    existing.league_name = name
                    existing.country = country
                    print(f"  ✏️  {name:30s} API:{api_id:4d} → FS:{fs_id}")
                else:
                    # Create new
                    mapping = LeagueIDMapping(
                        api_football_id=api_id,
                        footystats_id=fs_id,
                        league_name=name,
                        country=country,
                        is_verified=True
                    )
                    session.add(mapping)
                    print(f"  ✅ {name:30s} API:{api_id:4d} → FS:{fs_id}")

                success_count += 1

            except Exception as e:
                print(f"  ❌ {name:30s} Error: {e}")

        session.commit()

    print("\n" + "="*60)
    print("📊 LEAGUE MAPPING STATISTICS")
    print("="*60)
    print(f"Total leagues mapped:  {success_count}/{len(LEAGUE_MAPPINGS)}")
    print("="*60 + "\n")

    print("✅ League mappings initialized successfully\n")
    print("💡 Now team searches will be PRECISE - searching only in the correct league!\n")

    return True


if __name__ == "__main__":
    success = init_league_mappings()
    sys.exit(0 if success else 1)
