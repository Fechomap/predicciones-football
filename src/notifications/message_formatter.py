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

        # Goal ranges analysis
        goal_ranges = analysis.get("goal_ranges", {})

        # Build message
        message = f"""⚽ <b>OPORTUNIDAD DETECTADA</b>

{league_emoji} <b>Liga:</b> {league_name}
📅 <b>Partido:</b> {home_team} vs {away_team}
🕐 <b>Inicio:</b> {kickoff_time.strftime('%d/%m/%Y %H:%M')} hrs
⏰ <b>En:</b> {minutes_until} minutos
🏟️ <b>Estadio:</b> {venue}

━━━━━━━━━━━━━━━━━━━━━━

📊 <b>ANÁLISIS ESTADÍSTICO</b>
<i>(La recomendación de valor se basa en nuestra predicción Poisson)</i>

<b>Resultado recomendado:</b> {MessageFormatter._translate_outcome(outcome)} ({outcome})

🎯 <b>Probabilidades:</b>
• Calculada (Poisson): {calc_prob:.1f}%
• Casa de apuestas: {odds} (prob. implícita: {implied_prob:.1f}%)
• <b>Value Edge: +{edge:.1f}%</b>

📈 <b>Probabilidades del partido (Poisson):</b>
• Local: {home_prob:.1f}%
• Empate: {draw_prob:.1f}%
• Visitante: {away_prob:.1f}%

⚽ <b>Goles esperados:</b>
• {home_team}: {expected_home_goals:.2f}
• {away_team}: {expected_away_goals:.2f}

🥅 <b>Probabilidad de Goles Totales:</b>
• 0-1 Goles: {goal_ranges.get('0-1', 0) * 100:.1f}%
• 2-3 Goles: {goal_ranges.get('2-3', 0) * 100:.1f}%
• 4+ Goles: {goal_ranges.get('4+', 0) * 100:.1f}%

🔥 <b>Forma reciente (últimos 5):</b>
• {home_team}: {MessageFormatter._format_form_string(home_form.get('form_string', 'N/A'))} ({home_form.get('points', 0)} pts)
• {away_team}: {MessageFormatter._format_form_string(away_form.get('form_string', 'N/A'))} ({away_form.get('points', 0)} pts)
"""

        # Add FootyStats enhanced metrics if available (only if valid data)
        footystats = analysis.get("footystats")
        if footystats and footystats.get('quality_score', 0) > 0:
            quality_score = footystats.get('quality_score', 0)
            btts_prob = footystats.get('btts_probability', 0) * 100
            over_25_prob = footystats.get('over_25_probability', 0) * 100
            intensity = footystats.get('match_intensity', 'medium')

            intensity_emoji = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🔴'
            }.get(intensity, '⚪')

            message += f"""
📊 <b>DATOS MEJORADOS (FootyStats):</b>
• Calidad del partido: {quality_score:.0f}/100
• BTTS Probabilidad: {btts_prob:.1f}%
• Over 2.5 Probabilidad: {over_25_prob:.1f}%
• Intensidad: {intensity_emoji} {intensity.capitalize()}
"""

        message += f"""
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
    def _format_form_string(form_string: str) -> str:
        """
        Convert form string to emoji representation

        Args:
            form_string: Form string (e.g., "WLDWW" or "N/A")

        Returns:
            Form string with emojis (e.g., "✅❌🟨✅✅")
        """
        if not form_string or form_string == "N/A":
            return "N/A"

        # Replace W, D, L with emojis
        emoji_form = form_string.replace('W', '✅').replace('D', '🟨').replace('L', '❌')
        return emoji_form

    @staticmethod
    def format_apifootball_analysis(analysis: Dict) -> str:
        """Format API-Football analysis message"""
        teams = analysis.get("teams", {})
        fixture_info = analysis.get("fixture_info", {})
        league = analysis.get("league", {})
        predictions = analysis.get("predictions", {})
        percent = analysis.get("percent", {})

        home_team = teams.get("home", {}).get("name", "Unknown")
        away_team = teams.get("away", {}).get("name", "Unknown")
        league_name = league.get("name", "Unknown")
        date_str = fixture_info.get("date", "")[:16].replace("T", " ")

        home_pct = float(str(percent.get('home', '0')).rstrip('%')) if percent.get('home') else 0
        draw_pct = float(str(percent.get('draw', '0')).rstrip('%')) if percent.get('draw') else 0
        away_pct = float(str(percent.get('away', '0')).rstrip('%')) if percent.get('away') else 0

        winner = predictions.get("winner", {}).get("name", "N/A")
        advice = predictions.get("advice", "N/A")

        return f"""
🤖 <b>PREDICCIÓN API-FOOTBALL (AI)</b>

🏆 {league_name}
📅 {home_team} vs {away_team}
🕐 {date_str}

━━━━━━━━━━━━━━━━━━━━━━

📊 <b>PROBABILIDADES AI</b>
• Local (1): {home_pct:.1f}%
• Empate (X): {draw_pct:.1f}%
• Visitante (2): {away_pct:.1f}%

🎯 <b>RECOMENDACIÓN</b>
• Ganador sugerido: {winner}
• Consejo: {advice}

⚠️ <i>Predicción basada en AI de API-Football</i>
"""

    @staticmethod
    def format_poisson_analysis(analysis: Dict) -> str:
        """Format Poisson analysis message"""
        teams = analysis.get("teams", {})
        fixture_info = analysis.get("fixture_info", {})
        league = analysis.get("league", {})
        probabilities = analysis.get("probabilities", {})
        expected_goals = analysis.get("expected_goals", {})
        goal_ranges = analysis.get("goal_ranges", {})
        best_odds = analysis.get("best_odds", {})

        home_team = teams.get("home", {}).get("name", "Unknown")
        away_team = teams.get("away", {}).get("name", "Unknown")
        league_name = league.get("name", "Unknown")
        date_str = fixture_info.get("date", "")[:16].replace("T", " ")

        home_prob = probabilities.get("home_win", 0)
        draw_prob = probabilities.get("draw", 0)
        away_prob = probabilities.get("away_win", 0)

        message = f"""
🧮 <b>ANÁLISIS POISSON (Modelo Matemático)</b>

🏆 {league_name}
📅 {home_team} vs {away_team}
🕐 {date_str}

━━━━━━━━━━━━━━━━━━━━━━

📊 <b>PROBABILIDADES CALCULADAS</b>
• Local (1): {home_prob*100:.1f}%
• Empate (X): {draw_prob*100:.1f}%
• Visitante (2): {away_prob*100:.1f}%

⚽ <b>GOLES ESPERADOS</b>
• {home_team}: {expected_goals.get('home', 0):.2f}
• {away_team}: {expected_goals.get('away', 0):.2f}

🥅 <b>PROBABILIDAD DE GOLES TOTALES</b>
• 0-1 Goles: {goal_ranges.get('0-1', 0) * 100:.1f}%
• 2-3 Goles: {goal_ranges.get('2-3', 0) * 100:.1f}%
• 4+ Goles: {goal_ranges.get('4+', 0) * 100:.1f}%
"""

        if analysis.get("has_odds") and best_odds:
            message += f"""
━━━━━━━━━━━━━━━━━━━━━━

💰 <b>CUOTAS DISPONIBLES</b>
• Local: {best_odds.get('Home', 'N/A')}
• Empate: {best_odds.get('Draw', 'N/A')}
• Visitante: {best_odds.get('Away', 'N/A')}
"""

        message += "\n⚠️ <i>Predicción basada en distribución de Poisson</i>"
        return message

    @staticmethod
    def format_footystats_analysis(analysis: Dict) -> str:
        """Format FootyStats analysis message"""
        if not analysis.get("available"):
            return f"""
📈 <b>ANÁLISIS FOOTYSTATS</b>

❌ {analysis.get('message', 'Datos no disponibles')}

💡 <i>FootyStats requiere mapeo de IDs de equipos.
Algunos equipos pueden no estar disponibles aún.</i>
"""

        teams = analysis.get("teams", {})
        fixture_info = analysis.get("fixture_info", {})
        league = analysis.get("league", {})
        fs_data = analysis.get("analysis", {})

        home_team = teams.get("home", {}).get("name", "Unknown")
        away_team = teams.get("away", {}).get("name", "Unknown")
        league_name = league.get("name", "Unknown")
        date_str = fixture_info.get("date", "")[:16].replace("T", " ")

        quality_score = fs_data.get('quality_score', 0)
        btts_prob = fs_data.get('btts_probability', 0) * 100
        over_25_prob = fs_data.get('over_25_probability', 0) * 100
        intensity = fs_data.get('match_intensity', 'medium')
        home_stats = fs_data.get('home_stats', {})
        away_stats = fs_data.get('away_stats', {})

        intensity_emoji = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🔴'
        }.get(intensity, '⚪')

        return f"""
📈 <b>DATOS HISTÓRICOS DE LA TEMPORADA</b>

🏆 {league_name}
📅 {home_team} vs {away_team}
🕐 {date_str}

━━━━━━━━━━━━━━━━━━━━━━

📊 <b>CALIDAD ESPERADA DEL PARTIDO</b>
• Calificación: {quality_score:.0f}/100 {'🔥' if quality_score >= 70 else '⚽' if quality_score >= 50 else '😴'}
• Ritmo del juego: {intensity_emoji} {intensity.capitalize()}

⚽ <b>PROBABILIDADES DE GOLES</b>
• Ambos equipos anoten: {btts_prob:.1f}%
• Más de 2.5 goles (3+): {over_25_prob:.1f}%

━━━━━━━━━━━━━━━━━━━━━━

📊 <b>¿CÓMO JUEGA {home_team.upper()}?</b>
• Mete goles (promedio): {home_stats.get('avg_goals_scored', 0):.2f} por partido
• Le meten goles (promedio): {home_stats.get('avg_goals_conceded', 0):.2f} por partido
• Tiros de esquina (promedio): {home_stats.get('avg_corners', 0):.1f} por partido
• Tiros al arco (promedio): {home_stats.get('avg_shots_on_target', 0):.1f} por partido
• Posesión (promedio): {home_stats.get('avg_possession', 0):.1f}%
• Ambos anotan: {home_stats.get('btts_percentage', 0):.1f}% de sus partidos
• +3 goles total: {home_stats.get('over_25_percentage', 0):.1f}% de sus partidos
• Rendimiento: {home_stats.get('ppg', 0):.2f} pts/juego {'🔥' if home_stats.get('ppg', 0) >= 2 else '⚽' if home_stats.get('ppg', 0) >= 1 else '😔'}
• Récord: {home_stats.get('matches_played', 0)} partidos ({home_stats.get('wins', 0)}V-{home_stats.get('draws', 0)}E-{home_stats.get('losses', 0)}D)

📊 <b>¿CÓMO JUEGA {away_team.upper()}?</b>
• Mete goles (promedio): {away_stats.get('avg_goals_scored', 0):.2f} por partido
• Le meten goles (promedio): {away_stats.get('avg_goals_conceded', 0):.2f} por partido
• Tiros de esquina (promedio): {away_stats.get('avg_corners', 0):.1f} por partido
• Tiros al arco (promedio): {away_stats.get('avg_shots_on_target', 0):.1f} por partido
• Posesión (promedio): {away_stats.get('avg_possession', 0):.1f}%
• Ambos anotan: {away_stats.get('btts_percentage', 0):.1f}% de sus partidos
• +3 goles total: {away_stats.get('over_25_percentage', 0):.1f}% de sus partidos
• Rendimiento: {away_stats.get('ppg', 0):.2f} pts/juego {'🔥' if away_stats.get('ppg', 0) >= 2 else '⚽' if away_stats.get('ppg', 0) >= 1 else '😔'}
• Récord: {away_stats.get('matches_played', 0)} partidos ({away_stats.get('wins', 0)}V-{away_stats.get('draws', 0)}E-{away_stats.get('losses', 0)}D)

━━━━━━━━━━━━━━━━━━━━━━

💡 <b>INTERPRETACIÓN RÁPIDA</b>
{'🎯 Partido con muchos goles esperados' if over_25_prob >= 60 else '⚽ Goles normales esperados' if over_25_prob >= 45 else '🔒 Partido cerrado, pocos goles'}
{'✅ Probable que ambos anoten' if btts_prob >= 60 else '⚠️ Quizá solo uno anote' if btts_prob >= 45 else '❌ Difícil que ambos anoten'}

⚠️ <i>Basado en datos reales de la temporada actual</i>
"""

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
