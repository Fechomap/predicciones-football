"""
PDF Service - Generación de reportes PDF Profesionales (Final Spec v2 - 100% Parity)
"""
import os
from typing import List, Dict, Any
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from pathlib import Path

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class PDFService:
    """
    Servicio de generación de PDFs Profesionales
    Implementa "INFORME FINAL Y DEFINITIVO" + HOMOLOGACIÓN TOTAL TELEGRAM
    """

    @staticmethod
    def generate_league_weekly_report(
        league_name: str,
        results: List[Dict],
        output_dir: str = "reports"
    ) -> str:
        """
        Genera PDF HORIZONTAL con análisis de TODOS los partidos
        """
        logger.info(f"Generando PDF para {league_name} con {len(results)} partidos")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/{league_name.replace(' ', '_')}_{timestamp}.pdf"

        doc = SimpleDocTemplate(
            filename,
            pagesize=landscape(A4),
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1*cm,
            bottomMargin=1*cm
        )

        elements = []
        styles = PDFService._get_styles()

        # --- PÁGINA 1: RESUMEN EJECUTIVO ---
        elements.append(Paragraph(f"<b>{league_name.upper()} - RESUMEN SEMANAL</b>", styles['DocTitle']))
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} | {len(results)} partidos analizados", styles['DocSubtitle']))
        elements.append(Spacer(1, 0.5*cm))

        # Tabla Resumen
        summary_data = [['Ranking', 'Partido', 'Fecha', 'Confianza', 'Recomendación']]
        for idx, res in enumerate(results, 1):
            fix = res['fixture']
            val = res['analysis'].get('value_bet')

            home = fix['teams']['home']['name']
            away = fix['teams']['away']['name']
            date = fix['fixture']['date'][:10]
            # Confianza como fracción en vez de estrellas (mejor renderizado)
            conf = f"[{min(res['confidence'], 5)}/5]"
            rec = val.get('outcome', 'N/A') if (res['analysis'].get('has_value') and val) else "Observar"

            summary_data.append([f"#{idx}", f"{home} vs {away}", date, conf, rec])

        summary_table = Table(summary_data, colWidths=[2*cm, 10*cm, 3*cm, 4*cm, 6*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
        ]))
        elements.append(summary_table)
        elements.append(PageBreak())

        # --- PÁGINAS SIGUIENTES: DETALLE PARTIDOS ---
        for idx, result in enumerate(results, 1):
            match_block = PDFService._create_match_block(idx, result, styles, league_name)
            elements.append(match_block)
            
            # Separador (espacio)
            elements.append(Spacer(1, 0.6*cm))

        # Footer Paginación
        def footer(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors.HexColor('#6b7280'))
            canvas.drawRightString(landscape(A4)[0] - 1*cm, 0.5*cm, f"Página {doc.page}")
            canvas.restoreState()

        doc.build(elements, onFirstPage=footer, onLaterPages=footer)
        logger.info(f"📄 PDF Final generado: {filename}")
        return filename

    @staticmethod
    def _create_match_block(idx: int, result: Dict, styles: Dict, league_name: str) -> KeepTogether:
        """Crea el bloque de análisis según especificación final"""
        fixture = result['fixture']
        analysis = result['analysis']
        confidence = result['confidence']

        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        date_str = fixture['fixture']['date'][:16].replace("T", " ")

        # Confianza como texto en vez de emojis de estrellas (mejor renderizado)
        confidence_text = f"[{min(confidence, 5)}/5]"

        # 1. CABECERA DEL BLOQUE (1x3)
        header_data = [[
            Paragraph(f"<b>#{idx}</b> {confidence_text}", styles['HeaderRank']),
            Paragraph(f"<b>{home} vs {away}</b> ({league_name})", styles['HeaderMatch']),
            Paragraph(f"📅 {date_str}", styles['HeaderDate'])
        ]]
        
        header_table = Table(header_data, colWidths=[4*cm, 18*cm, 5*cm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
        ]))

        # 2. CUERPO DEL BLOQUE (1x2)
        left_col = PDFService._create_left_column(analysis, styles, fixture)
        right_col = PDFService._create_right_column(analysis, styles, fixture)

        body_data = [[left_col, right_col]]
        body_table = Table(body_data, colWidths=[13.5*cm, 13.5*cm])
        body_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))

        # 3. PIE DEL BLOQUE (Recomendación Auditor + Disclaimer)
        rec_text = PDFService._get_auditor_recommendation(analysis, confidence)
        footer_para = Paragraph(rec_text, styles['AuditorRec'])
        disclaimer_para = Paragraph("⚠️ Análisis estadístico - Apuesta responsable", styles['Disclaimer'])

        return KeepTogether([
            header_table,
            body_table,
            Spacer(1, 0.1*cm),
            footer_para,
            disclaimer_para
        ])

    @staticmethod
    def _create_left_column(analysis: Dict, styles: Dict, fixture: Dict) -> List:
        """
        Celda Izquierda: Predicciones y Value Bet
        HOMOLOGADO CON TELEGRAM (líneas 379-477)
        """
        elements = []
        elements.append(Paragraph("Análisis Predictivo", styles['SubTitle']))

        api = analysis.get('api_prediction', {})
        our = analysis.get('our_prediction', {})

        # 1. PREDICCIÓN API-FOOTBALL (según telegram_handlers.py:379-383)
        api_h = (api.get('home') or 0) * 100
        api_d = (api.get('draw') or 0) * 100
        api_a = (api.get('away') or 0) * 100

        # 2. PREDICCIÓN POISSON (según telegram_handlers.py:385-388)
        our_h = our.get('home', 0) * 100
        our_d = our.get('draw', 0) * 100
        our_a = our.get('away', 0) * 100

        # 3. COMPARACIÓN - DIFERENCIAS (según telegram_handlers.py:390-393)
        diff_h = abs((our.get('home', 0) - (api.get('home') or 0)) * 100)
        diff_d = abs((our.get('draw', 0) - (api.get('draw') or 0)) * 100)
        diff_a = abs((our.get('away', 0) - (api.get('away') or 0)) * 100)

        # TABLA DE PREDICCIONES CON 4 FILAS (como especificación)
        pred_data = [
            ['Modelo', 'Local (1)', 'Empate (X)', 'Visitante (2)'],
            ['API-Football', f"{api_h:.1f}%", f"{api_d:.1f}%", f"{api_a:.1f}%"],
            ['Poisson', f"{our_h:.1f}%", f"{our_d:.1f}%", f"{our_a:.1f}%"],
            ['Diferencia', f"{diff_h:.1f}%", f"{diff_d:.1f}%", f"{diff_a:.1f}%"]
        ]

        pred_table = Table(pred_data, colWidths=[3*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        pred_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            # Resaltar fila de diferencias (especificación línea 256)
            ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#fff3cd')),
        ]))
        elements.append(pred_table)
        elements.append(Spacer(1, 0.1*cm))

        # GANADOR SUGERIDO API (si existe - línea 383)
        winner = api.get('winner')
        if winner:
            elements.append(Paragraph(f"• <b>Ganador sugerido:</b> {winner}", styles['NormalText']))
            elements.append(Spacer(1, 0.15*cm))

        # VALUE BET (según telegram_handlers.py:456-477)
        value = analysis.get('value_bet')
        if analysis.get('has_value') and value:
            bg = colors.honeydew
            border = colors.HexColor('#4ade80')
            # Confianza como fracción en vez de estrellas (mejor renderizado en PDF)
            confidence_level = min(value.get('confidence', 3), 5)
            confidence_text = f"[{confidence_level}/5]"
            stake = value.get('suggested_stake', 0) * 100

            # FORMATO EXACTO COMO TELEGRAM (líneas 461-470)
            text = f"""<b>💰 VALUE BET DETECTADO</b><br/>
            <font size=7><i>(Basado en nuestra predicción Poisson)</i></font><br/><br/>
            • <b>Resultado:</b> {value.get('outcome')}<br/>
            • <b>Edge:</b> +{value.get('edge',0)*100:.1f}%<br/>
            • <b>Confianza:</b> {confidence_text}<br/><br/>
            💡 <b>RECOMENDACIÓN</b><br/>
            Stake sugerido: {stake:.0f}% del bankroll"""
        else:
            bg = colors.HexColor('#f3f4f6')
            border = colors.HexColor('#d1d5db')
            # FORMATO EXACTO COMO TELEGRAM (líneas 472-477)
            text = """ℹ️ <b>No se detectó value bet</b><br/>
            <font size=7>(Edge menor a 5%)</font>"""

        vb_table = Table([[Paragraph(text, styles['NormalText'])]], colWidths=[11*cm])
        vb_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg),
            ('BOX', (0, 0), (-1, -1), 1, border),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(vb_table)

        return elements

    @staticmethod
    def _create_right_column(analysis: Dict, styles: Dict, fixture: Dict) -> List:
        """
        Celda Derecha: Estadísticas Contexto
        ORDEN EXACTO SEGÚN TELEGRAM (líneas 397-436):
        1. Goles Esperados (movido de izq a der)
        2. Probabilidad de Goles Totales
        3. Forma Reciente
        4. Partidos Jugados
        5. FootyStats
        """
        elements = []
        elements.append(Paragraph("Rendimiento y Datos Clave", styles['SubTitle']))

        stats = analysis.get('statistics', {})
        footystats = analysis.get('footystats', {})
        ranges = analysis.get('goal_ranges', {})

        home_name = fixture['teams']['home']['name']
        away_name = fixture['teams']['away']['name']

        # 1. GOLES ESPERADOS (según telegram_handlers.py:397-399)
        xg_h = stats.get('expected_goals_home', 0)
        xg_a = stats.get('expected_goals_away', 0)

        xg_text = f"""
        <b>⚽ GOLES ESPERADOS</b><br/>
        • {home_name}: <b>{xg_h:.2f}</b><br/>
        • {away_name}: <b>{xg_a:.2f}</b>
        """
        elements.append(Paragraph(xg_text, styles['NormalText']))
        elements.append(Spacer(1, 0.15*cm))

        # 2. PROBABILIDAD DE GOLES TOTALES (según telegram_handlers.py:401-404)
        r_01 = ranges.get('0-1', 0) * 100
        r_23 = ranges.get('2-3', 0) * 100
        r_4p = ranges.get('4+', 0) * 100

        goals_text = f"""
        <b>🥅 PROBABILIDAD DE GOLES TOTALES</b><br/>
        • 0-1 Goles: {r_01:.1f}%<br/>
        • 2-3 Goles: {r_23:.1f}%<br/>
        • 4+ Goles: {r_4p:.1f}%
        """
        elements.append(Paragraph(goals_text, styles['NormalText']))
        elements.append(Spacer(1, 0.15*cm))

        # 3. FORMA RECIENTE CON PUNTUACIÓN (según telegram_handlers.py:406-408)
        h_form_str = PDFService._format_form_with_points(stats.get('home_form', 'N/A'))
        a_form_str = PDFService._format_form_with_points(stats.get('away_form', 'N/A'))

        form_text = f"""
        <b>🔥 FORMA RECIENTE</b> (últimos 5 partidos)<br/>
        • {home_name}: {h_form_str}<br/>
        • {away_name}: {a_form_str}
        """
        elements.append(Paragraph(form_text, styles['NormalText']))
        elements.append(Spacer(1, 0.15*cm))

        # 4. PARTIDOS JUGADOS (según telegram_handlers.py:410-412)
        h_matches = stats.get('home_matches', 0)
        a_matches = stats.get('away_matches', 0)

        matches_text = f"""
        <b>📊 PARTIDOS JUGADOS</b><br/>
        • {home_name} (casa): {h_matches} partidos<br/>
        • {away_name} (visita): {a_matches} partidos
        """
        elements.append(Paragraph(matches_text, styles['NormalText']))
        elements.append(Spacer(1, 0.15*cm))

        # 5. FOOTYSTATS (según telegram_handlers.py:418-434)
        if footystats and footystats.get('quality_score', 0) > 0:
            quality_score = footystats.get('quality_score', 0)
            btts_prob = footystats.get('btts_probability', 0) * 100
            over_25_prob = footystats.get('over_25_probability', 0) * 100
            intensity = footystats.get('match_intensity', 'medium')

            # INTENSIDAD - Símbolos ASCII para compatibilidad con ReportLab
            # (Telegram usa 🟢🟡🔴 pero ReportLab no los renderiza bien)
            intensity_symbol = {
                'low': '[BAJA]',
                'medium': '[MEDIA]',
                'high': '[ALTA]'
            }.get(intensity, '[N/A]')

            fs_text = f"""
            <b>📊 DATOS MEJORADOS (FootyStats):</b><br/>
            • Calidad del partido: {quality_score:.0f}/100<br/>
            • BTTS Probabilidad: {btts_prob:.1f}%<br/>
            • Over 2.5 Probabilidad: {over_25_prob:.1f}%<br/>
            • Intensidad: {intensity_symbol}
            """
        else:
            fs_text = "<i>❌ Datos de FootyStats no disponibles.</i>"

        elements.append(Paragraph(fs_text, styles['NormalText']))
        return elements

    @staticmethod
    def _get_auditor_recommendation(analysis: Dict, confidence: int) -> str:
        """Genera texto de recomendación del auditor"""
        conf_text = "CONFIANZA ALTA" if confidence >= 4 else "CONFIANZA MEDIA" if confidence == 3 else "CONFIANZA BAJA"
        
        if analysis.get('has_value'):
            return f"Recomendación del Auditor: <b>{conf_text}.</b> La consistencia entre nuestro modelo y la data de mercado, sumado al valor detectado, indica una fuerte oportunidad."
        else:
            return f"Recomendación del Auditor: <b>{conf_text}.</b> No se detecta valor claro. Se sugiere observar en vivo o buscar mejores cuotas."

    @staticmethod
    def _get_prob(analysis: Dict, outcome: str) -> float:
        """Helper para obtener probabilidad de nuestro modelo"""
        our = analysis.get('our_prediction', {})
        if 'Home' in outcome or 'Local' in outcome: return our.get('home', 0) * 100
        if 'Away' in outcome or 'Visit' in outcome: return our.get('away', 0) * 100
        return our.get('draw', 0) * 100

    @staticmethod
    def _format_form(form_data: Any) -> str:
        """Convierte forma a emojis sin puntuación (uso interno)"""
        if isinstance(form_data, dict):
            s = form_data.get('form_string', 'N/A')
        else:
            s = str(form_data)
        if s == 'N/A':
            return s
        return s.replace('W', '✅').replace('D', '🟨').replace('L', '❌')

    @staticmethod
    def _format_form_with_points(form_data: Any) -> str:
        """
        Formatea forma reciente CON puntuación
        EXACTO COMO TELEGRAM (message_formatter.py:162-177)
        Ejemplo: "WWDWL" -> "W W D W L (10/15 pts)"

        Nota: Usa letras en vez de emojis por limitación de ReportLab
        W = Victoria (verde en Telegram)
        D = Empate (amarillo en Telegram)
        L = Derrota (rojo en Telegram)
        """
        if isinstance(form_data, dict):
            form_string = form_data.get('form_string', 'N/A')
        else:
            form_string = str(form_data)

        if not form_string or form_string == "N/A":
            return "N/A"

        # Convertir a letras separadas por espacios para mejor legibilidad
        # (ReportLab no renderiza bien ✅🟨❌)
        visual_form = ' '.join(list(form_string))

        # Calcular puntos (W=3, D=1, L=0)
        points = form_string.count('W') * 3 + form_string.count('D') * 1
        max_points = len(form_string) * 3

        return f"{visual_form} ({points}/{max_points} pts)"

    @staticmethod
    def _get_styles() -> Dict:
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=14, alignment=TA_CENTER))
        styles.add(ParagraphStyle('DocSubtitle', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.grey))
        
        styles.add(ParagraphStyle('HeaderRank', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle('HeaderMatch', parent=styles['Normal'], fontSize=10, alignment=TA_LEFT))
        styles.add(ParagraphStyle('HeaderDate', parent=styles['Normal'], fontSize=10, alignment=TA_RIGHT))
        
        styles.add(ParagraphStyle('SubTitle', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor('#2563eb'), spaceAfter=4))
        styles.add(ParagraphStyle('NormalText', parent=styles['Normal'], fontSize=8, leading=10))
        styles.add(ParagraphStyle('AuditorRec', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Oblique', textColor=colors.HexColor('#1f2937'), leftIndent=5))
        styles.add(ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=6, textColor=colors.grey, alignment=TA_CENTER))
        
        return styles
