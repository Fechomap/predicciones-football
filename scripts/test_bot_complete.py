#!/usr/bin/env python3
"""
Complete bot simulation - Tests all analysis methods
Simulates the bot without sending notifications
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.bot_service import BotService
from src.database import db_manager
from src.utils.logger import setup_logger
import json
from datetime import datetime

logger = setup_logger(__name__)

def test_complete_bot():
    """Run complete bot simulation with all analysis methods"""

    print("\n" + "="*70)
    print("  🤖 BOT COMPLETE SIMULATION TEST")
    print("="*70 + "\n")

    # Initialize
    try:
        db_manager.initialize()
        bot_service = BotService()
        print("✅ Bot service initialized\n")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False

    # Get a Premier League fixture (teams are mapped)
    print("📋 Fetching test fixture from database...")

    # Try to get a Premier League fixture first (league_id=39)
    with db_manager.get_session() as session:
        from src.database import Fixture, Team, League

        fixture_orm = session.query(Fixture).join(
            League, Fixture.league_id == League.id
        ).filter(
            Fixture.league_id == 39,  # Premier League
            Fixture.status == 'NS'
        ).first()

        # If no Premier League, try any fixture
        if not fixture_orm:
            print("⚠️  No Premier League fixtures, using any available...")
            fixture_orm = session.query(Fixture).filter(
                Fixture.status == 'NS'
            ).first()

        if not fixture_orm:
            print("❌ No fixtures found in database")
            print("💡 Run: python3 scripts/load_full_season_fixtures.py")
            return False

        # Get complete team and league info
        home_team = session.query(Team).filter_by(id=fixture_orm.home_team_id).first()
        away_team = session.query(Team).filter_by(id=fixture_orm.away_team_id).first()
        league = session.query(League).filter_by(id=fixture_orm.league_id).first()

        # Convert to dict format expected by bot_service (API-Football structure)
        fixture = {
            'fixture': {
                'id': fixture_orm.id,
                'date': str(fixture_orm.kickoff_time),
                'timestamp': int(fixture_orm.kickoff_time.timestamp()) if fixture_orm.kickoff_time else None,
                'status': {'short': fixture_orm.status}
            },
            'league': {
                'id': fixture_orm.league_id,
                'name': league.name if league else 'Unknown',
                'country': league.country if league else 'Unknown'
            },
            'teams': {
                'home': {
                    'id': fixture_orm.home_team_id,
                    'name': home_team.name if home_team else 'Unknown'
                },
                'away': {
                    'id': fixture_orm.away_team_id,
                    'name': away_team.name if away_team else 'Unknown'
                }
            }
        }
    print(f"✅ Using fixture: {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
    print(f"   League: {fixture['league']['name']}")
    print(f"   Date: {fixture['fixture']['date']}")
    print(f"   Fixture ID: {fixture['fixture']['id']}\n")

    # Test counters
    tests_passed = 0
    tests_failed = 0

    # ============================================================
    # TEST 1: API-Football AI Analysis
    # ============================================================
    print("="*70)
    print("  [1/4] 🤖 API-FOOTBALL AI ANALYSIS")
    print("="*70)

    try:
        result = bot_service.analyze_fixture_apifootball(fixture)

        if result and result.get('available'):
            analysis = result.get('analysis', {})
            print(f"\n✅ SUCCESS")
            print(f"   Prediction: {analysis.get('prediction', 'N/A')}")
            print(f"   Confidence: {analysis.get('confidence', 'N/A')}")
            print(f"   Win Probability: {analysis.get('win_probability', {})}")
            tests_passed += 1
        else:
            print(f"\n⚠️  Not available: {result.get('message', 'Unknown reason')}")
            tests_failed += 1

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        tests_failed += 1

    # ============================================================
    # TEST 2: Poisson Analysis
    # ============================================================
    print("\n" + "="*70)
    print("  [2/4] 🧮 POISSON ANALYSIS")
    print("="*70)

    try:
        result = bot_service.analyze_fixture_poisson(fixture)

        if result and result.get('available'):
            analysis = result.get('analysis', {})
            print(f"\n✅ SUCCESS")
            print(f"   Expected Goals:")
            print(f"     Home: {analysis.get('expected_goals_home', 'N/A')}")
            print(f"     Away: {analysis.get('expected_goals_away', 'N/A')}")
            print(f"   Probabilities:")
            print(f"     Home win: {analysis.get('home_win_prob', 'N/A')}")
            print(f"     Draw: {analysis.get('draw_prob', 'N/A')}")
            print(f"     Away win: {analysis.get('away_win_prob', 'N/A')}")
            print(f"   BTTS: {analysis.get('btts_prob', 'N/A')}")
            print(f"   Over 2.5: {analysis.get('over_2_5_prob', 'N/A')}")
            tests_passed += 1
        else:
            print(f"\n⚠️  Not available: {result.get('message', 'Unknown reason')}")
            tests_failed += 1

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        tests_failed += 1

    # ============================================================
    # TEST 3: FootyStats Analysis (NEW)
    # ============================================================
    print("\n" + "="*70)
    print("  [3/4] 📈 FOOTYSTATS ANALYSIS")
    print("="*70)

    try:
        result = bot_service.analyze_fixture_footystats(fixture)

        if result and result.get('available'):
            analysis = result.get('analysis', {})
            print(f"\n✅ SUCCESS")
            print(f"   Quality Score: {analysis.get('quality_score', 'N/A')}/100")
            print(f"   Match Intensity: {analysis.get('match_intensity', 'N/A')}")
            print(f"   BTTS Probability: {analysis.get('btts_probability', 'N/A')}")
            print(f"   Over 2.5 Probability: {analysis.get('over_2_5_probability', 'N/A')}")

            home_stats = analysis.get('home_stats', {})
            away_stats = analysis.get('away_stats', {})
            print(f"\n   Home Team Stats:")
            print(f"     Avg Goals Scored: {home_stats.get('avg_goals_scored', 'N/A')}")
            print(f"     Avg Goals Conceded: {home_stats.get('avg_goals_conceded', 'N/A')}")
            print(f"     BTTS %: {home_stats.get('btts_percentage', 'N/A')}")

            print(f"\n   Away Team Stats:")
            print(f"     Avg Goals Scored: {away_stats.get('avg_goals_scored', 'N/A')}")
            print(f"     Avg Goals Conceded: {away_stats.get('avg_goals_conceded', 'N/A')}")
            print(f"     BTTS %: {away_stats.get('btts_percentage', 'N/A')}")
            tests_passed += 1
        else:
            print(f"\n⚠️  Not available: {result.get('message', 'Unknown reason')}")
            print(f"   (This is expected if teams are not mapped yet)")
            tests_failed += 1

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        logger.error("FootyStats analysis error", exc_info=True)
        tests_failed += 1

    # ============================================================
    # TEST 4: Complete Analysis (All methods combined)
    # ============================================================
    print("\n" + "="*70)
    print("  [4/4] 📊 COMPLETE ANALYSIS (ALL METHODS)")
    print("="*70)

    try:
        # This is the main analysis method that combines everything
        analysis_result = bot_service.analyze_fixture(fixture)

        if analysis_result:
            print(f"\n✅ SUCCESS - Complete analysis generated")
            print(f"\n   Prediction: {analysis_result.get('prediction', 'N/A')}")
            print(f"   Expected Goals: Home {analysis_result.get('expected_goals_home', 'N/A')} - Away {analysis_result.get('expected_goals_away', 'N/A')}")
            print(f"   Confidence Rating: {analysis_result.get('confidence_rating', 'N/A')}")

            # Value bets
            value_bets = analysis_result.get('value_bets', [])
            if value_bets:
                print(f"\n   💰 Value Bets Found: {len(value_bets)}")
                for bet in value_bets[:3]:  # Show first 3
                    print(f"      • {bet.get('bet_type')} - Edge: {bet.get('edge', 0):.1f}%")
            else:
                print(f"\n   No value bets identified")

            tests_passed += 1
        else:
            print(f"\n❌ Analysis returned None")
            tests_failed += 1

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        logger.error("Complete analysis error", exc_info=True)
        tests_failed += 1

    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "="*70)
    print("  📊 TEST SUMMARY")
    print("="*70)
    print(f"\n  Tests Passed: {tests_passed}/4")
    print(f"  Tests Failed: {tests_failed}/4")

    if tests_failed == 0:
        print("\n  ✅ ALL TESTS PASSED - BOT FUNCTIONING 100%")
        print("="*70 + "\n")
        return True
    else:
        print(f"\n  ⚠️  {tests_failed} test(s) failed (may be expected if data not available)")
        print("="*70 + "\n")
        return tests_passed >= 2  # At least 50% should pass


if __name__ == "__main__":
    success = test_complete_bot()
    sys.exit(0 if success else 1)
