"""Store and retrieve historical odds."""
import json
from pathlib import Path
from datetime import datetime, date
from typing import List, Optional, Dict

ODDS_DIR = Path("data_files/odds")

def save_odds_snapshot(
    game_id: str,
    home_team: str,
    away_team: str,
    home_ml: int,
    away_ml: int,
    total: float,
    over_odds: int,
    under_odds: int,
    home_pl_odds: int = -110,
    away_pl_odds: int = -110
) -> None:
    """Save current odds snapshot."""
    ODDS_DIR.mkdir(parents=True, exist_ok=True)
    
    file_path = ODDS_DIR / f"{game_id}.json"
    
    # Load existing or create new
    if file_path.exists():
        data = json.loads(file_path.read_text())
    else:
        data = {
            "game_id": game_id,
            "home_team": home_team,
            "away_team": away_team,
            "snapshots": []
        }
    
    # Add new snapshot
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "home_ml": home_ml,
        "away_ml": away_ml,
        "total": total,
        "over_odds": over_odds,
        "under_odds": under_odds,
        "home_pl_odds": home_pl_odds,
        "away_pl_odds": away_pl_odds
    }
    data["snapshots"].append(snapshot)
    
    file_path.write_text(json.dumps(data, indent=2))

def get_game_odds_history(game_id: str) -> Optional[dict]:
    """Get all odds snapshots for a game."""
    file_path = ODDS_DIR / f"{game_id}.json"
    if file_path.exists():
        return json.loads(file_path.read_text())
    return None

def get_todays_movements() -> List[dict]:
    """Get line movements for today's games."""
    movements = []
    
    for odds_file in ODDS_DIR.glob("*.json"):
        data = json.loads(odds_file.read_text())
        snapshots = data.get("snapshots", [])
        
        if len(snapshots) < 2:
            continue
        
        opening = snapshots[0]
        current = snapshots[-1]
        
        ml_move = current["home_ml"] - opening["home_ml"]
        total_move = current["total"] - opening["total"]
        
        if abs(ml_move) >= 10 or abs(total_move) >= 0.5:
            movements.append({
                "game_id": data["game_id"],
                "matchup": f"{data['away_team']} @ {data['home_team']}",
                "ml_move": ml_move,
                "total_move": total_move,
                "opening_ml": opening["home_ml"],
                "current_ml": current["home_ml"],
                "opening_total": opening["total"],
                "current_total": current["total"],
                "num_snapshots": len(snapshots)
            })
    
    return movements

def get_all_odds_files() -> List[Dict[str, any]]:
    """Get metadata for all tracked odds files."""
    files = []
    
    if not ODDS_DIR.exists():
        return files
    
    for odds_file in ODDS_DIR.glob("*.json"):
        data = json.loads(odds_file.read_text())
        snapshots = data.get("snapshots", [])
        
        if snapshots:
            files.append({
                "game_id": data.get("game_id"),
                "matchup": f"{data.get('away_team')} @ {data.get('home_team')}",
                "num_snapshots": len(snapshots),
                "first_snapshot": snapshots[0]["timestamp"][:19],
                "last_snapshot": snapshots[-1]["timestamp"][:19]
            })
    
    return files
