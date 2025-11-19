"""
Analysis Service - Orquestación de análisis con cache inteligente

RESPONSABILIDAD:
- Orquestar análisis de fixtures
- Gestionar cache de análisis (reutilizar <6 horas)
- Evitar llamadas API innecesarias
- Permitir al usuario forzar refresh
"""
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from sqlalchemy import and_

from ..database import db_manager, AnalysisHistory, Fixture
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class AnalysisService:
    """
    Servicio centralizado para análisis con cache inteligente

    Patrón: Cache-Aside
    - Busca en cache primero
    - Si no existe o está viejo, calcula nuevo
    - Guarda resultado en cache
    """

    CACHE_DURATION_HOURS = 6  # Reutilizar análisis <6 horas

    def __init__(self, bot_service):
        """
        Inicializa el servicio de análisis

        Args:
            bot_service: Instancia de BotService (para cálculos)
        """
        self.bot_service = bot_service

    def get_or_create_analysis(
        self,
        fixture: Dict,
        force_refresh: bool = False
    ) -> Optional[Dict]:
        """
        Obtiene análisis de cache o crea uno nuevo

        FLUJO:
        1. Si force_refresh=False: Buscar en cache
        2. Si existe y es reciente (<6h): Devolver
        3. Si no existe o viejo o force_refresh=True: Calcular nuevo
        4. Guardar en cache
        5. Devolver resultado

        Args:
            fixture: Datos del partido
            force_refresh: Si True, ignora cache y llama API

        Returns:
            Análisis completo o None si falla
        """
        fixture_id = fixture.get("fixture", {}).get("id")

        if not fixture_id:
            logger.error("Fixture ID is None, cannot analyze")
            return None

        # 1. Buscar en cache (si no es force refresh)
        if not force_refresh:
            cached = self._get_cached_analysis(fixture_id)

            if cached:
                logger.info(f"✅ Cache HIT: fixture {fixture_id} (reutilizando análisis)")
                return cached

        # 2. Cache miss o force refresh - calcular nuevo
        logger.info(
            f"{'🔄 Force REFRESH' if force_refresh else '❌ Cache MISS'}: "
            f"fixture {fixture_id} - Calculando análisis (llamadas API)"
        )

        analysis = self.bot_service.analyze_fixture(fixture)

        if not analysis:
            logger.warning(f"Analysis failed for fixture {fixture_id}")
            return None

        # 3. Guardar en cache
        self._save_to_cache(fixture_id, analysis)

        return analysis

    def _get_cached_analysis(self, fixture_id: int) -> Optional[Dict]:
        """
        Busca análisis reciente en cache (<6 horas)

        Args:
            fixture_id: ID del fixture

        Returns:
            Análisis si existe y es reciente, None si no
        """
        cutoff_time = datetime.now() - timedelta(hours=self.CACHE_DURATION_HOURS)

        with db_manager.get_session() as session:
            cached = session.query(AnalysisHistory).filter(
                and_(
                    AnalysisHistory.fixture_id == fixture_id,
                    AnalysisHistory.created_at >= cutoff_time
                )
            ).order_by(AnalysisHistory.created_at.desc()).first()

            if cached:
                age_hours = (datetime.now() - cached.created_at).total_seconds() / 3600
                logger.debug(
                    f"Cache found for fixture {fixture_id} "
                    f"(age: {age_hours:.1f}h, PDF: {cached.pdf_url or 'N/A'})"
                )
                return json.loads(cached.analysis_data)

        return None

    def _save_to_cache(self, fixture_id: int, analysis: Dict):
        """
        Guarda análisis en cache

        Args:
            fixture_id: ID del fixture
            analysis: Datos del análisis
        """
        try:
            with db_manager.get_session() as session:
                # Convertir numpy types a Python natives (para PostgreSQL)
                def to_python_type(value):
                    """Convierte numpy.float64 a float de Python"""
                    if hasattr(value, 'item'):  # numpy type
                        return value.item()
                    return value

                our_pred = analysis.get('our_prediction', {})

                # Crear registro de análisis
                record = AnalysisHistory(
                    fixture_id=fixture_id,
                    analysis_data=json.dumps(analysis),
                    pdf_url=analysis.get('pdf_url'),
                    confidence_score=to_python_type(analysis.get('confidence_rating', 0)),
                    home_probability=to_python_type(our_pred.get('home', 0)),
                    draw_probability=to_python_type(our_pred.get('draw', 0)),
                    away_probability=to_python_type(our_pred.get('away', 0))
                )
                session.add(record)
                session.commit()

                logger.info(f"💾 Analysis saved to cache for fixture {fixture_id}")

        except Exception as e:
            logger.error(f"Failed to save analysis to cache: {e}")
            # No falla el análisis si no se puede guardar en cache

    def invalidate_cache(self, fixture_id: int):
        """
        Invalida (elimina) cache para un fixture

        Útil cuando el usuario quiere forzar actualización

        Args:
            fixture_id: ID del fixture
        """
        try:
            with db_manager.get_session() as session:
                deleted = session.query(AnalysisHistory).filter(
                    AnalysisHistory.fixture_id == fixture_id
                ).delete()

                session.commit()

                if deleted > 0:
                    logger.info(f"🗑️  Cache invalidated for fixture {fixture_id} ({deleted} records)")
                else:
                    logger.debug(f"No cache to invalidate for fixture {fixture_id}")

        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")

    def get_cache_stats(self) -> Dict:
        """
        Obtiene estadísticas del cache

        Returns:
            Dict con stats: total_cached, cache_hit_rate, etc.
        """
        with db_manager.get_session() as session:
            total = session.query(AnalysisHistory).count()

            # Análisis recientes (<6 horas)
            cutoff = datetime.now() - timedelta(hours=self.CACHE_DURATION_HOURS)
            recent = session.query(AnalysisHistory).filter(
                AnalysisHistory.created_at >= cutoff
            ).count()

            # Análisis viejos (>6 horas)
            old = total - recent

            return {
                'total_cached': total,
                'recent_cached': recent,
                'old_cached': old,
                'cache_duration_hours': self.CACHE_DURATION_HOURS
            }

    def analyze_full_league_week(
        self,
        league_id: int,
        force_refresh: bool = False
    ) -> Optional[Dict]:
        """
        Analiza TODOS los partidos de la semana de una liga

        IMPORTANTE: Genera PDF con resumen completo

        Args:
            league_id: ID de la liga
            force_refresh: Si True, ignora cache para todos los partidos

        Returns:
            Dict con 'pdf_path', 'results', 'summary'
        """
        from .fixtures_service import FixturesService
        from ..utils.confidence_calculator import ConfidenceCalculator
        from .pdf_service import PDFService

        logger.info(f"📊 Analizando liga completa: {league_id} (force_refresh={force_refresh})")

        # Obtener partidos de la semana
        fixtures_service = FixturesService(self.bot_service.data_collector)
        fixtures = fixtures_service.get_weekly_fixtures(league_id)

        if not fixtures:
            logger.warning(f"No fixtures found for league {league_id}")
            return None

        logger.info(f"📅 Analizando {len(fixtures)} partidos de la semana")

        # Analizar cada partido
        results = []
        for fixture in fixtures:
            try:
                # Analizar (con cache)
                analysis = self.get_or_create_analysis(fixture, force_refresh=force_refresh)

                if analysis:
                    # Calcular confianza
                    confidence = ConfidenceCalculator.calculate(analysis)

                    results.append({
                        'fixture': fixture,
                        'analysis': analysis,
                        'confidence': confidence
                    })
            except Exception as e:
                logger.error(f"Error analyzing fixture {fixture.get('fixture', {}).get('id')}: {e}")
                continue

        # Ordenar por confianza (mayor a menor)
        results.sort(key=lambda x: x['confidence'], reverse=True)

        # Generar PDF
        league_info = fixtures[0].get('league', {}) if fixtures else {}
        league_name = league_info.get('name', f'League {league_id}')

        pdf_path = PDFService.generate_league_weekly_report(league_name, results)

        return {
            'league_id': league_id,
            'league_name': league_name,
            'total_fixtures': len(results),
            'pdf_path': pdf_path,
            'results': results,
            'top_3': results[:3],  # Top 3 para botones
            'summary': {
                'high_confidence': sum(1 for r in results if r['confidence'] >= 4),
                'medium_confidence': sum(1 for r in results if r['confidence'] == 3),
                'low_confidence': sum(1 for r in results if r['confidence'] <= 2)
            }
        }
