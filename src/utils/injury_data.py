"""Injury data persistence."""
from datetime import datetime
from typing import List, Dict
from pathlib import Path
import json

INJURY_FILE = "data_files/injuries.json"

def load_injuries() -> Dict[str, List[dict]]:
    """Load current injury data from file."""
    path = Path(INJURY_FILE)
    if path.exists():
        return json.loads(path.read_text())
    return {}

def load_team_injuries(team: str) -> List[dict]:
    """Get injuries for a specific team."""
    injuries = load_injuries()
    return injuries.get(team, [])

def save_injury(
    player_name: str,
    team: str,
    position: str,
    status: str,
    injury_type: str,
    player_tier: str = "medium"
) -> None:
    """Manually add/update an injury."""
    injuries = load_injuries()
    
    if team not in injuries:
        injuries[team] = []
    
    # Update or add
    for i, inj in enumerate(injuries[team]):
        if inj["player_name"] == player_name:
            injuries[team][i] = {
                "player_name": player_name,
                "position": position,
                "status": status,
                "injury_type": injury_type,
                "player_tier": player_tier.lower(),
                "updated": datetime.now().isoformat()
            }
            break
    else:
        injuries[team].append({
            "player_name": player_name,
            "position": position,
            "status": status,
            "injury_type": injury_type,
            "player_tier": player_tier.lower(),
            "updated": datetime.now().isoformat()
        })
    
    Path(INJURY_FILE).parent.mkdir(exist_ok=True)
    Path(INJURY_FILE).write_text(json.dumps(injuries, indent=2))

def remove_injury(player_name: str, team: str) -> None:
    """Remove an injury record."""
    injuries = load_injuries()
    
    if team in injuries:
        injuries[team] = [
            inj for inj in injuries[team]
            if inj["player_name"] != player_name
        ]
        
        if not injuries[team]:
            del injuries[team]
        
        Path(INJURY_FILE).write_text(json.dumps(injuries, indent=2))

def pregame_injury_summary(home_team: str, away_team: str) -> dict:
    """Get injury summary for game preview."""
    from src.models.injury_impact import calculate_injury_impact
    
    home_injuries = load_team_injuries(home_team)
    away_injuries = load_team_injuries(away_team)
    
    home_impact = calculate_injury_impact(home_injuries) if home_injuries else None
    away_impact = calculate_injury_impact(away_injuries) if away_injuries else None
    
    home_net = home_impact.net_impact if home_impact else 0.0
    away_net = away_impact.net_impact if away_impact else 0.0
    
    # Which team has injury advantage?
    advantage = home_net - away_net
    
    return {
        "home_key_out": home_impact.key_injuries if home_impact else [],
        "away_key_out": away_impact.key_injuries if away_impact else [],
        "home_impact": home_net,
        "away_impact": away_net,
        "injury_edge": "Home" if advantage > 0.1 else "Away" if advantage < -0.1 else "Even",
        "edge_magnitude": abs(advantage)
    }
