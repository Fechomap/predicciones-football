"""
PDF Service - Generación de reportes PDF IDÉNTICOS a Telegram

CRÍTICO:
- Formato EXACTAMENTE igual que _format_analysis() en telegram_handlers.py
- Mismos cálculos, mismos datos, mismo orden
- Horizontal (landscape) para máximo espacio
- TODO continuo (NO páginas separadas)
- Márgenes: 1cm
"""
from typing import List, Dict
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT
from pathlib import Path

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class PDFService:
    """Servicio de generación de PDFs (formato idéntico a Telegram)"""

    @staticmethod
    def generate_league_weekly_report(
        league_name: str,
        results: List[Dict],
        output_dir: str = "reports"
    ) -> str:
        """
        Genera PDF HORIZONTAL con análisis de TODOS los partidos

        FORMATO: Exactamente como Telegram (telegram_handlers.py:349-481)
        - Cada partido: Análisis completo
        - TODO continuo
        - MISMOS cálculos que Telegram

        Args:
            league_name: Nombre de la liga
            results: Lista de {fixture, analysis, confidence}
            output_dir: Directorio de salida

        Returns:
            Path al archivo PDF generado
        """
        # Crear directorio si no existe
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Nombre del archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/{league_name.replace(' ', '_')}_{timestamp}.pdf"

        # Crear PDF HORIZONTAL con márgenes de 1cm
        doc = SimpleDocTemplate(
            filename,
            pagesize=landscape(A4),
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1*cm,
            bottomMargin=1*cm
        )

        elements = []
        styles = getSampleStyleSheet()

        # Título
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=12,
            spaceAfter=0.5*cm,
            alignment=1  # Centrado
        )

        title = Paragraph(
            f"<b>{league_name.upper()} - ANÁLISIS COMPLETO</b><br/>"
            f"<font size=9>{datetime.now().strftime('%d/%m/%Y')} | "
            f"{len(results)} partidos | Ordenados por confianza</font>",
            title_style
        )
        elements.append(title)
        elements.append(Spacer(1, 0.3*cm))

        # Generar análisis de cada partido (FORMATO TELEGRAM)
        for idx, result in enumerate(results, 1):
            partido_analysis = PDFService._format_partido_como_telegram(
                idx, result, styles
            )
            elements.append(partido_analysis)

            # Separador entre partidos
            if idx < len(results):
                elements.append(Spacer(1, 0.4*cm))
                sep_style = ParagraphStyle('Sep', parent=styles['Normal'], fontSize=8)
                elements.append(Paragraph("━" * 100, sep_style))
                elements.append(Spacer(1, 0.4*cm))

        # Generar PDF
        doc.build(elements)

        logger.info(f"📄 PDF generado: {filename}")
        logger.info(f"   - {len(results)} partidos")

        return filename

    @staticmethod
    def _format_partido_como_telegram(idx: int, result: Dict, styles) -> Paragraph:
        """
        Formatea partido EXACTAMENTE como telegram_handlers.py:349-481

        IMPORTANTE: Usar los MISMOS nombres de campos y cálculos
        """
        fixture = result['fixture']
        analysis = result['analysis']
        confidence = result['confidence']

        # Extraer datos (IGUAL que Telegram líneas 353-367)
        fixture_info = fixture.get("fixture", {})
        teams = fixture.get("teams", {})
        league = fixture.get("league", {})

        home_team = teams.get("home", {}).get("name", "")
        away_team = teams.get("away", {}).get("name", "")
        league_name = league.get("name", "")
        date_str = fixture_info.get("date", "")[:16].replace("T", " ")

        our_pred = analysis.get("our_prediction", {})
        api_pred = analysis.get("api_prediction", {})
        stats = analysis.get("statistics", {})
        goal_ranges = analysis.get("goal_ranges", {})
        value = analysis.get("value_bet")

        # Construir mensaje EXACTAMENTE como Telegram (líneas 370-481)
        message_text = f"""
<b>PARTIDO #{idx}</b><br/>
<br/>
⚽ <b>ANÁLISIS DEL PARTIDO</b><br/>
<br/>
🏆 {league_name}<br/>
📅 {home_team} vs {away_team}<br/>
🕐 {date_str}<br/>
<br/>
━━━━━━━━━━━━━━━━━━━━━━<br/>
<br/>
🤖 <b>PREDICCIÓN API-FOOTBALL</b><br/>
• Local (1): {(api_pred.get('home') or 0)*100:.1f}%<br/>
• Empate (X): {(api_pred.get('draw') or 0)*100:.1f}%<br/>
• Visitante (2): {(api_pred.get('away') or 0)*100:.1f}%<br/>
{f"• Ganador sugerido: {api_pred.get('winner', 'N/A')}<br/>" if api_pred.get('winner') else ""}<br/>
🧮 <b>NUESTRA PREDICCIÓN (Poisson)</b><br/>
• Local (1): {our_pred.get('home', 0)*100:.1f}%<br/>
• Empate (X): {our_pred.get('draw', 0)*100:.1f}%<br/>
• Visitante (2): {our_pred.get('away', 0)*100:.1f}%<br/>
<br/>
📊 <b>COMPARACIÓN</b><br/>
• Diferencia Local: {abs((our_pred.get('home', 0) - (api_pred.get('home') or 0)) * 100):.1f}%<br/>
• Diferencia Empate: {abs((our_pred.get('draw', 0) - (api_pred.get('draw') or 0)) * 100):.1f}%<br/>
• Diferencia Visitante: {abs((our_pred.get('away', 0) - (api_pred.get('away') or 0)) * 100):.1f}%<br/>
<br/>
━━━━━━━━━━━━━━━━━━━━━━<br/>
<br/>
⚽ <b>GOLES ESPERADOS</b><br/>
• {home_team}: {stats.get('expected_goals_home', 0):.2f}<br/>
• {away_team}: {stats.get('expected_goals_away', 0):.2f}<br/>
<br/>
🥅 <b>PROBABILIDAD DE GOLES TOTALES</b><br/>
• 0-1 Goles: {goal_ranges.get('0-1', 0) * 100:.1f}%<br/>
• 2-3 Goles: {goal_ranges.get('2-3', 0) * 100:.1f}%<br/>
• 4+ Goles: {goal_ranges.get('4+', 0) * 100:.1f}%<br/>
<br/>
📈 <b>FORMA RECIENTE</b> (últimos 5 partidos)<br/>
• {home_team}: {PDFService._format_form_string(stats.get('home_form', 'N/A'))}<br/>
• {away_team}: {PDFService._format_form_string(stats.get('away_form', 'N/A'))}<br/>
<br/>
📊 <b>PARTIDOS JUGADOS</b><br/>
• {home_team} (casa): {stats.get('home_matches', 0)} partidos<br/>
• {away_team} (visita): {stats.get('away_matches', 0)} partidos<br/>
"""

        # FootyStats (IGUAL que Telegram líneas 416-436)
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

            message_text += f"""
📊 <b>DATOS MEJORADOS (FootyStats):</b><br/>
• Calidad del partido: {quality_score:.0f}/100<br/>
• BTTS Probabilidad: {btts_prob:.1f}%<br/>
• Over 2.5 Probabilidad: {over_25_prob:.1f}%<br/>
• Intensidad: {intensity_emoji} {intensity.capitalize()}<br/>
<br/>
"""

        # Value Bet (IGUAL que Telegram líneas 438-478)
        if analysis.get("odds_unavailable"):
            # No odds available
            message_text += """
━━━━━━━━━━━━━━━━━━━━━━<br/>
<br/>
⚠️ <b>CUOTAS NO DISPONIBLES</b><br/>
<br/>
No se pudieron obtener cuotas de mercado para este partido.<br/>
<br/>
<i>Posibles razones:</i><br/>
• El partido está muy lejos en el futuro<br/>
• Las casas de apuestas aún no publicaron cuotas<br/>
• Error temporal en la API<br/>
<br/>
El análisis estadístico (arriba) sigue siendo válido.<br/>
Intenta de nuevo más cerca del partido.<br/>
"""
        elif analysis.get("has_value") and value:
            confidence_stars = "⭐" * min(value.get('confidence', 3), 5)
            message_text += f"""
━━━━━━━━━━━━━━━━━━━━━━<br/>
<br/>
💰 <b>VALUE BET DETECTADO</b><br/>
<i>(Basado en nuestra predicción Poisson)</i><br/>
<br/>
• Resultado: {value.get('outcome', 'N/A')}<br/>
• Edge: +{value.get('edge', 0)*100:.1f}%<br/>
• Confianza: {confidence_stars}<br/>
<br/>
💡 <b>RECOMENDACIÓN</b><br/>
Stake sugerido: {value.get('suggested_stake', 0)*100:.0f}% del bankroll<br/>
"""
        else:
            message_text += """
━━━━━━━━━━━━━━━━━━━━━━<br/>
<br/>
ℹ️ <b>No se detectó value bet</b><br/>
(Edge menor a 5%)<br/>
"""

        message_text += "<br/><br/>⚠️ Análisis estadístico - Apuesta responsable"

        # Crear párrafo con el análisis
        analysis_style = ParagraphStyle(
            'Analysis',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            leftIndent=0.5*cm,
            rightIndent=0.5*cm,
            alignment=TA_LEFT
        )

        return Paragraph(message_text, analysis_style)

    @staticmethod
    def _format_form_string(form_string: str) -> str:
        """
        Convert form string to emoji (IGUAL que message_formatter.py:162-177)

        Args:
            form_string: Form string (e.g., "WLDWW" or "N/A")

        Returns:
            Form string with emojis (e.g., "✅❌🟨✅✅")
        """
        if not form_string or form_string == "N/A":
            return "N/A"

        # Replace W, D, L with emojis (MISMO que Telegram)
        emoji_form = form_string.replace('W', '✅').replace('D', '🟨').replace('L', '❌')
        return emoji_form
