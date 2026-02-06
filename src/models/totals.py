"""Over/Under total goals predictions."""
import math
from dataclasses import dataclass

@dataclass
class TotalsPrediction:
    """Prediction for game totals."""
    expected_total: float
    over_prob: float
    under_prob: float
    push_prob: float

def predict_total(
    home_xg: float,
    away_xg: float,
    line: float = 6.0
) -> TotalsPrediction:
    """
    Calculate over/under probabilities.
    
    Args:
        home_xg: Home team expected goals
        away_xg: Away team expected goals
        line: Total goals line (e.g., 6.0, 6.5)
    
    Returns:
        TotalsPrediction with probabilities
    """
    total_xg = home_xg + away_xg
    
    # Calculate cumulative Poisson probabilities
    under_prob = 0.0
    push_prob = 0.0
    
    # Use combined expected total
    for goals in range(int(line) + 1):
        prob = (math.exp(-total_xg) * (total_xg ** goals)) / math.factorial(goals)
        
        if goals < line:
            under_prob += prob
        elif goals == line:  # Push on whole numbers
            push_prob = prob
    
    over_prob = 1 - under_prob - push_prob
    
    return TotalsPrediction(
        expected_total=round(total_xg, 2),
        over_prob=round(over_prob, 4),
        under_prob=round(under_prob, 4),
        push_prob=round(push_prob, 4)
    )
