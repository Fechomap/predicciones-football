# scripts/validate_integration.py

import sys
import os
import json

# Add src to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.bot_service import BotService
from src.database.connection import db_manager
from src.database.models import Fixture
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def validate_integration():
    """
    Runs a series of checks to validate the new FootyStats integration.
    1. Checks the enhanced analyzer directly (triggers live API call).
    2. Checks the BotService's FootyStats-only analysis path.
    """
    
    print("🚀 Starting FootyStats Integration Validation...")

    try:
        print("   - Initializing database connection...")
        db_manager.initialize()
        print("   - Database initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}", exc_info=True)
        return
    
    try:
        bot_service = BotService()
        enhanced_analyzer = bot_service.enhanced_analyzer
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}", exc_info=True)
        return

    # --- 1. VALIDATE EnhancedAnalyzer (Live API Call) ---
    print("\n[STEP 1/2] Validating EnhancedAnalyzer (triggers live API call)...")
    # Example Match: Manchester United (API ID: 33) vs. Arsenal (API ID: 42) in Premier League (API ID: 39)
    home_id = 33
    away_id = 42
    home_name = "Manchester United"
    away_name = "Arsenal"
    league_id = 39
    
    print(f"   - Analyzing: {home_name} vs. {away_name} (League ID: {league_id})")
    
    try:
        analysis = enhanced_analyzer.analyze_match_quality(
            home_team_id=home_id,
            away_team_id=away_id,
            home_team_name=home_name,
            away_team_name=away_name,
            league_id=league_id
        )
        
        if analysis and analysis.get('quality_score') is not None:
            print("   ✅ SUCCESS: Received data from EnhancedAnalyzer.")
            print("      - Quality Score:", analysis.get('quality_score'))
            print("      - BTTS Probability:", analysis.get('btts_probability'))
        else:
            print("   ⚠️ WARNING: EnhancedAnalyzer returned no data or an incomplete response.")
            print("      - Response:", analysis)

    except Exception as e:
        logger.error(f"   ❌ FAILED: Error during EnhancedAnalyzer test: {e}", exc_info=True)


    # --- 2. VALIDATE BotService (FootyStats-only analysis path) ---
    print("\n[STEP 2/2] Validating BotService's 'analyze_fixture_footystats' method...")
    
    test_fixture = None
    try:
        with db_manager.get_session() as session:
            # Find an upcoming fixture for a known, mapped team if possible
            # Lets find ANY upcoming fixture for now to test the logic
            orm_fixture = session.query(Fixture).filter(
                Fixture.status == 'NS'
            ).order_by(Fixture.kickoff_time).first()

        if orm_fixture:
            fixture_id = orm_fixture.id
            print(f"   - Found upcoming fixture with ID: {fixture_id}. Using it for the test.")
            test_fixture = bot_service.fixtures_service.get_fixture_by_id(fixture_id)
        else:
            print("   ⚠️ WARNING: No upcoming fixtures found in the database. Cannot perform this validation step.")
            print("\n🏁 Validation Finished (with warnings).")
            return

    except Exception as e:
        logger.error(f"   ❌ FAILED: Could not retrieve a fixture from the database: {e}", exc_info=True)
        return

    if test_fixture:
        try:
            fs_only_analysis = bot_service.analyze_fixture_footystats(test_fixture)
            
            if fs_only_analysis and fs_only_analysis.get('available'):
                 print("   ✅ SUCCESS: Received data from bot_service.analyze_fixture_footystats.")
                 print("      - Quality Score:", fs_only_analysis.get('analysis', {}).get('quality_score'))
            elif fs_only_analysis and not fs_only_analysis.get('available'):
                 print(f"   ⚠️ WARNING: FootyStats data not available for this fixture. Message: {fs_only_analysis.get('message')}")
            else:
                 print("   ❌ FAILED: BotService returned an unexpected response.")
                 print("      - Response:", fs_only_analysis)

        except Exception as e:
            logger.error(f"   ❌ FAILED: Error during BotService test: {e}", exc_info=True)

    print("\n🏁 Validation Finished.")


if __name__ == "__main__":
    validate_integration()