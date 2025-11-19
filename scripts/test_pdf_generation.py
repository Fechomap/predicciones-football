#!/usr/bin/env python3
"""Test script for PDF generation"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.reports.pdf_generator import PDFReportGenerator
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_data():
    """Create sample match data for testing"""

    fixture_data = {
        'fixture': {
            'id': 1379087,
            'date': '2025-11-22T11:30:00+00:00',
            'timestamp': int(datetime(2025, 11, 22, 11, 30).timestamp()),
            'status': {'short': 'NS'},
            'venue': {'name': 'St. James\' Park'}
        },
        'league': {
            'id': 39,
            'name': 'Premier League',
            'country': 'England',
            'round': 'Regular Season - 12',
            'season': 2025
        },
        'teams': {
            'home': {
                'id': 34,
                'name': 'Newcastle United',
                'logo': 'https://media.api-sports.io/football/teams/34.png'
            },
            'away': {
                'id': 50,
                'name': 'Manchester City',
                'logo': 'https://media.api-sports.io/football/teams/50.png'
            }
        }
    }

    api_football_analysis = {
        'predictions': {
            'home': 35.2,
            'draw': 28.5,
            'away': 36.3,
            'advice': 'Victoria visitante o empate'
        },
        'form': {
            'home': 'W-W-D-L-W',
            'away': 'W-D-W-W-L',
            'home_points': 2.6,
            'away_points': 2.4
        }
    }

    poisson_analysis = {
        'probabilities': {
            'home_win': 32.8,
            'draw': 27.1,
            'away_win': 40.1
        },
        'expected_goals_home': 1.45,
        'expected_goals_away': 1.82
    }

    footystats_analysis = {
        'quality_score': 87,
        'home_team_stats': {
            'avg_goals_scored': 3.00,
            'avg_goals_conceded': 0.50,
            'btts_percentage': 50.0,
            'over_25_percentage': 50.0,
            'matches_played': 2
        },
        'away_team_stats': {
            'avg_goals_scored': 1.67,
            'avg_goals_conceded': 1.67,
            'btts_percentage': 100.0,
            'over_25_percentage': 100.0,
            'matches_played': 3
        }
    }

    value_bet_analysis = {
        'has_value': True,
        'recommended_bet': 'Victoria Manchester City',
        'odds': 2.65,
        'edge': 6.4,
        'suggested_stake': 3.2,
        'confidence': 4
    }

    return {
        'fixture': fixture_data,
        'api_football': api_football_analysis,
        'poisson': poisson_analysis,
        'footystats': footystats_analysis,
        'value_bet': value_bet_analysis
    }


def main():
    """Test PDF generation"""
    logger.info("=" * 70)
    logger.info("🧪 TESTING PDF GENERATION")
    logger.info("=" * 70)

    # Create sample data
    logger.info("\n📊 Creating sample match data...")
    data = create_sample_data()

    # Initialize generator
    logger.info("🔧 Initializing PDF generator...")
    pdf_gen = PDFReportGenerator()

    # Generate PDF
    logger.info("📄 Generating PDF report...")
    try:
        pdf_path = pdf_gen.generate_match_report(
            fixture_data=data['fixture'],
            api_football_analysis=data['api_football'],
            poisson_analysis=data['poisson'],
            footystats_analysis=data['footystats'],
            value_bet_analysis=data['value_bet'],
            output_path='/tmp/test_match_analysis.pdf'
        )

        logger.info(f"\n✅ PDF GENERATED SUCCESSFULLY!")
        logger.info(f"📍 Location: {pdf_path}")
        logger.info(f"\n💡 Open the PDF with:")
        logger.info(f"   open {pdf_path}")
        logger.info("\n" + "=" * 70)

    except Exception as e:
        logger.error(f"\n❌ PDF generation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
