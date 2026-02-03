"""Odds conversion and value calculation utilities."""


def american_to_implied(american_odds: int) -> float:
    """
    Convert American odds to implied probability.
    
    Args:
        american_odds: American format odds (e.g., -150, +130)
    
    Returns:
        Implied probability (0-1)
    
    Examples:
        >>> american_to_implied(-150)
        0.6
        >>> american_to_implied(+150)
        0.4
    """
    if american_odds > 0:
        return 100 / (american_odds + 100)
    else:
        return abs(american_odds) / (abs(american_odds) + 100)


def implied_to_american(probability: float) -> int:
    """
    Convert implied probability to American odds.
    
    Args:
        probability: Win probability (0-1)
    
    Returns:
        American odds (negative for favorite, positive for underdog)
    
    Examples:
        >>> implied_to_american(0.6)
        -150
        >>> implied_to_american(0.4)
        150
    """
    if probability <= 0 or probability >= 1:
        return 0
    
    if probability >= 0.5:
        return int(-100 * probability / (1 - probability))
    else:
        return int(100 * (1 - probability) / probability)


def decimal_to_american(decimal_odds: float) -> int:
    """Convert decimal odds to American odds."""
    if decimal_odds >= 2.0:
        return int((decimal_odds - 1) * 100)
    else:
        return int(-100 / (decimal_odds - 1))


def american_to_decimal(american_odds: int) -> float:
    """Convert American odds to decimal odds."""
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1


def calculate_edge(
    model_prob: float,
    book_odds: int
) -> dict:
    """
    Calculate betting edge and Kelly criterion.
    
    Args:
        model_prob: Model's predicted probability (0-1)
        book_odds: Bookmaker's American odds
    
    Returns:
        Dictionary with edge metrics
    
    Example:
        >>> calculate_edge(0.55, +110)
        {'model_prob': 55.0, 'implied_prob': 47.6, 'edge_pct': 7.4, ...}
    """
    implied_prob = american_to_implied(book_odds)
    edge = model_prob - implied_prob
    
    # Kelly criterion for optimal bet sizing
    if edge > 0:
        decimal_odds = american_to_decimal(book_odds)
        kelly = (decimal_odds * model_prob - 1) / (decimal_odds - 1)
        kelly = max(0, min(kelly, 0.25))  # Cap at 25%
    else:
        kelly = 0.0
    
    return {
        "model_prob": round(model_prob * 100, 1),
        "implied_prob": round(implied_prob * 100, 1),
        "edge_pct": round(edge * 100, 1),
        "kelly_fraction": round(kelly, 4),
        "kelly_pct": round(kelly * 100, 2),
        "has_value": edge > 0.02,  # 2% minimum edge
        "bet_rating": _get_bet_rating(edge)
    }


def _get_bet_rating(edge: float) -> str:
    """Get bet rating based on edge."""
    if edge < 0.02:
        return "No bet"
    elif edge < 0.05:
        return "Small edge"
    elif edge < 0.10:
        return "Good value"
    else:
        return "Strong value"


def calculate_ev(
    model_prob: float,
    book_odds: int,
    stake: float = 1.0
) -> float:
    """
    Calculate expected value of a bet.
    
    Args:
        model_prob: Model's probability of winning
        book_odds: American odds
        stake: Bet amount (default 1 unit)
    
    Returns:
        Expected value in units
    """
    decimal_odds = american_to_decimal(book_odds)
    win_amount = stake * (decimal_odds - 1)
    
    ev = (model_prob * win_amount) - ((1 - model_prob) * stake)
    return round(ev, 4)


def breakeven_probability(american_odds: int) -> float:
    """
    Calculate breakeven win rate needed for odds.
    
    Args:
        american_odds: Book's American odds
    
    Returns:
        Required win rate to break even
    """
    return american_to_implied(american_odds)


def juice_percentage(
    home_odds: int,
    away_odds: int
) -> float:
    """
    Calculate the book's juice/vig percentage.
    
    Args:
        home_odds: American odds for home team
        away_odds: American odds for away team
    
    Returns:
        Juice percentage (e.g., 4.5 means 4.5% vig)
    """
    home_implied = american_to_implied(home_odds)
    away_implied = american_to_implied(away_odds)
    
    total_implied = home_implied + away_implied
    juice = (total_implied - 1) * 100
    
    return round(juice, 2)
