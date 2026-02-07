"""Automatically fetch NHL game schedules for GitHub Actions."""
import sys
from pathlib import Path
from datetime import datetime, date, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.nhl_client import NHLClient


def fetch_game_schedules(days_ahead: int = 10):
    """
    Fetch and cache game schedules for upcoming days.
    
    Args:
        days_ahead: Number of days ahead to fetch (default: 10)
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting game schedule fetch...")
    print(f"Fetching schedules for the next {days_ahead} days\n")
    
    client = NHLClient(cache_ttl_minutes=1440)  # 24 hour cache for schedules
    
    total_games = 0
    dates_fetched = 0
    errors = 0
    
    # Fetch schedules for each day
    for day_offset in range(days_ahead):
        fetch_date = date.today() + timedelta(days=day_offset)
        date_str = fetch_date.isoformat()
        
        try:
            schedule = client.get_schedule(date_str)
            
            # Count games for this date
            games_count = 0
            for game_week in schedule.get("gameWeek", []):
                games_count += len(game_week.get("games", []))
            
            total_games += games_count
            dates_fetched += 1
            
            if games_count > 0:
                print(f"✅ {date_str}: {games_count} games cached")
            else:
                print(f"ℹ️  {date_str}: No games scheduled")
                
        except Exception as e:
            errors += 1
            print(f"❌ {date_str}: Error fetching schedule - {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 SUMMARY")
    print("=" * 60)
    print(f"Dates fetched: {dates_fetched}/{days_ahead}")
    print(f"Total games cached: {total_games}")
    print(f"Errors: {errors}")
    print("=" * 60)
    
    if errors > 0:
        print("\n⚠️  Some schedules failed to fetch - check API connectivity")
        sys.exit(1)
    elif total_games == 0:
        print("\nℹ️  No games found in the next {days_ahead} days")
        print("   This is normal during off-season or breaks")
    else:
        print(f"\n✅ Successfully cached {total_games} games")
    
    return {
        "dates_fetched": dates_fetched,
        "total_games": total_games,
        "errors": errors
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch NHL game schedules")
    parser.add_argument(
        "--days",
        type=int,
        default=10,
        help="Number of days ahead to fetch (default: 10)"
    )
    
    args = parser.parse_args()
    
    try:
        fetch_game_schedules(days_ahead=args.days)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
