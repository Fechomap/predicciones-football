"""
Country Service - Gestión de países y sus ligas

RESPONSABILIDAD:
- Agrupar ligas por país
- Top países por popularidad
- Mostrar ligas principales de cada país
"""
from typing import List, Dict
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class CountryService:
    """Servicio de gestión de países"""

    # Top países para fútbol (ordenados por popularidad)
    TOP_COUNTRIES = [
        {"name": "Mexico", "emoji": "🇲🇽", "priority": 1},       # PRIORITARIO
        {"name": "England", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "priority": 2},
        {"name": "Spain", "emoji": "🇪🇸", "priority": 3},
        {"name": "Italy", "emoji": "🇮🇹", "priority": 4},
        {"name": "Germany", "emoji": "🇩🇪", "priority": 5},
        {"name": "France", "emoji": "🇫🇷", "priority": 6},
        {"name": "Brazil", "emoji": "🇧🇷", "priority": 7},
        {"name": "Argentina", "emoji": "🇦🇷", "priority": 8},
        {"name": "Portugal", "emoji": "🇵🇹", "priority": 9},
        {"name": "Netherlands", "emoji": "🇳🇱", "priority": 10},
    ]

    # Ligas principales por país
    MAIN_LEAGUES_BY_COUNTRY = {
        "Mexico": [
            {"id": 262, "name": "Liga MX", "tier": 1},
            {"id": 723, "name": "Copa MX", "tier": 2},
        ],
        "England": [
            {"id": 39, "name": "Premier League", "tier": 1},
            {"id": 40, "name": "Championship", "tier": 2},
            {"id": 41, "name": "League One", "tier": 3},
            {"id": 42, "name": "League Two", "tier": 4},
            {"id": 2, "name": "Champions League", "tier": 1},  # Europa
        ],
        "Spain": [
            {"id": 140, "name": "La Liga", "tier": 1},
            {"id": 141, "name": "Segunda División", "tier": 2},
            {"id": 556, "name": "Copa del Rey", "tier": 2},
        ],
        "Italy": [
            {"id": 135, "name": "Serie A", "tier": 1},
            {"id": 136, "name": "Serie B", "tier": 2},
            {"id": 137, "name": "Coppa Italia", "tier": 2},
        ],
        "Germany": [
            {"id": 78, "name": "Bundesliga", "tier": 1},
            {"id": 79, "name": "2. Bundesliga", "tier": 2},
            {"id": 81, "name": "DFB Pokal", "tier": 2},
        ],
        "France": [
            {"id": 61, "name": "Ligue 1", "tier": 1},
            {"id": 62, "name": "Ligue 2", "tier": 2},
        ],
        "Brazil": [
            {"id": 71, "name": "Serie A", "tier": 1},
            {"id": 72, "name": "Serie B", "tier": 2},
        ],
        "Argentina": [
            {"id": 128, "name": "Liga Profesional", "tier": 1},
            {"id": 129, "name": "Primera B Nacional", "tier": 2},
        ],
        "Portugal": [
            {"id": 94, "name": "Primeira Liga", "tier": 1},
        ],
        "Netherlands": [
            {"id": 88, "name": "Eredivisie", "tier": 1},
        ],
        "Europe": [  # Competiciones internacionales
            {"id": 2, "name": "UEFA Champions League", "tier": 1},
            {"id": 3, "name": "UEFA Europa League", "tier": 2},
            {"id": 848, "name": "CONMEBOL Libertadores", "tier": 1},
        ]
    }

    @staticmethod
    def get_top_countries(limit: int = 10) -> List[Dict]:
        """Obtiene top países (México primero)"""
        return CountryService.TOP_COUNTRIES[:limit]

    @staticmethod
    def get_all_countries_paginated(page: int = 1, per_page: int = 10) -> Dict:
        """
        Obtiene países paginados

        Args:
            page: Número de página
            per_page: Países por página

        Returns:
            Dict con paginación
        """
        all_countries = CountryService.TOP_COUNTRIES

        total = len(all_countries)
        total_pages = (total + per_page - 1) // per_page

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        countries = all_countries[start_idx:end_idx]

        return {
            'countries': countries,
            'page': page,
            'total_pages': total_pages,
            'total': total,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }

    @staticmethod
    def get_leagues_by_country(country_name: str) -> List[Dict]:
        """
        Obtiene ligas de un país específico

        Args:
            country_name: Nombre del país

        Returns:
            Lista de ligas ordenadas por tier
        """
        leagues = CountryService.MAIN_LEAGUES_BY_COUNTRY.get(country_name, [])
        return sorted(leagues, key=lambda x: x['tier'])

    @staticmethod
    def get_country_info(country_name: str) -> Dict:
        """Obtiene info de un país"""
        for country in CountryService.TOP_COUNTRIES:
            if country['name'] == country_name:
                return country
        return {"name": country_name, "emoji": "🌍", "priority": 99}
