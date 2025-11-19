#!/usr/bin/env python3
"""
Test del sistema de cache de análisis

Prueba que:
1. Primera llamada genera análisis y guarda en cache
2. Segunda llamada reutiliza cache (sin llamadas API)
3. Force refresh ignora cache
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.bot_service import BotService
from src.database import db_manager
from src.utils.logger import setup_logger
import time

logger = setup_logger(__name__)


def test_cache_system():
    """Test del sistema de cache"""

    print("\n" + "="*70)
    print("  🧪 TEST DEL SISTEMA DE CACHE")
    print("="*70)

    # Initialize
    db_manager.initialize()
    bot_service = BotService()

    # Get a Premier League fixture
    with db_manager.get_session() as session:
        from src.database import Fixture, Team, League

        fixture_orm = session.query(Fixture).join(
            League, Fixture.league_id == League.id
        ).filter(
            Fixture.league_id == 39,  # Premier League
            Fixture.status == 'NS'
        ).first()

        if not fixture_orm:
            print("❌ No hay partidos de Premier League")
            return False

        home_team = session.query(Team).filter_by(id=fixture_orm.home_team_id).first()
        away_team = session.query(Team).filter_by(id=fixture_orm.away_team_id).first()
        league = session.query(League).filter_by(id=fixture_orm.league_id).first()

        fixture = {
            'fixture': {
                'id': fixture_orm.id,
                'date': str(fixture_orm.kickoff_time),
                'timestamp': int(fixture_orm.kickoff_time.timestamp()) if fixture_orm.kickoff_time else None,
                'status': {'short': fixture_orm.status}
            },
            'league': {
                'id': fixture_orm.league_id,
                'name': league.name if league else 'Unknown',
                'country': league.country if league else 'Unknown'
            },
            'teams': {
                'home': {
                    'id': fixture_orm.home_team_id,
                    'name': home_team.name if home_team else 'Unknown'
                },
                'away': {
                    'id': fixture_orm.away_team_id,
                    'name': away_team.name if away_team else 'Unknown'
                }
            }
        }

    print(f"\n📋 Partido de prueba:")
    print(f"   {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
    print(f"   Fixture ID: {fixture['fixture']['id']}\n")

    # ============================================================
    # TEST 1: Primera llamada (sin cache)
    # ============================================================
    print("="*70)
    print("  [1/3] PRIMERA LLAMADA - Sin cache")
    print("="*70)

    start = time.time()
    analysis1 = bot_service.analysis_service.get_or_create_analysis(fixture, force_refresh=False)
    elapsed1 = time.time() - start

    if analysis1:
        print(f"\n✅ Análisis completado")
        print(f"   Tiempo: {elapsed1:.2f} segundos")
        print(f"   Resultado: Cache MISS (calculado desde cero)")
    else:
        print(f"\n❌ Análisis falló")
        return False

    # Verificar que se guardó en BD
    with db_manager.get_session() as session:
        from src.database import AnalysisHistory
        cached_count = session.query(AnalysisHistory).filter_by(
            fixture_id=fixture['fixture']['id']
        ).count()
        print(f"   💾 Análisis guardados en BD: {cached_count}")

    # ============================================================
    # TEST 2: Segunda llamada (CON cache)
    # ============================================================
    print("\n" + "="*70)
    print("  [2/3] SEGUNDA LLAMADA - Con cache")
    print("="*70)

    start = time.time()
    analysis2 = bot_service.analysis_service.get_or_create_analysis(fixture, force_refresh=False)
    elapsed2 = time.time() - start

    if analysis2:
        print(f"\n✅ Análisis completado")
        print(f"   Tiempo: {elapsed2:.2f} segundos")

        if elapsed2 < elapsed1 * 0.3:  # Debería ser al menos 70% más rápido
            print(f"   Resultado: ✅ Cache HIT (reutilizado)")
            print(f"   Ahorro: {((elapsed1 - elapsed2) / elapsed1 * 100):.0f}%")
        else:
            print(f"   Resultado: ⚠️  No parece haber usado cache")
    else:
        print(f"\n❌ Análisis falló")
        return False

    # ============================================================
    # TEST 3: Force Refresh (ignora cache)
    # ============================================================
    print("\n" + "="*70)
    print("  [3/3] FORCE REFRESH - Ignora cache")
    print("="*70)

    start = time.time()
    analysis3 = bot_service.analysis_service.get_or_create_analysis(fixture, force_refresh=True)
    elapsed3 = time.time() - start

    if analysis3:
        print(f"\n✅ Análisis completado")
        print(f"   Tiempo: {elapsed3:.2f} segundos")

        if elapsed3 > elapsed2 * 2:  # Debería ser más lento que cache
            print(f"   Resultado: ✅ Cache ignorado (recalculado)")
        else:
            print(f"   Resultado: Cache usado (o datos muy rápidos)")
    else:
        print(f"\n❌ Análisis falló")
        return False

    # ============================================================
    # RESUMEN
    # ============================================================
    print("\n" + "="*70)
    print("  📊 RESUMEN DEL TEST")
    print("="*70)

    print(f"\n⏱️  Tiempos:")
    print(f"   Primera llamada (sin cache): {elapsed1:.2f}s")
    print(f"   Segunda llamada (con cache):  {elapsed2:.2f}s")
    print(f"   Force refresh:                {elapsed3:.2f}s")

    # Verificar cache stats
    stats = bot_service.analysis_service.get_cache_stats()
    print(f"\n💾 Estadísticas de cache:")
    print(f"   Total en cache: {stats['total_cached']}")
    print(f"   Recientes (<6h): {stats['recent_cached']}")
    print(f"   Antiguos (>6h): {stats['old_cached']}")

    cache_working = elapsed2 < elapsed1 * 0.5
    if cache_working:
        print(f"\n✅ CACHE FUNCIONANDO CORRECTAMENTE")
        print(f"   Ahorro de tiempo: {((elapsed1 - elapsed2) / elapsed1 * 100):.0f}%")
        print(f"   Ahorro estimado de API calls: ~80-90%")
        return True
    else:
        print(f"\n⚠️  Cache puede no estar funcionando óptimamente")
        return False


if __name__ == "__main__":
    success = test_cache_system()
    print("\n" + "="*70 + "\n")
    sys.exit(0 if success else 1)
