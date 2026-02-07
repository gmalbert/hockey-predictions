"""Adjust predictions based on goalie matchup."""
from dataclasses import dataclass

LEAGUE_AVG_SAVE_PCT = 0.905

@dataclass
class GoalieAdjustment:
    """Adjustment to opponent's expected goals."""
    goalie_name: str
    save_pct: float
    adjustment: float  # Negative = fewer goals expected
    confidence: str

def calculate_goalie_adjustment(
    goalie_save_pct: float,
    sample_size: int
) -> GoalieAdjustment:
    """
    Calculate goal adjustment based on goalie vs league average.
    
    Each 1% above/below average SV% ≈ 0.3 goals difference
    """
    diff_from_avg = goalie_save_pct - LEAGUE_AVG_SAVE_PCT
    
    # Base adjustment: 30 shots/game * SV% difference
    base_adjustment = -diff_from_avg * 30
    
    # Reduce confidence for small sample sizes
    if sample_size < 10:
        confidence = "low"
        adjustment = base_adjustment * 0.5  # Regress heavily
    elif sample_size < 20:
        confidence = "medium"
        adjustment = base_adjustment * 0.75
    else:
        confidence = "high"
        adjustment = base_adjustment
    
    return GoalieAdjustment(
        goalie_name="",  # Fill in caller
        save_pct=goalie_save_pct,
        adjustment=round(adjustment, 2),
        confidence=confidence
    )

def adjusted_xg_for_matchup(
    base_team_xg: float,
    opposing_goalie_sv_pct: float,
    opposing_goalie_games: int
) -> float:
    """
    Adjust a team's expected goals based on opposing goalie.
    
    Example:
        Team xG: 3.2
        Opposing goalie: 0.925 SV% (elite)
        Adjustment: -0.6 goals
        Adjusted xG: 2.6
    """
    adj = calculate_goalie_adjustment(opposing_goalie_sv_pct, opposing_goalie_games)
    return round(base_team_xg + adj.adjustment, 2)
