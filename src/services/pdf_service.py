"""
PDF Service - Generación de reportes PDF por liga

RESPONSABILIDAD:
- Generar PDF horizontal con resumen de liga completa
- Ordenar partidos por confianza (estrellas)
- Formato optimizado para análisis rápido
"""
from typing import List, Dict
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from pathlib import Path

from ..utils.logger import setup_logger
from ..utils.confidence_calculator import ConfidenceCalculator

logger = setup_logger(__name__)


class PDFService:
    """Servicio de generación de PDFs"""

    @staticmethod
    def generate_league_weekly_report(
        league_name: str,
        results: List[Dict],
        output_dir: str = "reports"
    ) -> str:
        """
        Genera PDF horizontal con resumen semanal de una liga

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

        # Crear PDF en orientación horizontal
        doc = SimpleDocTemplate(
            filename,
            pagesize=landscape(A4),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )

        # Elementos del PDF
        elements = []
        styles = getSampleStyleSheet()

        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=20,
            alignment=1  # Centrado
        )

        week_start = datetime.now().strftime("%d/%m/%Y")
        title = Paragraph(
            f"<b>{league_name} - RESUMEN SEMANAL</b><br/>"
            f"<font size=10>Semana del {week_start}</font>",
            title_style
        )
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))

        # Preparar datos para la tabla
        table_data = [
            ['#', 'Partido', 'Fecha', 'Local', 'Empate', 'Visit.', 'Edge', 'Confianza']
        ]

        for idx, result in enumerate(results, 1):
            fixture = result['fixture']
            analysis = result['analysis']
            confidence = result['confidence']

            # Extraer datos
            teams = fixture.get('teams', {})
            fixture_info = fixture.get('fixture', {})
            our_pred = analysis.get('our_prediction', {})

            home_team = teams.get('home', {}).get('name', 'N/A')
            away_team = teams.get('away', {}).get('name', 'N/A')
            date = fixture_info.get('date', '')[:10]  # YYYY-MM-DD

            # Probabilidades
            home_prob = our_pred.get('home', 0) * 100
            draw_prob = our_pred.get('draw', 0) * 100
            away_prob = our_pred.get('away', 0) * 100

            # Edge
            edge = analysis.get('best_edge', 0) * 100

            # Estrellas
            stars = '⭐' * confidence

            table_data.append([
                str(idx),
                f"{home_team} vs {away_team}",
                date,
                f"{home_prob:.0f}%",
                f"{draw_prob:.0f}%",
                f"{away_prob:.0f}%",
                f"{edge:.1f}%",
                stars
            ])

        # Crear tabla
        table = Table(table_data, colWidths=[
            0.4*inch,  # #
            2.8*inch,  # Partido
            0.8*inch,  # Fecha
            0.7*inch,  # Local
            0.7*inch,  # Empate
            0.7*inch,  # Visit
            0.7*inch,  # Edge
            1.2*inch   # Confianza
        ])

        # Estilo de tabla
        table_style = TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            # Body
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            # Alternar colores de filas
            *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ecf0f1'))
              for i in range(2, len(table_data), 2)]
        ])

        # Resaltar top 3 (alta confianza)
        for i in range(1, min(4, len(table_data))):
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#d5f4e6'))  # Verde claro

        table.setStyle(table_style)
        elements.append(table)

        # Nota al pie
        elements.append(Spacer(1, 0.3*inch))
        note_style = ParagraphStyle(
            'Note',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#7f8c8d')
        )
        note = Paragraph(
            "💡 <b>Recomendación:</b> Concentrarse en los primeros 3-5 partidos (mayor confianza). "
            "Los partidos están ordenados de mayor a menor confianza de apuesta.",
            note_style
        )
        elements.append(note)

        # Generar PDF
        doc.build(elements)

        logger.info(f"📄 PDF generado: {filename}")
        return filename
