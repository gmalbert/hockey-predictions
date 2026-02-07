"""Compare goalie matchups for betting edge."""
from dataclasses import dataclass

@dataclass
class MatchupEdge:
    """Goalie matchup comparison."""
    home_goalie: str
    away_goalie: str
    home_sv_pct: float
    away_sv_pct: float
    edge_team: str  # Which team has goalie advantage
    edge_magnitude: float  # Expected goal difference from goalies

def compare_goalie_matchup(
    home_goalie_sv_pct: float,
    away_goalie_sv_pct: float,
    home_goalie_name: str = "Home",
    away_goalie_name: str = "Away"
) -> MatchupEdge:
    """
    Compare goalie quality and determine edge.
    
    Returns which team benefits from goalie matchup.
    """
    # Calculate expected goals saved above average for each
    home_goals_saved = (home_goalie_sv_pct - 0.905) * 30  # vs 30 shots
    away_goals_saved = (away_goalie_sv_pct - 0.905) * 30
    
    # Net edge (positive = home advantage)
    net_edge = home_goals_saved - away_goals_saved
    
    if abs(net_edge) < 0.1:
        edge_team = "Even"
    elif net_edge > 0:
        edge_team = "Home"
    else:
        edge_team = "Away"
    
    return MatchupEdge(
        home_goalie=home_goalie_name,
        away_goalie=away_goalie_name,
        home_sv_pct=home_goalie_sv_pct,
        away_sv_pct=away_goalie_sv_pct,
        edge_team=edge_team,
        edge_magnitude=abs(round(net_edge, 2))
    )

def goalie_recent_form(game_log: list, n_games: int = 5) -> dict:
    """Analyze goalie's recent form."""
    recent = game_log[-n_games:] if len(game_log) >= n_games else game_log
    
    if not recent:
        return {"games": 0, "recent_sv_pct": None}
    
    total_saves = sum(g.get("saves", 0) for g in recent)
    total_shots = sum(g.get("shots_against", 0) for g in recent)
    
    recent_sv_pct = total_saves / total_shots if total_shots > 0 else 0
    
    return {
        "games": len(recent),
        "recent_sv_pct": round(recent_sv_pct, 3),
        "recent_gaa": sum(g.get("goals_against", 0) for g in recent) / len(recent),
        "wins": sum(1 for g in recent if g.get("decision") == "W"),
        "quality_starts": sum(
            1 for g in recent 
            if g.get("saves", 0) / max(g.get("shots_against", 1), 1) > 0.917
        )
    }
