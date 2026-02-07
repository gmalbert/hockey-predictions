"""Update NHL injuries from CBS Sports."""
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.injury_scraper import scrape_cbs_injuries, save_injuries_to_file

if __name__ == "__main__":
    print("=" * 60)
    print("NHL INJURY UPDATER - CBS Sports Scraper")
    print("=" * 60)
    print()
    
    print("🔍 Fetching latest injuries from CBS Sports...")
    injuries = scrape_cbs_injuries()
    
    if injuries:
        total = sum(len(inj_list) for inj_list in injuries.values())
        print(f"\n✅ Found {total} injuries across {len(injuries)} teams\n")
        
        # Show summary by team (first 10 teams)
        for team, inj_list in list(injuries.items())[:10]:
            print(f"  {team}: {len(inj_list)} injuries")
            for inj in inj_list[:2]:
                print(f"    - {inj['player_name']} ({inj['position']}): {inj['injury_type']}")
        
        if len(injuries) > 10:
            remaining = len(injuries) - 10
            print(f"\n  ... and {remaining} more teams")
        
        # Save to file
        print()
        save_injuries_to_file(injuries)
        
        print("\n" + "=" * 60)
        print("✅ Update Complete!")
        print("=" * 60)
        print("\n💡 Run the app to see injury impacts on predictions:")
        print("   streamlit run predictions.py")
        print()
    else:
        print("\n❌ Failed to fetch injuries from CBS Sports")
        print("   Check your internet connection and try again")
