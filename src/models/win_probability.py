"""Win probability calculations using Poisson distribution."""
import math
from typing import NamedTuple


class GameProbabilities(NamedTuple):
    """Probabilities for game outcomes."""
    home_win: float       # Total home win probability (reg + OT)
    away_win: float       # Total away win probability (reg + OT)
    home_regulation: float  # Home win in regulation
    away_regulation: float  # Away win in regulation
    overtime: float       # Probability game goes to OT


def poisson_prob(expected: float, actual: int) -> float:
    """
    Calculate Poisson probability P(X = actual).
    
    Args:
        expected: Expected value (lambda)
        actual: Observed value (k)
    
    Returns:
        Probability of exactly 'actual' occurrences
    """
    if actual < 0:
        return 0.0
    return (math.exp(-expected) * (expected ** actual)) / math.factorial(actual)


def calculate_win_probability(
    home_xg: float,
    away_xg: float,
    home_ot_advantage: float = 0.52,
    max_goals: int = 10
) -> GameProbabilities:
    """
    Calculate win probabilities using Poisson model.
    
    Args:
        home_xg: Expected goals for home team
        away_xg: Expected goals for away team
        home_ot_advantage: Home win probability in OT (default 52%)
        max_goals: Maximum goals to consider per team
    
    Returns:
        GameProbabilities with all outcome probabilities
    
    Example:
        >>> probs = calculate_win_probability(3.2, 2.8)
        >>> probs.home_win
        0.5623
    """
    home_reg_win = 0.0
    away_reg_win = 0.0
    tie_prob = 0.0
    
    for h in range(max_goals + 1):
        home_prob = poisson_prob(home_xg, h)
        for a in range(max_goals + 1):
            away_prob = poisson_prob(away_xg, a)
            combined_prob = home_prob * away_prob
            
            if h > a:
                home_reg_win += combined_prob
            elif a > h:
                away_reg_win += combined_prob
            else:
                tie_prob += combined_prob
    
    # OT/SO: split ties based on home advantage
    ot_home_win = tie_prob * home_ot_advantage
    ot_away_win = tie_prob * (1 - home_ot_advantage)
    
    return GameProbabilities(
        home_win=round(home_reg_win + ot_home_win, 4),
        away_win=round(away_reg_win + ot_away_win, 4),
        home_regulation=round(home_reg_win, 4),
        away_regulation=round(away_reg_win, 4),
        overtime=round(tie_prob, 4)
    )


def implied_probability_to_odds(prob: float) -> int:
    """
    Convert probability to American odds.
    
    Args:
        prob: Win probability (0-1)
    
    Returns:
        American odds (negative for favorite, positive for underdog)
    """
    if prob <= 0 or prob >= 1:
        return 0
    
    if prob >= 0.5:
        return int(-100 * prob / (1 - prob))
    else:
        return int(100 * (1 - prob) / prob)
