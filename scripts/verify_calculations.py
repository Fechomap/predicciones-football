import sys
import os
import asyncio
import logging

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.bot_service import BotService
from src.database import db_manager
from src.utils.logger import setup_logger

# Setup logger
logger = setup_logger("verify_calc", level="INFO")

async def verify_calculations():
    """
    Verifica los cálculos para los partidos de Liga MX
    """
    # Inicializar DB
    db_manager.initialize()
    
    bot_service = BotService()
    
    # ID de Liga MX
    LEAGUE_ID = 262 
    
    print(f"\n🔍 VERIFICANDO CÁLCULOS PARA LIGA {LEAGUE_ID}...\n")
    
    # 1. Obtener fixtures
    fixtures_service = bot_service.fixtures_service
    upcoming = fixtures_service.get_upcoming_fixtures(hours_ahead=360, force_refresh=False)
    league_fixtures = [f for f in upcoming if f['league']['id'] == LEAGUE_ID]
    
    print(f"Encontrados {len(league_fixtures)} partidos para la liga.\n")
    
    for fixture in league_fixtures:
        fix_id = fixture['fixture']['id']
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        date = fixture['fixture']['date']
        
        print(f"⚽ {home} vs {away} (ID: {fix_id}) - {date}")
        
        # 2. Analizar (usando la misma lógica del bot)
        # Forzamos refresh para ver los datos crudos de la API
        analysis = bot_service.analyze_fixture(fixture)
        
        if not analysis:
            print("   ❌ No se pudo analizar")
            continue
            
        # 3. Inspeccionar Predicción API
        api_pred = analysis.get('api_prediction', {})
        print(f"   🤖 API Prediction Raw: {api_pred}")
        
        # 4. Inspeccionar Predicción Poisson (Nuestra)
        our_pred = analysis.get('our_prediction', {})
        stats = analysis.get('statistics', {})
        
        print(f"   📊 Stats Base:")
        print(f"      - Home Attack: {stats.get('home_attack_strength', 0):.2f}")
        print(f"      - Home Defense: {stats.get('home_defense_strength', 0):.2f}")
        print(f"      - Away Attack: {stats.get('away_attack_strength', 0):.2f}")
        print(f"      - Away Defense: {stats.get('away_defense_strength', 0):.2f}")
        print(f"      - League Avg Goals: {stats.get('league_avg_goals', 0):.2f}")
        
        print(f"   🧮 Poisson Calculation:")
        print(f"      - Expected Home Goals: {stats.get('expected_goals_home', 0):.2f}")
        print(f"      - Expected Away Goals: {stats.get('expected_goals_away', 0):.2f}")
        print(f"      - Probabilities: Home={our_pred.get('home', 0):.1%}, Draw={our_pred.get('draw', 0):.1%}, Away={our_pred.get('away', 0):.1%}")
        
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(verify_calculations())
