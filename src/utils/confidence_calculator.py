"""
Confidence Calculator - Calcula confianza de apuestas (1-5 estrellas)

FACTORES:
- Edge (50%)
- Datos FootyStats disponibles (30%)
- Diferencia de forma entre equipos (20%)
"""
from typing import Dict
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ConfidenceCalculator:
    """Calcula nivel de confianza para value bets"""

    @staticmethod
    def calculate(analysis: Dict) -> int:
        """
        Calcula confianza de 1 a 5 estrellas

        Args:
            analysis: Resultado del análisis completo

        Returns:
            Confianza (1-5 estrellas)

        Factores:
        - Edge (50%): Mayor edge = mayor confianza
        - FootyStats (30%): Datos disponibles + calidad alta
        - Forma (20%): Gran diferencia de forma entre equipos
        """
        score = 0.0

        # 1. Edge (peso 50% - máximo 2.5 puntos)
        edge = analysis.get('best_edge', 0)

        if edge >= 0.15:  # 15%+ edge
            score += 2.5
        elif edge >= 0.10:  # 10-15% edge
            score += 2.0
        elif edge >= 0.07:  # 7-10% edge
            score += 1.5
        elif edge >= 0.05:  # 5-7% edge
            score += 1.0

        # 2. FootyStats (peso 30% - máximo 1.5 puntos)
        footystats_data = analysis.get('footystats_analysis', {})

        if footystats_data:
            # Datos disponibles: +0.5
            score += 0.5

            # Calidad alta (>70): +1.0 adicional
            quality = footystats_data.get('quality_score', 0)
            if quality >= 70:
                score += 1.0
            elif quality >= 50:
                score += 0.5

        # 3. Diferencia de Forma (peso 20% - máximo 1.0 puntos)
        our_prediction = analysis.get('our_prediction', {})
        form_home = our_prediction.get('home_form_score', 50)
        form_away = our_prediction.get('away_form_score', 50)

        form_diff = abs(form_home - form_away)

        if form_diff > 30:  # Muy diferente
            score += 1.0
        elif form_diff > 15:  # Moderadamente diferente
            score += 0.5

        # Convertir a estrellas (1-5)
        stars = min(5, max(1, round(score)))

        logger.debug(
            f"Confidence calculation: edge={edge:.2%}, "
            f"footystats={'Yes' if footystats_data else 'No'}, "
            f"form_diff={form_diff:.1f} → {stars} stars"
        )

        return stars

    @staticmethod
    def get_confidence_label(stars: int) -> str:
        """
        Obtiene etiqueta textual de confianza

        Args:
            stars: Número de estrellas (1-5)

        Returns:
            Etiqueta descriptiva
        """
        labels = {
            5: "⭐⭐⭐⭐⭐ Muy Alta",
            4: "⭐⭐⭐⭐ Alta",
            3: "⭐⭐⭐ Media",
            2: "⭐⭐ Baja",
            1: "⭐ Muy Baja"
        }
        return labels.get(stars, "⭐ Muy Baja")

    @staticmethod
    def should_recommend(stars: int, min_stars: int = 3) -> bool:
        """
        Determina si se debe recomendar la apuesta

        Args:
            stars: Confianza calculada
            min_stars: Mínimo de estrellas para recomendar

        Returns:
            True si se debe recomendar
        """
        return stars >= min_stars
