#!/usr/bin/env python3
"""
Completar mapeo de Premier League manualmente
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import db_manager, TeamIDMapping

# Mapeos manuales verificados (equipos que no alcanzaron 95% con fuzzy matching)
MANUAL_MAPPINGS = {
    39: 223,   # Wolves → Wolverhampton Wanderers FC
    51: 209,   # Brighton → Brighton & Hove Albion FC
    47: 92,    # Tottenham → Tottenham Hotspur FC
    48: 153,   # West Ham → West Ham United FC
    34: 157,   # Newcastle → Newcastle United FC
    35: 148,   # Bournemouth → AFC Bournemouth
    55: 218,   # Brentford → Brentford FC
    66: 158,   # Aston Villa → Aston Villa FC
}

# Equipos que NO están en Premier 2024-2025 (bajaron)
NOT_IN_LEAGUE = {
    63: "Leeds United",        # Descendió
    746: "Sunderland",          # No está en Premier
}


def complete_mapping():
    """Completa el mapeo de Premier League"""

    print("\n" + "="*70)
    print("  ✅ COMPLETANDO MAPEO PREMIER LEAGUE")
    print("="*70)

    db_manager.initialize()

    with db_manager.get_session() as session:
        mapped_count = 0

        for api_id, fs_id in MANUAL_MAPPINGS.items():
            # Verificar si existe
            existing = session.query(TeamIDMapping).filter_by(
                api_football_id=api_id
            ).first()

            # Obtener nombre del equipo
            from src.database import Team
            team = session.query(Team).filter_by(id=api_id).first()
            team_name = team.name if team else f"Team {api_id}"

            if existing:
                print(f"  ℹ️  {team_name:30} ya existe, actualizando...")
                existing.footystats_id = fs_id
                existing.confidence_score = 1.0  # 100% manual
                existing.is_verified = True
            else:
                mapping = TeamIDMapping(
                    api_football_id=api_id,
                    footystats_id=fs_id,
                    team_name=team_name,
                    league_id=39,  # Premier League
                    confidence_score=1.0,  # 100% manual
                    is_verified=True
                )
                session.add(mapping)
                print(f"  ✅ {team_name:30} API:{api_id:4} → FS:{fs_id:4}")

            mapped_count += 1

        session.commit()

        print(f"\n✅ Mapeados {mapped_count} equipos adicionales")

        # Marcar equipos que no están en la liga
        print(f"\n📝 Equipos NO en Premier League 2024-2025:")
        for api_id, name in NOT_IN_LEAGUE.items():
            print(f"  ⚠️  {name:30} (descendió o no está)")

    # Verificar total
    with db_manager.get_session() as session:
        total_mapped = session.query(TeamIDMapping).filter(
            TeamIDMapping.api_football_id.in_(list(MANUAL_MAPPINGS.keys()) + [40, 33, 50, 42, 49, 36, 52, 45, 44])
        ).count()

        print(f"\n" + "="*70)
        print(f"  📊 COBERTURA PREMIER LEAGUE: {total_mapped}/18 equipos")
        print(f"  (Leeds y Sunderland no aplican - están fuera de Premier)")
        print("="*70 + "\n")


if __name__ == "__main__":
    complete_mapping()
