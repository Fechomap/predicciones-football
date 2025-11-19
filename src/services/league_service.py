"""
League Service - Gestión de ligas por deporte

RESPONSABILIDAD:
- Obtener ligas disponibles por deporte
- Top 10 ligas (con Liga MX prioritaria para fútbol)
- Paginación de ligas
"""
from typing import List, Dict, Optional
from ..database import db_manager, League
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class LeagueService:
    """Servicio de gestión de ligas"""

    # Top 10 ligas de FÚTBOL (orden de prioridad)
    FOOTBALL_TOP_LEAGUES = [
        {"id": 262, "name": "Liga MX", "country": "Mexico", "priority": 1},          # ⭐ PRIORITARIA
        {"id": 39, "name": "Premier League", "country": "England", "priority": 2},
        {"id": 140, "name": "La Liga", "country": "Spain", "priority": 3},
        {"id": 135, "name": "Serie A", "country": "Italy", "priority": 4},
        {"id": 78, "name": "Bundesliga", "country": "Germany", "priority": 5},
        {"id": 61, "name": "Ligue 1", "country": "France", "priority": 6},
        {"id": 2, "name": "UEFA Champions League", "country": "Europe", "priority": 7},
        {"id": 3, "name": "UEFA Europa League", "country": "Europe", "priority": 8},
        {"id": 848, "name": "CONMEBOL Libertadores", "country": "South America", "priority": 9},
        {"id": 128, "name": "Liga Profesional Argentina", "country": "Argentina", "priority": 10},
    ]

    def __init__(self, api_client=None):
        """
        Inicializa el servicio

        Args:
            api_client: Cliente de API-Football (opcional)
        """
        self.api_client = api_client

    @staticmethod
    def get_top_leagues_for_football(limit: int = 10) -> List[Dict]:
        """
        Obtiene top ligas de fútbol (Liga MX first)

        Args:
            limit: Número de ligas (default: 10)

        Returns:
            Lista de top ligas ordenadas por prioridad
        """
        return LeagueService.FOOTBALL_TOP_LEAGUES[:limit]

    @staticmethod
    def get_all_football_leagues_paginated(page: int = 1, per_page: int = 10) -> Dict:
        """
        Obtiene todas las ligas de fútbol paginadas

        Args:
            page: Número de página
            per_page: Ligas por página

        Returns:
            Dict con paginación
        """
        # Obtener todas las ligas de BD
        with db_manager.get_session() as session:
            all_leagues = session.query(League).order_by(League.name).all()

            total = len(all_leagues)
            total_pages = (total + per_page - 1) // per_page

            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page

            leagues_page = all_leagues[start_idx:end_idx]

            return {
                'leagues': [
                    {
                        'id': league.id,
                        'name': league.name,
                        'country': league.country,
                        'enabled': league.enabled
                    }
                    for league in leagues_page
                ],
                'page': page,
                'total_pages': total_pages,
                'total_leagues': total,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }

    @staticmethod
    def get_league_by_id(league_id: int) -> Optional[Dict]:
        """
        Obtiene información de una liga específica

        Args:
            league_id: ID de la liga

        Returns:
            Dict con info de la liga o None
        """
        with db_manager.get_session() as session:
            league = session.query(League).filter_by(id=league_id).first()

            if league:
                return {
                    'id': league.id,
                    'name': league.name,
                    'country': league.country,
                    'enabled': league.enabled
                }

        return None

    @staticmethod
    def get_enabled_leagues() -> List[Dict]:
        """
        Obtiene solo las ligas habilitadas

        Returns:
            Lista de ligas habilitadas
        """
        with db_manager.get_session() as session:
            leagues = session.query(League).filter_by(enabled=True).all()

            return [
                {
                    'id': league.id,
                    'name': league.name,
                    'country': league.country
                }
                for league in leagues
            ]
