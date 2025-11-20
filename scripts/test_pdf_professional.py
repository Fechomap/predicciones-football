import sys
import os
from datetime import datetime
import copy

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.services.pdf_service import PDFService

def test_professional_pdf():
    print("🚀 Generando PDF de prueba profesional (Completo)...")
    
    # Base mock match con TODOS los campos requeridos
    base_match = {
        'fixture': {
            'fixture': {'date': '2025-11-23T18:00:00+00:00'},
            'teams': {
                'home': {'name': 'Home Team'},
                'away': {'name': 'Away Team'}
            }
        },
        'confidence': 5,
        'analysis': {
            'api_prediction': {'home': 0.65, 'draw': 0.20, 'away': 0.15, 'winner': 'Home Team'},
            'our_prediction': {'home': 0.68, 'draw': 0.18, 'away': 0.14},
            'statistics': {
                'expected_goals_home': 2.10,
                'expected_goals_away': 0.80,
                'home_form': {'form_string': 'WWDWL'},
                'away_form': {'form_string': 'LWWDL'},
                'home_matches': 12,
                'away_matches': 12
            },
            'goal_ranges': {'0-1': 0.35, '2-3': 0.45, '4+': 0.20},
            'footystats': {
                'quality_score': 85,
                'btts_probability': 0.45,
                'over_25_probability': 0.60,
                'match_intensity': 'High'
            },
            'has_value': True,
            'value_bet': {
                'outcome': 'Home Win',
                'edge': 0.125,
                'suggested_stake': 0.04,
                'odds': 2.10
            }
        }
    }

    # Generate 4 matches covering different scenarios
    results = []
    
    # 1. High Confidence Value Bet
    m1 = copy.deepcopy(base_match)
    m1['fixture']['teams']['home']['name'] = "Manchester City"
    m1['fixture']['teams']['away']['name'] = "Liverpool"
    results.append(m1)
    
    # 2. No Value Bet
    m2 = copy.deepcopy(base_match)
    m2['fixture']['teams']['home']['name'] = "Real Madrid"
    m2['fixture']['teams']['away']['name'] = "Barcelona"
    m2['confidence'] = 3
    m2['analysis']['has_value'] = False
    m2['analysis']['value_bet'] = None
    m2['analysis']['footystats']['match_intensity'] = 'Medium'
    results.append(m2)
    
    # 3. Low Intensity / No FootyStats
    m3 = copy.deepcopy(base_match)
    m3['fixture']['teams']['home']['name'] = "Getafe"
    m3['fixture']['teams']['away']['name'] = "Valencia"
    m3['confidence'] = 2
    m3['analysis']['footystats'] = None
    results.append(m3)

    output_path = PDFService.generate_league_weekly_report(
        "Liga Test Completa",
        results,
        output_dir="/tmp"
    )
    
    print(f"✅ PDF generado en: {output_path}")
    
    if os.path.exists(output_path):
        print("✅ Archivo existe y tiene tamaño:", os.path.getsize(output_path), "bytes")
    else:
        print("❌ Error: Archivo no encontrado")

if __name__ == "__main__":
    test_professional_pdf()
