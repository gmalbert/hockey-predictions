"""
Quick test to verify all Data Gathering Roadmap tasks are working.
Run this to verify the implementation after setup.
"""
import sys
from pathlib import Path

# ensure src package is importable when running under pytest
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.nhl_client import NHLClient
from src.utils.cache import get_cache_size_mb, clear_old_cache

def main():
    print("\n" + "="*60)
    print("DATA GATHERING ROADMAP - VERIFICATION TEST")
    print("="*60)
    
    # Initialize client
    client = NHLClient()
    
    # Test each phase
    test_phase_1(client)
    test_phase_2(client)
    test_phase_3(client)
    test_additional_features(client)
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED - ROADMAP FULLY IMPLEMENTED")
    print("="*60 + "\n")

def test_phase_1(client):
    """Test Phase 1: Core API Client Setup"""
    print("\n📦 PHASE 1: Core API Client Setup")
    print("-"*60)
    
    # Task 1.1: Base HTTP Client
    assert hasattr(client, '_fetch_sync'), "Missing _fetch_sync method"
    assert hasattr(client, 'CACHE_DIR'), "Missing CACHE_DIR"
    assert hasattr(client, 'TEAM_ID_MAP'), "Missing TEAM_ID_MAP"
    print("✅ Task 1.1: Base HTTP Client - PASS")
    
    # Task 1.2: Synchronous wrapper (not needed)
    print("✅ Task 1.2: Synchronous Wrapper - NOT NEEDED")

def test_phase_2(client):
    """Test Phase 2: Essential Data Endpoints"""
    print("\n📊 PHASE 2: Essential Data Endpoints")
    print("-"*60)
    
    # Task 2.1: Today's Schedule
    games = client.get_todays_games()
    assert isinstance(games, list), "get_todays_games should return list"
    print(f"✅ Task 2.1: Today's Schedule - {len(games)} games")
    
    # Task 2.2: Team Statistics
    summary = client.get_team_summary('TOR')
    assert summary is not None, "get_team_summary should return data"
    assert 'wins' in summary, "Summary should have wins"
    print(f"✅ Task 2.2: Team Statistics - TOR: {summary['wins']}-{summary['losses']}-{summary['ot_losses']}")

    # historical and current team mapping
    hist = client.get_team_summary('ARI', season='20232024')
    assert hist is not None, "Historical ARI should return stats"
    assert hist['team'] == 'ARI'
    curr = client.get_team_summary('UTA')
    # when Utah stats aren't published, fallback returns Arizona data
    assert curr is not None, "get_team_summary('UTA') should return data via fallback"
    assert curr['team'] == 'ARI', "Fallback should use Arizona summary"
    print(f"✅ ARI/UTA mapping validated (historic {hist['wins']} wins, fallback record {curr['wins']}-{curr['losses']})")
    
    # Task 2.3: Player Statistics
    skaters = client.get_skater_stats(limit=5)
    goalies = client.get_goalie_stats(limit=3)
    assert len(skaters) > 0, "Should return skater stats"
    assert len(goalies) > 0, "Should return goalie stats"
    print(f"✅ Task 2.3: Player Statistics - {len(skaters)} skaters, {len(goalies)} goalies")

def test_phase_3(client):
    """Test Phase 3: Historical Data Collection"""
    print("\n📈 PHASE 3: Historical Data Collection")
    print("-"*60)
    
    # Task 3.1: Game Results History
    games = client.get_season_games('TOR')
    assert isinstance(games, list), "get_season_games should return list"
    assert len(games) > 0, "Should have completed games"
    print(f"✅ Task 3.1: Game Results History - {len(games)} completed games")
    
    # Task 3.2: Cache Management
    cache_size = get_cache_size_mb()
    removed = clear_old_cache(max_age_hours=720)  # 30 days
    assert cache_size >= 0, "Cache size should be non-negative"
    print(f"✅ Task 3.2: Cache Management - {cache_size} MB, {removed} old files removed")

def test_additional_features(client):
    """Test Additional Implemented Features"""
    print("\n🎯 ADDITIONAL FEATURES")
    print("-"*60)
    
    # Standings
    standings = client.get_standings()
    assert 'standings' in standings, "Should return standings data"
    print(f"✅ Standings - {len(standings.get('standings', []))} teams")
    
    # ESPN Odds
    odds = client.get_espn_odds(days_ahead=3)
    assert isinstance(odds, list), "Should return odds list"
    print(f"✅ ESPN Odds - {len(odds)} games with odds")

if __name__ == "__main__":
    main()
