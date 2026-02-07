"""Analyze line movements for betting signals."""
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class MovementType(Enum):
    STEAM = "steam"          # Sharp, fast move
    DRIFT = "drift"          # Gradual move
    REVERSE = "reverse"      # Against public betting
    STABLE = "stable"        # No significant movement

@dataclass
class LineMovementAnalysis:
    """Analysis of line movement."""
    game_id: str
    movement_type: MovementType
    direction: str  # "home", "away", "over", "under"
    magnitude: float
    is_sharp_action: bool
    confidence: str
    recommendation: str

def analyze_moneyline_movement(
    opening_home_ml: int,
    current_home_ml: int,
    hours_until_game: float
) -> LineMovementAnalysis:
    """
    Analyze moneyline movement for sharp action.
    
    Sharp indicators:
    - Movement against public team
    - Fast, significant moves (>15 cents)
    - Late movement (within 2 hours of game)
    """
    movement = current_home_ml - opening_home_ml
    
    # Determine direction
    if movement < -10:  # Home became more favored
        direction = "home"
    elif movement > 10:
        direction = "away"
    else:
        direction = "none"
    
    magnitude = abs(movement)
    
    # Classify movement type
    if magnitude >= 20 and hours_until_game < 2:
        movement_type = MovementType.STEAM
        is_sharp = True
        confidence = "high"
    elif magnitude >= 15:
        movement_type = MovementType.STEAM
        is_sharp = True
        confidence = "medium"
    elif magnitude >= 8:
        movement_type = MovementType.DRIFT
        is_sharp = False
        confidence = "low"
    else:
        movement_type = MovementType.STABLE
        is_sharp = False
        confidence = "low"
    
    # Recommendation
    if is_sharp and direction != "none":
        recommendation = f"Consider {direction} ML - sharp movement detected"
    else:
        recommendation = "No clear signal from line movement"
    
    return LineMovementAnalysis(
        game_id="",
        movement_type=movement_type,
        direction=direction,
        magnitude=magnitude,
        is_sharp_action=is_sharp,
        confidence=confidence,
        recommendation=recommendation
    )

def analyze_total_movement(
    opening_total: float,
    current_total: float,
    opening_over_odds: int,
    current_over_odds: int
) -> LineMovementAnalysis:
    """Analyze total movement."""
    total_move = current_total - opening_total
    juice_move = current_over_odds - opening_over_odds
    
    # Total moved up = sharp over action
    # Total moved down = sharp under action
    if total_move >= 0.5:
        direction = "over"
        is_sharp = True
    elif total_move <= -0.5:
        direction = "under"
        is_sharp = True
    elif abs(juice_move) >= 15:
        # Juice move without total move
        direction = "over" if juice_move > 0 else "under"
        is_sharp = True
    else:
        direction = "none"
        is_sharp = False
    
    return LineMovementAnalysis(
        game_id="",
        movement_type=MovementType.STEAM if is_sharp else MovementType.STABLE,
        direction=direction,
        magnitude=abs(total_move),
        is_sharp_action=is_sharp,
        confidence="medium" if is_sharp else "low",
        recommendation=f"Sharp action on {direction}" if is_sharp else "No clear signal"
    )

def model_vs_market_edge(
    model_home_prob: float,
    current_home_ml: int,
    opening_home_ml: int
) -> dict:
    """
    Compare model prediction to market movement.
    
    Best signals:
    - Model agrees with line movement direction
    - Model probability exceeds market by 5%+
    """
    from src.utils.odds import american_to_implied
    
    current_implied = american_to_implied(current_home_ml)
    opening_implied = american_to_implied(opening_home_ml)
    
    model_edge = model_home_prob - current_implied
    market_moved_toward = current_implied > opening_implied
    model_agrees = (model_home_prob > 0.5) == market_moved_toward
    
    return {
        "model_prob": round(model_home_prob * 100, 1),
        "market_implied": round(current_implied * 100, 1),
        "edge": round(model_edge * 100, 1),
        "market_direction": "home" if market_moved_toward else "away",
        "model_agrees_with_market": model_agrees,
        "signal_strength": "strong" if model_agrees and model_edge > 0.05 else "weak"
    }
