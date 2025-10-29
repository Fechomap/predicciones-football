"""Telegram message formatter"""
from datetime import datetime
from typing import Dict

from ..utils.config import LEAGUE_CONFIG


class MessageFormatter:
    """Formats betting analysis messages for Telegram"""

    @staticmethod
    def format_value_bet_alert(
        fixture: Dict,
        analysis: Dict,
        value_bet: Dict
    ) -> str:
        """
        Format value bet alert message

        Args:
            fixture: Fixture data
            analysis: Statistical analysis
            value_bet: Value bet detection data

        Returns:
            Formatted message string
        """
        # Extract fixture info
        fixture_data = fixture.get("fixture", {})
        teams = fixture.get("teams", {})
        league = fixture.get("league", {})

        home_team = teams.get("home", {}).get("name", "Unknown")
        away_team = teams.get("away", {}).get("name", "Unknown")
        venue = fixture_data.get("venue", {}).get("name", "")

        # Get kickoff time
        kickoff_timestamp = fixture_data.get("timestamp", 0)
        kickoff_time = datetime.fromtimestamp(kickoff_timestamp)
        time_until = kickoff_time - datetime.now()
        minutes_until = int(time_until.total_seconds() / 60)

        # Get league info
        league_id = league.get("id")
        league_info = LEAGUE_CONFIG.get(league_id, {})
        league_emoji = league_info.get("emoji", "⚽")
        league_name = league.get("name", "Unknown League")

        # Extract analysis data
        home_prob = analysis.get("home_probability", 0)
        draw_prob = analysis.get("draw_probability", 0)
        away_prob = analysis.get("away_probability", 0)
        expected_home_goals = analysis.get("expected_home_goals", 0)
        expected_away_goals = analysis.get("expected_away_goals", 0)
        confidence = analysis.get("confidence", 3)

        # Extract value bet data
        outcome = value_bet.get("outcome", "Home")
        calc_prob = value_bet.get("calculated_probability", 0)
        odds = value_bet.get("bookmaker_odds", 0)
        edge = value_bet.get("edge", 0)
        implied_prob = value_bet.get("implied_probability", 0)
        suggested_stake = value_bet.get("suggested_stake", 3)

        # Form analysis
        home_form = analysis.get("home_form", {})
        away_form = analysis.get("away_form", {})

        # Build message
        message = f"""⚽ <b>OPORTUNIDAD DETECTADA</b>

{league_emoji} <b>Liga:</b> {league_name}
📅 <b>Partido:</b> {home_team} vs {away_team}
🕐 <b>Inicio:</b> {kickoff_time.strftime('%d/%m/%Y %H:%M')} hrs
⏰ <b>En:</b> {minutes_until} minutos
🏟️ <b>Estadio:</b> {venue}

━━━━━━━━━━━━━━━━━━━━━━

📊 <b>ANÁLISIS ESTADÍSTICO</b>

<b>Resultado recomendado:</b> {MessageFormatter._translate_outcome(outcome)} ({outcome})

🎯 <b>Probabilidades:</b>
• Calculada: {calc_prob:.1f}%
• Casa de apuestas: {odds} (prob. implícita: {implied_prob:.1f}%)
• <b>Value Edge: +{edge:.1f}%</b>

📈 <b>Probabilidades del partido:</b>
• Local: {home_prob:.1f}%
• Empate: {draw_prob:.1f}%
• Visitante: {away_prob:.1f}%

⚽ <b>Goles esperados:</b>
• {home_team}: {expected_home_goals:.2f}
• {away_team}: {expected_away_goals:.2f}

🔥 <b>Forma reciente (últimos 5):</b>
• {home_team}: {home_form.get('form_string', 'N/A')} ({home_form.get('points', 0)} pts)
• {away_team}: {away_form.get('form_string', 'N/A')} ({away_form.get('points', 0)} pts)

━━━━━━━━━━━━━━━━━━━━━━

💰 <b>RECOMENDACIÓN</b>

• Confianza: {'⭐' * confidence} ({confidence}/5)
• Stake sugerido: {suggested_stake}% del bankroll
• Expected Value: +{value_bet.get('expected_value', 0):.2f}%

⚠️ <i>Disclaimer: Análisis estadístico basado en datos históricos. Apuesta responsable.</i>
"""

        return message

    @staticmethod
    def _translate_outcome(outcome: str) -> str:
        """Translate outcome to Spanish"""
        translations = {
            "Home": "Victoria Local",
            "Draw": "Empate",
            "Away": "Victoria Visitante",
            "Over": "Más de",
            "Under": "Menos de",
            "BTTS": "Ambos anotan"
        }
        return translations.get(outcome, outcome)

    @staticmethod
    def format_daily_summary(
        opportunities_count: int,
        best_value: Dict = None
    ) -> str:
        """
        Format daily summary message

        Args:
            opportunities_count: Number of opportunities found today
            best_value: Best value bet of the day

        Returns:
            Formatted summary message
        """
        message = f"""📊 <b>RESUMEN DIARIO</b>

🎯 Oportunidades detectadas hoy: {opportunities_count}
"""

        if best_value:
            message += f"""
🏆 <b>Mejor oportunidad:</b>
• {best_value.get('match', 'N/A')}
• Edge: +{best_value.get('edge', 0):.1f}%
• Cuota: {best_value.get('odds', 0)}
"""

        return message

    @staticmethod
    def format_error_message(error: str) -> str:
        """
        Format error message

        Args:
            error: Error description

        Returns:
            Formatted error message
        """
        return f"""❌ <b>ERROR</b>

Se ha producido un error:
{error}

El bot seguirá funcionando normalmente.
"""

    @staticmethod
    def format_startup_message() -> str:
        """Format bot startup message"""
        return """🤖 <b>BOT INICIADO</b>

El bot de análisis de apuestas está activo y monitoreando partidos.

Recibirás alertas cuando se detecten oportunidades de value bets.

⚽ ¡Buena suerte!
"""
