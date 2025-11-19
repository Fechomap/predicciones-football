"""PDF Report Generator for match analysis"""
import os
from datetime import datetime
from typing import Dict, Optional
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class PDFReportGenerator:
    """
    Generates professional PDF reports for match analysis

    Includes:
    - Match header with teams and league
    - API-Football predictions
    - Poisson analysis
    - FootyStats historical data
    - Charts and visualizations
    - Value bet recommendations
    """

    def __init__(self):
        """Initialize PDF generator"""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        if 'CustomTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ))

        # Section header
        if 'SectionHeader' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionHeader',
                parent=self.styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#2563eb'),
                spaceAfter=12,
                spaceBefore=20,
                fontName='Helvetica-Bold',
                borderPadding=5,
                backColor=colors.HexColor('#eff6ff')
            ))

        # Subsection
        if 'SubSection' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SubSection',
                parent=self.styles['Heading3'],
                fontSize=12,
                textColor=colors.HexColor('#374151'),
                spaceAfter=8,
                fontName='Helvetica-Bold'
            ))

        # Body text
        if 'CustomBodyText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomBodyText',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#1f2937'),
                spaceAfter=6,
                leading=14
            ))

        # Highlight box
        if 'HighlightBox' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='HighlightBox',
                parent=self.styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor('#065f46'),
                backColor=colors.HexColor('#d1fae5'),
                borderPadding=10,
                borderColor=colors.HexColor('#059669'),
                borderWidth=1,
                fontName='Helvetica-Bold'
            ))

    def generate_match_report(
        self,
        fixture_data: Dict,
        api_football_analysis: Optional[Dict] = None,
        poisson_analysis: Optional[Dict] = None,
        footystats_analysis: Optional[Dict] = None,
        value_bet_analysis: Optional[Dict] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate complete match analysis PDF

        Args:
            fixture_data: Basic fixture information
            api_football_analysis: API-Football predictions
            poisson_analysis: Poisson model results
            footystats_analysis: FootyStats historical data
            value_bet_analysis: Value bet recommendations
            output_path: Optional custom output path

        Returns:
            Path to generated PDF file
        """
        try:
            # Extract match info
            home_team = fixture_data['teams']['home']['name']
            away_team = fixture_data['teams']['away']['name']
            league_name = fixture_data['league']['name']
            fixture_id = fixture_data['fixture']['id']
            kickoff_time = datetime.fromisoformat(fixture_data['fixture']['date'].replace('Z', '+00:00'))

            # Generate filename
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_home = home_team.replace(' ', '_').replace('/', '-')
                safe_away = away_team.replace(' ', '_').replace('/', '-')
                filename = f"match_analysis_{safe_home}_vs_{safe_away}_{timestamp}.pdf"
                output_path = os.path.join('/tmp', filename)

            logger.info(f"Generating PDF report for {home_team} vs {away_team}")

            # Pre-generate all charts (before building PDF)
            chart_images = {}
            if poisson_analysis and 'probabilities' in poisson_analysis:
                chart_path = self._create_probability_chart(poisson_analysis['probabilities'])
                if chart_path:
                    chart_images['poisson_chart'] = chart_path

            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=1.5*cm,
                leftMargin=1.5*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )

            # Build content
            story = []

            # Header
            story.extend(self._create_header(
                home_team, away_team, league_name, kickoff_time
            ))

            # API-Football Section
            if api_football_analysis:
                story.extend(self._create_api_football_section(api_football_analysis))

            # Poisson Section
            if poisson_analysis:
                story.extend(self._create_poisson_section(poisson_analysis, chart_images))

            # FootyStats Section
            if footystats_analysis:
                story.extend(self._create_footystats_section(footystats_analysis))

            # Value Bet Section
            if value_bet_analysis:
                story.extend(self._create_value_bet_section(value_bet_analysis))

            # Footer
            story.extend(self._create_footer(fixture_id))

            # Build PDF
            doc.build(story)

            # Clean up temp chart files
            for chart_path in chart_images.values():
                try:
                    if os.path.exists(chart_path):
                        os.remove(chart_path)
                except Exception as cleanup_error:
                    logger.warning(f"Could not remove temp file {chart_path}: {cleanup_error}")

            logger.info(f"✅ PDF generated successfully: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating PDF: {e}", exc_info=True)
            # Clean up any temp files on error
            if 'chart_images' in locals():
                for chart_path in chart_images.values():
                    try:
                        if os.path.exists(chart_path):
                            os.remove(chart_path)
                    except:
                        pass
            raise

    def _create_header(self, home_team: str, away_team: str, league: str, kickoff: datetime) -> list:
        """Create PDF header with match information"""
        story = []

        # Title
        title_text = f"{home_team} vs {away_team}"
        story.append(Paragraph(title_text, self.styles['CustomTitle']))

        # Match details table
        match_info = [
            ['Liga:', league],
            ['Fecha:', kickoff.strftime('%d/%m/%Y %H:%M')],
            ['Generado:', datetime.now().strftime('%d/%m/%Y %H:%M')]
        ]

        match_table = Table(match_info, colWidths=[3*cm, 12*cm])
        match_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1f2937')),
            ('ALIGNMENT', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        story.append(match_table)
        story.append(Spacer(1, 0.5*cm))

        return story

    def _create_api_football_section(self, analysis: Dict) -> list:
        """Create API-Football analysis section"""
        story = []

        story.append(Paragraph("📊 ANÁLISIS API-FOOTBALL", self.styles['SectionHeader']))

        # Predictions table
        if 'predictions' in analysis:
            pred = analysis['predictions']

            data = [
                ['Resultado', 'Probabilidad', 'Consejo'],
                ['Victoria Local', f"{pred.get('home', 0):.1f}%", pred.get('advice', 'N/A')],
                ['Empate', f"{pred.get('draw', 0):.1f}%", ''],
                ['Victoria Visitante', f"{pred.get('away', 0):.1f}%", ''],
            ]

            pred_table = Table(data, colWidths=[5*cm, 4*cm, 6*cm])
            pred_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))

            story.append(pred_table)
            story.append(Spacer(1, 0.3*cm))

        # Form comparison
        if 'form' in analysis:
            story.append(Paragraph("Forma Reciente:", self.styles['SubSection']))
            form_data = [
                ['Equipo', 'Últimos 5 Partidos', 'Rendimiento'],
                ['Local', analysis['form'].get('home', 'N/A'), f"{analysis['form'].get('home_points', 0)} pts/partido"],
                ['Visitante', analysis['form'].get('away', 'N/A'), f"{analysis['form'].get('away_points', 0)} pts/partido"],
            ]

            form_table = Table(form_data, colWidths=[5*cm, 6*cm, 4*cm])
            form_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#64748b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))

            story.append(form_table)

        story.append(Spacer(1, 0.5*cm))
        return story

    def _create_poisson_section(self, analysis: Dict, chart_images: Dict = None) -> list:
        """Create Poisson analysis section with probability charts"""
        story = []

        story.append(Paragraph("🧮 ANÁLISIS POISSON (MODELO ESTADÍSTICO)", self.styles['SectionHeader']))

        # Probabilities table
        probs = analysis.get('probabilities', {})
        data = [
            ['Resultado', 'Probabilidad', 'Goles Esperados'],
            ['Victoria Local', f"{probs.get('home_win', 0):.1f}%", f"{analysis.get('expected_goals_home', 0):.2f}"],
            ['Empate', f"{probs.get('draw', 0):.1f}%", '-'],
            ['Victoria Visitante', f"{probs.get('away_win', 0):.1f}%", f"{analysis.get('expected_goals_away', 0):.2f}"],
        ]

        probs_table = Table(data, colWidths=[5*cm, 4*cm, 6*cm])
        probs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        story.append(probs_table)
        story.append(Spacer(1, 0.3*cm))

        # Add probability chart if provided
        if chart_images and 'poisson_chart' in chart_images:
            img = Image(chart_images['poisson_chart'], width=14*cm, height=8*cm)
            story.append(img)

        story.append(Spacer(1, 0.5*cm))
        return story

    def _create_footystats_section(self, analysis: Dict) -> list:
        """Create FootyStats historical analysis section"""
        story = []

        story.append(Paragraph("📈 DATOS HISTÓRICOS (FootyStats)", self.styles['SectionHeader']))

        # Match quality
        if 'quality_score' in analysis:
            quality_text = f"<b>Calidad del Partido:</b> {analysis['quality_score']}/100"
            story.append(Paragraph(quality_text, self.styles['CustomBodyText']))
            story.append(Spacer(1, 0.2*cm))

        # Team statistics comparison
        home_stats = analysis.get('home_team_stats', {})
        away_stats = analysis.get('away_team_stats', {})

        if home_stats and away_stats:
            story.append(Paragraph("Estadísticas de Temporada:", self.styles['SubSection']))

            stats_data = [
                ['Métrica', 'Local', 'Visitante'],
                ['Goles anotados/partido', f"{home_stats.get('avg_goals_scored', 0):.2f}", f"{away_stats.get('avg_goals_scored', 0):.2f}"],
                ['Goles recibidos/partido', f"{home_stats.get('avg_goals_conceded', 0):.2f}", f"{away_stats.get('avg_goals_conceded', 0):.2f}"],
                ['Ambos anotan (%)', f"{home_stats.get('btts_percentage', 0):.1f}%", f"{away_stats.get('btts_percentage', 0):.1f}%"],
                ['Más de 2.5 goles (%)', f"{home_stats.get('over_25_percentage', 0):.1f}%", f"{away_stats.get('over_25_percentage', 0):.1f}%"],
                ['Partidos jugados', str(home_stats.get('matches_played', 0)), str(away_stats.get('matches_played', 0))],
            ]

            stats_table = Table(stats_data, colWidths=[7*cm, 4*cm, 4*cm])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))

            story.append(stats_table)

        story.append(Spacer(1, 0.5*cm))
        return story

    def _create_value_bet_section(self, analysis: Dict) -> list:
        """Create value bet recommendations section"""
        story = []

        story.append(Paragraph("💰 RECOMENDACIÓN DE APUESTA", self.styles['SectionHeader']))

        # Value bet highlight
        if analysis.get('has_value'):
            recommendation = analysis.get('recommended_bet', 'N/A')
            edge = analysis.get('edge', 0)
            odds = analysis.get('odds', 0)
            stake = analysis.get('suggested_stake', 0)

            highlight_text = f"""
            <b>✅ VALUE BET DETECTADO</b><br/>
            <br/>
            Apuesta recomendada: <b>{recommendation}</b><br/>
            Cuota: <b>{odds:.2f}</b><br/>
            Edge (ventaja): <b>{edge:.1f}%</b><br/>
            Stake sugerido: <b>{stake:.1f}% del bankroll</b>
            """

            story.append(Paragraph(highlight_text, self.styles['HighlightBox']))
        else:
            no_value_text = "⚠️ No se detectó value bet en este partido según el análisis."
            story.append(Paragraph(no_value_text, self.styles['CustomBodyText']))

        story.append(Spacer(1, 0.5*cm))

        # Confidence rating
        if 'confidence' in analysis:
            conf_text = f"<b>Nivel de Confianza:</b> {analysis['confidence']}/5 ⭐"
            story.append(Paragraph(conf_text, self.styles['CustomBodyText']))

        story.append(Spacer(1, 0.5*cm))
        return story

    def _create_footer(self, fixture_id: int) -> list:
        """Create PDF footer"""
        story = []

        story.append(Spacer(1, 1*cm))

        footer_text = f"""
        <para alignment="center">
        ───────────────────────────────────────<br/>
        <br/>
        🤖 Generado con Football Betting Bot<br/>
        📊 Análisis basado en múltiples fuentes: API-Football, Modelo Poisson, FootyStats<br/>
        <br/>
        ⚠️ <i>Este análisis es informativo. Apuesta responsablemente.</i><br/>
        <br/>
        Fixture ID: {fixture_id} | {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </para>
        """

        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#6b7280'),
            alignment=TA_CENTER
        )

        story.append(Paragraph(footer_text, footer_style))

        return story

    def _create_probability_chart(self, probabilities: Dict) -> Optional[str]:
        """Create probability bar chart using matplotlib"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            labels = ['Victoria\nLocal', 'Empate', 'Victoria\nVisitante']
            values = [
                probabilities.get('home_win', 0),
                probabilities.get('draw', 0),
                probabilities.get('away_win', 0)
            ]
            colors_map = ['#3b82f6', '#6b7280', '#ef4444']

            bars = ax.bar(labels, values, color=colors_map, edgecolor='black', linewidth=1.5)

            # Add value labels on bars
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{value:.1f}%',
                       ha='center', va='bottom', fontweight='bold', fontsize=12)

            ax.set_ylabel('Probabilidad (%)', fontsize=12, fontweight='bold')
            ax.set_title('Distribución de Probabilidades (Modelo Poisson)',
                        fontsize=14, fontweight='bold', pad=20)
            ax.set_ylim(0, max(values) * 1.2)
            ax.grid(axis='y', alpha=0.3, linestyle='--')

            # Save to temp file
            temp_path = f'/tmp/prob_chart_{datetime.now().timestamp()}.png'
            plt.tight_layout()
            plt.savefig(temp_path, dpi=150, bbox_inches='tight')
            plt.close()

            return temp_path

        except Exception as e:
            logger.error(f"Error creating chart: {e}")
            return None
