#!/usr/bin/env python3
"""
Análisis completo del estado de la base de datos
- Partidos guardados
- IDs mapeados
- Estrategia de persistencia
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import db_manager, Fixture, Team, League, TeamIDMapping, AnalysisHistory
from datetime import datetime, timedelta
from sqlalchemy import func

def analyze_database():
    """Análisis completo de la base de datos"""

    print("\n" + "="*80)
    print("  📊 ANÁLISIS COMPLETO DE LA BASE DE DATOS")
    print("="*80)

    try:
        db_manager.initialize()

        with db_manager.get_session() as session:

            # ============================================================
            # 1. PARTIDOS (FIXTURES)
            # ============================================================
            print("\n" + "="*80)
            print("  [1] PARTIDOS GUARDADOS")
            print("="*80)

            total_fixtures = session.query(Fixture).count()
            print(f"\n📅 Total de partidos en BD: {total_fixtures}")

            if total_fixtures > 0:
                # Partidos por estado
                fixtures_by_status = session.query(
                    Fixture.status, func.count(Fixture.id)
                ).group_by(Fixture.status).all()

                print("\n📊 Partidos por estado:")
                for status, count in fixtures_by_status:
                    print(f"   {status:10s} → {count:4d} partidos")

                # Partidos futuros (próximos 30 días)
                now = datetime.now()
                future_30_days = now + timedelta(days=30)

                upcoming_fixtures = session.query(Fixture).filter(
                    Fixture.kickoff_time.between(now, future_30_days),
                    Fixture.status == 'NS'  # Not Started
                ).count()

                print(f"\n⏰ Partidos próximos 30 días: {upcoming_fixtures}")

                # Partidos por liga
                fixtures_by_league = session.query(
                    League.name, func.count(Fixture.id)
                ).join(Fixture, Fixture.league_id == League.id).group_by(League.name).all()

                print("\n🏆 Partidos por liga:")
                for league_name, count in fixtures_by_league:
                    print(f"   {league_name:30s} → {count:4d} partidos")

                # Fecha más antigua y más reciente
                oldest = session.query(func.min(Fixture.kickoff_time)).scalar()
                newest = session.query(func.max(Fixture.kickoff_time)).scalar()

                print(f"\n📆 Rango de fechas:")
                print(f"   Más antiguo: {oldest}")
                print(f"   Más reciente: {newest}")
            else:
                print("\n⚠️  NO HAY PARTIDOS EN LA BASE DE DATOS")
                print("   Ejecuta: python3 scripts/load_full_season_fixtures.py")

            # ============================================================
            # 2. EQUIPOS
            # ============================================================
            print("\n" + "="*80)
            print("  [2] EQUIPOS")
            print("="*80)

            total_teams = session.query(Team).count()
            print(f"\n👥 Total de equipos en BD: {total_teams}")

            if total_teams > 0:
                # Equipos por liga
                teams_by_league = session.query(
                    League.name, func.count(Team.id)
                ).join(Team, Team.league_id == League.id).group_by(League.name).all()

                print("\n🏆 Equipos por liga:")
                for league_name, count in teams_by_league:
                    print(f"   {league_name:30s} → {count:4d} equipos")

            # ============================================================
            # 3. MAPEO DE IDS FOOTYSTATS
            # ============================================================
            print("\n" + "="*80)
            print("  [3] MAPEO DE IDS FOOTYSTATS")
            print("="*80)

            total_mappings = session.query(TeamIDMapping).count()
            print(f"\n🗺️  Total de mapeos: {total_mappings}")

            if total_mappings > 0:
                # Mapeos por liga
                mappings_by_league = session.query(
                    League.name, func.count(TeamIDMapping.id)
                ).join(Team, TeamIDMapping.api_football_id == Team.id)\
                 .join(League, Team.league_id == League.id)\
                 .group_by(League.name).all()

                print("\n📊 Mapeos por liga:")
                for league_name, count in mappings_by_league:
                    print(f"   {league_name:30s} → {count:4d} equipos mapeados")

                # Porcentaje de cobertura
                print("\n📈 Cobertura de mapeo:")
                for league_name, team_count in teams_by_league:
                    mapped_count = next((count for ln, count in mappings_by_league if ln == league_name), 0)
                    coverage = (mapped_count / team_count * 100) if team_count > 0 else 0
                    status = "✅" if coverage >= 90 else "⚠️" if coverage >= 50 else "❌"
                    print(f"   {status} {league_name:30s} → {mapped_count:2d}/{team_count:2d} ({coverage:.1f}%)")
            else:
                print("\n❌ NO HAY MAPEOS DE FOOTYSTATS")
                print("   Ejecuta: python3 scripts/auto_map_all_teams.py")

            # ============================================================
            # 4. ANÁLISIS DE PARTIDOS
            # ============================================================
            print("\n" + "="*80)
            print("  [4] ANÁLISIS GUARDADOS")
            print("="*80)

            total_analyses = session.query(AnalysisHistory).count()
            print(f"\n📊 Total de análisis guardados: {total_analyses}")

            if total_analyses > 0:
                # Análisis por fixture
                analyses_per_fixture = session.query(
                    AnalysisHistory.fixture_id, func.count(AnalysisHistory.id)
                ).group_by(AnalysisHistory.fixture_id).all()

                # Fixtures con múltiples análisis
                multiple_analyses = [(fid, count) for fid, count in analyses_per_fixture if count > 1]

                if multiple_analyses:
                    print(f"\n⚠️  Fixtures con múltiples análisis: {len(multiple_analyses)}")
                    print("   (Se están repitiendo análisis innecesariamente)")
                    for fixture_id, count in multiple_analyses[:5]:  # Mostrar primeros 5
                        print(f"      Fixture {fixture_id}: {count} análisis")

                # Análisis recientes
                recent_analyses = session.query(AnalysisHistory).order_by(
                    AnalysisHistory.created_at.desc()
                ).limit(5).all()

                print(f"\n📅 Últimos 5 análisis:")
                for analysis in recent_analyses:
                    print(f"   Fixture {analysis.fixture_id} → {analysis.created_at}")

                # Verificar si se están reutilizando
                print(f"\n❓ ¿Se reutilizan los análisis guardados?")
                print("   Necesita verificación en el código del bot")
            else:
                print("\n⚠️  NO HAY ANÁLISIS GUARDADOS")
                print("   La tabla existe pero está vacía")
                print("   💡 El bot NO está guardando análisis")

            # ============================================================
            # 5. LIGAS ACTIVAS
            # ============================================================
            print("\n" + "="*80)
            print("  [5] LIGAS CONFIGURADAS")
            print("="*80)

            total_leagues = session.query(League).count()
            print(f"\n🏆 Total de ligas en BD: {total_leagues}")

            if total_leagues > 0:
                leagues = session.query(League).all()
                print("\n📋 Ligas disponibles:")
                for league in leagues:
                    print(f"   {league.id:4d} → {league.name:30s} ({league.country})")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # 6. RECOMENDACIONES
    # ============================================================
    print("\n" + "="*80)
    print("  [6] 💡 RECOMENDACIONES")
    print("="*80)

    print("\n🔧 Problemas detectados:")
    if total_fixtures == 0:
        print("   ❌ No hay partidos en BD - Cargar fixtures")
    if total_mappings < total_teams * 0.8:
        print("   ⚠️  Mapeo incompleto de FootyStats - Completar mapeos")
    print("   ❌ No hay cache de análisis - Implementar persistencia")

    print("\n✅ Acciones necesarias:")
    print("   1. Cargar partidos de la temporada completa")
    print("   2. Mapear TODOS los equipos a FootyStats")
    print("   3. Implementar cache de análisis en BD")
    print("   4. Implementar botón de 'refresh' manual")
    print("   5. Evitar llamadas API innecesarias")

    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    analyze_database()
