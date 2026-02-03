"""Puck line prediction model."""
import math
from dataclasses import dataclass
from typing import List, Optional

from .win_probability import poisson_prob


@dataclass
class PuckLinePrediction:
    """Puck line prediction results."""
    home_minus_1_5: float  # Prob home wins by 2+
    away_plus_1_5: float   # Prob away loses by 1 or less, or wins
    expected_margin: float  # Expected home margin
    confidence: str        # "high", "medium", "low"


def predict_puck_line(
    home_xg: float,
    away_xg: float,
    home_margin_history: Optional[List[int]] = None,
    away_margin_history: Optional[List[int]] = None,
    max_goals: int = 10
) -> PuckLinePrediction:
    """
    Predict puck line (-1.5/+1.5) outcomes.
    
    Uses Poisson distribution for base prediction, optionally
    blended with historical margin data.
    
    Args:
        home_xg: Home team expected goals
        away_xg: Away team expected goals
        home_margin_history: List of home team's win margins (optional)
        away_margin_history: List of away team's margins vs opponents (optional)
        max_goals: Maximum goals to simulate
    
    Returns:
        PuckLinePrediction with probabilities
    
    Example:
        >>> pred = predict_puck_line(3.5, 2.8)
        >>> pred.home_minus_1_5
        0.3842
    """
    # Poisson-based calculation
    home_cover = 0.0  # Home -1.5 (wins by 2+)
    away_cover = 0.0  # Away +1.5 (home wins by 0-1, tie, or loses)
    
    for h in range(max_goals + 1):
        home_prob = poisson_prob(home_xg, h)
        for a in range(max_goals + 1):
            away_prob = poisson_prob(away_xg, a)
            combined_prob = home_prob * away_prob
            margin = h - a
            
            if margin >= 2:
                home_cover += combined_prob
            else:  # margin <= 1 (includes ties, which go to OT)
                away_cover += combined_prob
    
    # Blend with historical data if available
    if home_margin_history and len(home_margin_history) >= 10:
        hist_cover_rate = sum(1 for m in home_margin_history if m >= 2) / len(home_margin_history)
        # 60% Poisson, 40% historical
        home_cover = 0.6 * home_cover + 0.4 * hist_cover_rate
        away_cover = 1 - home_cover
        confidence = "high"
    elif home_margin_history and len(home_margin_history) >= 5:
        hist_cover_rate = sum(1 for m in home_margin_history if m >= 2) / len(home_margin_history)
        home_cover = 0.75 * home_cover + 0.25 * hist_cover_rate
        away_cover = 1 - home_cover
        confidence = "medium"
    else:
        confidence = "low"
    
    expected_margin = home_xg - away_xg
    
    return PuckLinePrediction(
        home_minus_1_5=round(home_cover, 4),
        away_plus_1_5=round(away_cover, 4),
        expected_margin=round(expected_margin, 2),
        confidence=confidence
    )


def analyze_margin_distribution(margins: List[int]) -> dict:
    """
    Analyze a team's historical win margin distribution.
    
    Args:
        margins: List of game margins (positive = wins, negative = losses)
    
    Returns:
        Dictionary with margin statistics
    """
    if not margins:
        return {"games": 0}
    
    wins = [m for m in margins if m > 0]
    losses = [m for m in margins if m < 0]
    
    return {
        "games": len(margins),
        "wins": len(wins),
        "losses": len(losses),
        "ties_to_ot": sum(1 for m in margins if m == 0),
        "win_by_2_plus": sum(1 for m in wins if m >= 2),
        "win_by_1": sum(1 for m in wins if m == 1),
        "lose_by_1": sum(1 for m in losses if m == -1),
        "lose_by_2_plus": sum(1 for m in losses if m <= -2),
        "cover_minus_1_5_rate": sum(1 for m in margins if m >= 2) / len(margins) if margins else 0,
        "avg_win_margin": sum(wins) / len(wins) if wins else 0,
        "avg_loss_margin": sum(losses) / len(losses) if losses else 0,
    }


def puck_line_value(
    prediction: PuckLinePrediction,
    home_minus_1_5_odds: int,
    away_plus_1_5_odds: int
) -> dict:
    """
    Calculate betting value on puck line.
    
    Args:
        prediction: PuckLinePrediction object
        home_minus_1_5_odds: American odds for home -1.5
        away_plus_1_5_odds: American odds for away +1.5
    
    Returns:
        Dictionary with value analysis
    """
    def american_to_implied(odds: int) -> float:
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)
    
    home_implied = american_to_implied(home_minus_1_5_odds)
    away_implied = american_to_implied(away_plus_1_5_odds)
    
    home_edge = prediction.home_minus_1_5 - home_implied
    away_edge = prediction.away_plus_1_5 - away_implied
    
    return {
        "home_minus_1_5": {
            "model_prob": round(prediction.home_minus_1_5 * 100, 1),
            "implied_prob": round(home_implied * 100, 1),
            "edge": round(home_edge * 100, 1),
            "has_value": home_edge > 0.02
        },
        "away_plus_1_5": {
            "model_prob": round(prediction.away_plus_1_5 * 100, 1),
            "implied_prob": round(away_implied * 100, 1),
            "edge": round(away_edge * 100, 1),
            "has_value": away_edge > 0.02
        }
    }
