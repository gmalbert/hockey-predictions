"""
Test script for UI Layout implementation.
Verifies all pages can be imported and key components work.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all page modules can be imported."""
    print("\n" + "="*60)
    print("TESTING UI LAYOUT IMPLEMENTATION")
    print("="*60)
    
    print("\n📦 Testing Page Imports...")
    
    # Test each page can be imported
    pages = [
        ("Main App", "src.app"),
        ("Today's Games", "src.pages.1_📅_Todays_Games"),
        ("Team Stats", "src.pages.2_📊_Team_Stats"),
        ("Standings", "src.pages.3_🏆_Standings"),
        ("Value Finder", "src.pages.4_💰_Value_Finder"),
        ("Player Props", "src.pages.5_🎯_Player_Props"),
        ("Performance", "src.pages.6_📈_Performance"),
    ]
    
    passed = 0
    failed = 0
    
    for name, module_path in pages:
        try:
            # Try to import the module
            __import__(module_path)
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            failed += 1
    
    print(f"\n📊 Import Results: {passed} passed, {failed} failed")
    return failed == 0


def test_utilities():
    """Test utility functions."""
    print("\n🔧 Testing Utilities...")
    
    try:
        from src.utils.styles import (
            apply_custom_css,
            format_odds,
            calculate_implied_probability,
            kelly_criterion,
            american_to_decimal
        )
        
        # Test format_odds
        assert format_odds(-110) == "-110", "format_odds failed for negative"
        assert format_odds(150) == "+150", "format_odds failed for positive"
        assert format_odds(None) == "N/A", "format_odds failed for None"
        print("  ✅ format_odds")
        
        # Test calculate_implied_probability
        prob = calculate_implied_probability(-110)
        assert prob is not None and 0.5 < prob < 0.6, "implied probability -110 failed"
        print("  ✅ calculate_implied_probability")
        
        # Test american_to_decimal
        decimal = american_to_decimal(-110)
        assert decimal is not None and 1.9 < decimal < 2.0, "american_to_decimal failed"
        print("  ✅ american_to_decimal")
        
        # Test kelly_criterion
        kelly = kelly_criterion(0.55, 2.0)
        assert kelly is not None and kelly > 0, "kelly_criterion failed"
        print("  ✅ kelly_criterion")
        
        print("  ✅ All utility functions working")
        return True
        
    except Exception as e:
        print(f"  ❌ Utility test failed: {e}")
        return False


def test_data_integration():
    """Test that pages can access NHL client."""
    print("\n📡 Testing Data Integration...")
    
    try:
        from src.api.nhl_client import NHLClient
        
        client = NHLClient()
        
        # Test basic API calls
        games = client.get_todays_games()
        print(f"  ✅ Today's games: {len(games)} games")
        
        standings = client.get_standings()
        teams = standings.get("standings", [])
        print(f"  ✅ Standings: {len(teams)} teams")
        
        team_stats = client.get_team_summary("TOR")
        if team_stats:
            print(f"  ✅ Team stats: TOR {team_stats['wins']}-{team_stats['losses']}-{team_stats['ot_losses']}")
        else:
            print("  ⚠️  Team stats: No data for TOR")
        
        skaters = client.get_skater_stats(limit=5)
        print(f"  ✅ Skater stats: {len(skaters)} players")
        
        odds = client.get_espn_odds(days_ahead=1)
        print(f"  ✅ ESPN odds: {len(odds)} games")
        
        print("  ✅ All data integration tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Data integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_page_structure():
    """Verify page files exist and have correct structure."""
    print("\n📄 Testing Page Structure...")
    
    pages_dir = Path(__file__).parent.parent / "src" / "pages"
    
    expected_pages = [
        "1_📅_Todays_Games.py",
        "2_📊_Team_Stats.py",
        "3_🏆_Standings.py",
        "4_💰_Value_Finder.py",
        "5_🎯_Player_Props.py",
        "6_📈_Performance.py",
    ]
    
    passed = 0
    for page in expected_pages:
        page_path = pages_dir / page
        if page_path.exists():
            # Check file has content
            try:
                content = page_path.read_text(encoding='utf-8')
                if len(content) > 100 and "st.set_page_config" in content:
                    print(f"  ✅ {page}")
                    passed += 1
                else:
                    print(f"  ⚠️  {page} - file exists but may be incomplete")
            except Exception as e:
                print(f"  ⚠️  {page} - error reading file: {e}")
        else:
            print(f"  ❌ {page} - not found")
    
    print(f"\n  {passed}/{len(expected_pages)} pages verified")
    return passed == len(expected_pages)


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("UI LAYOUT ROADMAP - VERIFICATION TESTS")
    print("="*60)
    
    results = {
        "Page Structure": test_page_structure(),
        "Page Imports": test_imports(),
        "Utilities": test_utilities(),
        "Data Integration": test_data_integration(),
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED - UI LAYOUT FULLY IMPLEMENTED")
        print("="*60)
        print("\nYou can now run the app with:")
        print("  streamlit run predictions.py")
        print("\nOr navigate to specific pages from the sidebar.")
    else:
        print("\n" + "="*60)
        print("❌ SOME TESTS FAILED - CHECK OUTPUT ABOVE")
        print("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
