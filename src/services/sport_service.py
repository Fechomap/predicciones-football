"""
Sport Service - Gestión de deportes multi-deporte

RESPONSABILIDAD:
- Obtener TODOS los deportes disponibles en API-Football
- Paginación de deportes (10 en 10)
- Top 10 deportes por popularidad
- Cache en BD para evitar llamadas API innecesarias
"""
from typing import List, Dict, Optional
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class SportService:
    """Servicio de gestión de deportes"""

    # Top 10 deportes por popularidad mundial
    TOP_SPORTS = [
        {"id": 1, "name": "⚽ Football", "key": "football"},
        {"id": 2, "name": "🏀 Basketball", "key": "basketball"},
        {"id": 3, "name": "🏈 American Football", "key": "american-football"},
        {"id": 4, "name": "⚾ Baseball", "key": "baseball"},
        {"id": 5, "name": "🎾 Tennis", "key": "tennis"},
        {"id": 6, "name": "🏒 Ice Hockey", "key": "hockey"},
        {"id": 7, "name": "🏐 Volleyball", "key": "volleyball"},
        {"id": 8, "name": "🏉 Rugby", "key": "rugby"},
        {"id": 9, "name": "🏏 Cricket", "key": "cricket"},
        {"id": 10, "name": "🥊 Boxing", "key": "boxing"}
    ]

    def __init__(self, api_client=None):
        """
        Inicializa el servicio

        Args:
            api_client: Cliente de API-Football (opcional)
        """
        self.api_client = api_client

    @staticmethod
    def get_top_sports(limit: int = 10) -> List[Dict]:
        """
        Obtiene los deportes más populares

        Args:
            limit: Número de deportes a devolver (default: 10)

        Returns:
            Lista de deportes top
        """
        return SportService.TOP_SPORTS[:limit]

    @staticmethod
    def get_all_sports_paginated(page: int = 1, per_page: int = 10) -> Dict:
        """
        Obtiene deportes paginados

        Args:
            page: Número de página (1-indexed)
            per_page: Deportes por página

        Returns:
            Dict con 'sports', 'page', 'total_pages', 'has_next', 'has_prev'
        """
        all_sports = SportService.TOP_SPORTS  # TODO: Obtener de API si necesario

        # Calcular paginación
        total = len(all_sports)
        total_pages = (total + per_page - 1) // per_page

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        sports = all_sports[start_idx:end_idx]

        return {
            'sports': sports,
            'page': page,
            'total_pages': total_pages,
            'total_sports': total,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }

    @staticmethod
    def get_sport_by_id(sport_id: int) -> Optional[Dict]:
        """
        Obtiene información de un deporte específico

        Args:
            sport_id: ID del deporte

        Returns:
            Dict con info del deporte o None
        """
        for sport in SportService.TOP_SPORTS:
            if sport['id'] == sport_id:
                return sport
        return None

    @staticmethod
    def is_football(sport_id: int) -> bool:
        """
        Verifica si el deporte es fútbol

        Args:
            sport_id: ID del deporte

        Returns:
            True si es fútbol
        """
        return sport_id == 1
