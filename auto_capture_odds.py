"""Automatically capture odds snapshots for GitHub Actions."""
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.nhl_client import NHLClient
from src.utils.odds_storage import save_odds_snapshot


def capture_odds_snapshots():
    """Capture current odds for upcoming games."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting odds capture...")
    
    client = NHLClient()
    
    # Get odds for next 3 days (focus on near-term games)
    try:
        odds_data = client.get_espn_odds(days_ahead=3)
        print(f"Found {len(odds_data)} games with odds data")
        
        if not odds_data:
            print("ℹ️  No upcoming games found in the next 3 days")
            print("   This is normal if there are no scheduled games")
            return
    except Exception as e:
        print(f"❌ Error fetching odds: {e}")
        import traceback
        traceback.print_exc()
        return
    
    captured_count = 0
    skipped_count = 0
    
    for game in odds_data:
        game_id = game.get("game_id")
        home_team = game.get("home_team")
        away_team = game.get("away_team")
        odds_list = game.get("odds", [])
        
        if not game_id or not home_team or not away_team:
            skipped_count += 1
            continue
        
        # Use DraftKings odds (preferred) or first available provider
        draftkings_odds = None
        for odds_provider in odds_list:
            if odds_provider.get("provider") == "DraftKings":
                draftkings_odds = odds_provider
                break
        
        # Fallback to first provider if DraftKings not available
        selected_odds = draftkings_odds or (odds_list[0] if odds_list else None)
        
        if not selected_odds:
            print(f"⚠️  No odds available for {away_team} @ {home_team}")
            skipped_count += 1
            continue
        
        # Extract odds values with fallbacks
        home_ml = selected_odds.get("moneyline", {}).get("home")
        away_ml = selected_odds.get("moneyline", {}).get("away")
        
        total_over = selected_odds.get("total", {}).get("over", {})
        total_under = selected_odds.get("total", {}).get("under", {})
        total_line = total_over.get("line") or total_under.get("line")
        over_odds = total_over.get("odds")
        under_odds = total_under.get("odds")
        
        spread_home = selected_odds.get("spread", {}).get("home", {})
        spread_away = selected_odds.get("spread", {}).get("away", {})
        home_pl_odds = spread_home.get("odds")
        away_pl_odds = spread_away.get("odds")
        
        # Only save if we have at least moneyline odds
        if home_ml is not None and away_ml is not None:
            try:
                save_odds_snapshot(
                    game_id=str(game_id),
                    home_team=home_team,
                    away_team=away_team,
                    home_ml=int(home_ml),
                    away_ml=int(away_ml),
                    total=float(total_line) if total_line else 6.5,  # Default NHL total
                    over_odds=int(over_odds) if over_odds else -110,
                    under_odds=int(under_odds) if under_odds else -110,
                    home_pl_odds=int(home_pl_odds) if home_pl_odds else -110,
                    away_pl_odds=int(away_pl_odds) if away_pl_odds else -110
                )
                captured_count += 1
                print(f"✅ Captured: {away_team} @ {home_team} (ML: {away_ml}/{home_ml})")
            except Exception as e:
                print(f"❌ Error saving {away_team} @ {home_team}: {e}")
                skipped_count += 1
        else:
            print(f"⚠️  Incomplete odds for {away_team} @ {home_team}")
            skipped_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Captured: {captured_count} games")
    print(f"   ⚠️  Skipped: {skipped_count} games")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Capture complete!")


if __name__ == "__main__":
    capture_odds_snapshots()
