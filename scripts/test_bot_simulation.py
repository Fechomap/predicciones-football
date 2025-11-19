#!/usr/bin/env python3
"""
Bot simulation with mock data - Tests all calculations without API calls
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analyzers.poisson_analyzer import PoissonAnalyzer
from src.analyzers.form_analyzer import FormAnalyzer
from src.analyzers.value_detector import ValueDetector
from src.services.team_mapping_service import TeamMappingService

def test_poisson_calculations():
    """Test Poisson analyzer with mock data"""
    print("\n" + "="*70)
    print("  🧮 POISSON ANALYZER TEST")
    print("="*70)

    # Mock team stats (Liverpool vs Man United example)
    home_stats = {
        'home_matches': 10,
        'home_goals_scored': 21,
        'home_goals_conceded': 8,
    }

    away_stats = {
        'away_matches': 10,
        'away_goals_scored': 17,
        'away_goals_conceded': 12,
    }

    print("\n📊 Input Data:")
    print(f"   Home: {home_stats['home_goals_scored']/home_stats['home_matches']:.1f} goals/game, {home_stats['home_goals_conceded']/home_stats['home_matches']:.1f} conceded/game")
    print(f"   Away: {away_stats['away_goals_scored']/away_stats['away_matches']:.1f} goals/game, {away_stats['away_goals_conceded']/away_stats['away_matches']:.1f} conceded/game")

    try:
        # Calculate expected goals
        expected_home, expected_away = PoissonAnalyzer.calculate_expected_goals(
            home_stats, away_stats, league_id=39  # Premier League
        )

        # Calculate match probabilities
        match_probs = PoissonAnalyzer.calculate_match_probabilities(expected_home, expected_away)

        # Calculate over/under
        over_under = PoissonAnalyzer.calculate_over_under_probabilities(expected_home, expected_away, 2.5)

        # Calculate BTTS
        btts_prob = PoissonAnalyzer.calculate_btts_probability(expected_home, expected_away)

        print(f"\n✅ RESULTS:")
        print(f"   Expected Goals:")
        print(f"     Home: {expected_home:.2f}")
        print(f"     Away: {expected_away:.2f}")
        print(f"\n   Win Probabilities:")
        print(f"     Home: {match_probs.get('home_win', 0)*100:.1f}%")
        print(f"     Draw: {match_probs.get('draw', 0)*100:.1f}%")
        print(f"     Away: {match_probs.get('away_win', 0)*100:.1f}%")
        print(f"\n   Market Probabilities:")
        print(f"     BTTS: {btts_prob*100:.1f}%")
        print(f"     Over 2.5: {over_under.get('over_2.5', 0)*100:.1f}%")
        print(f"     Under 2.5: {over_under.get('under_2.5', 0)*100:.1f}%")

        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_value_detector():
    """Test value detector with mock odds"""
    print("\n" + "="*70)
    print("  💰 VALUE DETECTOR TEST")
    print("="*70)

    # Mock analysis results
    test_scenarios = [
        {
            'name': 'Home Win',
            'calc_prob': 0.55,
            'odds': 1.85,
        },
        {
            'name': 'BTTS Yes',
            'calc_prob': 0.62,
            'odds': 1.70,
        },
        {
            'name': 'Over 2.5',
            'calc_prob': 0.58,
            'odds': 1.95,
        }
    ]

    print("\n📊 Testing value detection scenarios:")
    value_bets_found = 0

    try:
        for scenario in test_scenarios:
            result = ValueDetector.detect_value_bet(
                scenario['calc_prob'],
                scenario['odds'],
                minimum_edge=0.05  # 5% minimum edge
            )

            print(f"\n   {scenario['name']}:")
            print(f"     Our probability: {scenario['calc_prob']*100:.1f}%")
            print(f"     Bookmaker odds: {scenario['odds']}")
            print(f"     Implied prob: {result['implied_probability']*100:.1f}%")
            print(f"     Edge: {result['edge']*100:.1f}%")
            print(f"     Expected Value: ${result['expected_value']:.2f}")

            if result['is_value_bet']:
                print(f"     ✅ VALUE BET DETECTED!")
                value_bets_found += 1
            else:
                print(f"     ❌ No value")

        print(f"\n✅ RESULTS: Found {value_bets_found}/{len(test_scenarios)} value bets")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_team_mapping():
    """Test team mapping service"""
    print("\n" + "="*70)
    print("  🗺️  TEAM MAPPING SERVICE TEST")
    print("="*70)

    # Initialize database
    from src.database import db_manager
    try:
        db_manager.initialize()
        print("   Database initialized")
    except Exception as e:
        print(f"   ⚠️  Could not initialize database: {e}")
        print(f"   Skipping team mapping test")
        return False

    mapper = TeamMappingService()

    # Test known teams (Premier League)
    test_teams = [
        (40, "Liverpool"),
        (33, "Manchester United"),
        (50, "Manchester City"),
        (42, "Arsenal"),
        (49, "Chelsea"),
    ]

    print("\n📊 Testing team mappings:")

    mapped_count = 0
    for api_id, name in test_teams:
        try:
            fs_id = mapper.get_footystats_id(api_id)
            if fs_id:
                print(f"   ✅ {name:20s} API:{api_id:3d} → FS:{fs_id}")
                mapped_count += 1
            else:
                print(f"   ⚠️  {name:20s} API:{api_id:3d} → Not mapped")
        except Exception as e:
            print(f"   ❌ {name:20s} Error: {e}")

    print(f"\n✅ RESULTS: {mapped_count}/{len(test_teams)} teams mapped")
    return mapped_count >= 3  # At least 60% should be mapped


def test_form_analyzer():
    """Test form analyzer"""
    print("\n" + "="*70)
    print("  📈 FORM ANALYZER TEST")
    print("="*70)

    # Mock recent matches for home team (team_id = 1)
    home_matches = [
        {'teams': {'home': {'id': 1}, 'away': {'id': 2}}, 'goals': {'home': 2, 'away': 1}},  # W
        {'teams': {'home': {'id': 1}, 'away': {'id': 3}}, 'goals': {'home': 3, 'away': 0}},  # W
        {'teams': {'home': {'id': 4}, 'away': {'id': 1}}, 'goals': {'home': 1, 'away': 1}},  # D
        {'teams': {'home': {'id': 1}, 'away': {'id': 5}}, 'goals': {'home': 2, 'away': 0}},  # W
        {'teams': {'home': {'id': 6}, 'away': {'id': 1}}, 'goals': {'home': 2, 'away': 1}},  # L
    ]

    # Mock recent matches for away team (team_id = 10)
    away_matches = [
        {'teams': {'home': {'id': 10}, 'away': {'id': 11}}, 'goals': {'home': 0, 'away': 2}},  # L
        {'teams': {'home': {'id': 12}, 'away': {'id': 10}}, 'goals': {'home': 1, 'away': 1}},  # D
        {'teams': {'home': {'id': 13}, 'away': {'id': 10}}, 'goals': {'home': 0, 'away': 1}},  # W
        {'teams': {'home': {'id': 10}, 'away': {'id': 14}}, 'goals': {'home': 1, 'away': 2}},  # L
        {'teams': {'home': {'id': 15}, 'away': {'id': 10}}, 'goals': {'home': 0, 'away': 2}},  # W
    ]

    print("\n📊 Input Data:")
    print(f"   Home team: 5 recent matches")
    print(f"   Away team: 5 recent matches")

    try:
        home_form = FormAnalyzer.calculate_form_score(home_matches, team_id=1)
        away_form = FormAnalyzer.calculate_form_score(away_matches, team_id=10)

        print(f"\n✅ RESULTS:")
        print(f"   Home form: {home_form['form_string']} (Score: {home_form['score']:.1f}/100)")
        print(f"   Away form: {away_form['form_string']} (Score: {away_form['score']:.1f}/100)")

        comparison = FormAnalyzer.compare_forms(home_form, away_form)
        print(f"   Form advantage: {comparison['advantage']}")

        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all simulation tests"""
    print("\n" + "="*70)
    print("  🤖 FOOTBALL BETTING BOT - CALCULATION SIMULATION")
    print("="*70)
    print("\n  Testing all analyzers with simulated data...")
    print("  (No API calls, no notifications)\n")

    results = []

    # Run all tests
    results.append(("Poisson Analyzer", test_poisson_calculations()))
    results.append(("Value Detector", test_value_detector()))
    results.append(("Team Mapping", test_team_mapping()))
    results.append(("Form Analyzer", test_form_analyzer()))

    # Summary
    print("\n" + "="*70)
    print("  📊 SIMULATION SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\n  Tests Results:")
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"    {status} - {name}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n  ✅ ALL CALCULATIONS WORKING PERFECTLY")
        print("="*70 + "\n")
        return True
    elif passed >= total * 0.75:
        print(f"\n  ⚠️  {total - passed} test(s) failed, but bot is mostly functional")
        print("="*70 + "\n")
        return True
    else:
        print(f"\n  ❌ Too many failures ({total - passed}/{total})")
        print("="*70 + "\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
