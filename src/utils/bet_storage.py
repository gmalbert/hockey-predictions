"""Bet recommendation tracking and performance evaluation."""
import json
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict, Any


RECOMMENDATIONS_FILE = Path("data_files/recommendations.json")
RESULTS_FILE = Path("data_files/results/game_results.json")


def load_recommendations() -> List[Dict[str, Any]]:
    """
    Load all bet recommendations.
    
    Returns:
        List of recommendation dictionaries
    """
    if not RECOMMENDATIONS_FILE.exists():
        return []
    
    try:
        with open(RECOMMENDATIONS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("recommendations", [])
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_recommendations(recommendations: List[Dict[str, Any]]) -> None:
    """
    Save recommendations to storage.
    
    Args:
        recommendations: List of recommendation dictionaries
    """
    RECOMMENDATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RECOMMENDATIONS_FILE, 'w') as f:
        json.dump({"recommendations": recommendations}, f, indent=2)


def add_recommendation(
    game_id: str,
    game_date: str,
    home_team: str,
    away_team: str,
    bet_type: str,
    recommendation: str,
    odds: str,
    edge_percent: float,
    model_prob: float
) -> Dict[str, Any]:
    """
    Add a new betting recommendation.
    
    Args:
        game_id: Unique game identifier
        game_date: Date of the game (YYYY-MM-DD)
        home_team: Home team abbreviation
        away_team: Away team abbreviation
        bet_type: Type of bet (e.g., "Moneyline", "Puck Line", "Over", "Under")
        recommendation: Specific recommendation (e.g., "TOR ML", "Over 6.0")
        odds: American odds (e.g., "-150", "+120")
        edge_percent: Edge percentage calculated
        model_prob: Model's probability for this outcome
    
    Returns:
        The created recommendation dictionary
    """
    recommendations = load_recommendations()
    
    rec = {
        "id": len(recommendations) + 1,
        "game_id": game_id,
        "date": game_date,
        "home_team": home_team,
        "away_team": away_team,
        "matchup": f"{away_team} @ {home_team}",
        "bet_type": bet_type,
        "recommendation": recommendation,
        "odds": odds,
        "edge_percent": edge_percent,
        "model_prob": model_prob,
        "result": None,  # Will be filled when game completes
        "won": None,
        "created_at": datetime.now().isoformat()
    }
    
    recommendations.append(rec)
    save_recommendations(recommendations)
    
    return rec


def load_game_results() -> Dict[str, Dict[str, Any]]:
    """
    Load game results from storage.
    
    Returns:
        Dictionary mapping game_id to result data
    """
    if not RESULTS_FILE.exists():
        return {}
    
    try:
        with open(RESULTS_FILE, 'r') as f:
            data = json.load(f)
            # Convert list to dict keyed by game_id
            return {r["game_id"]: r for r in data.get("results", [])}
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def evaluate_recommendations() -> None:
    """
    Evaluate all recommendations against actual game results.
    Updates recommendations with win/loss status based on outcomes.
    """
    recommendations = load_recommendations()
    results = load_game_results()
    
    updated = False
    
    for rec in recommendations:
        # Skip already evaluated
        if rec.get("result") is not None:
            continue
        
        game_id = rec["game_id"]
        if game_id not in results:
            continue
        
        result = results[game_id]
        rec["result"] = result
        
        # Determine if recommendation won
        bet_type = rec["bet_type"]
        recommendation = rec["recommendation"]
        
        home_goals = result.get("home_goals", 0)
        away_goals = result.get("away_goals", 0)
        total_goals = home_goals + away_goals
        home_won = result.get("home_won", home_goals > away_goals)
        
        # Evaluate based on bet type
        if bet_type == "Moneyline":
            # Check if recommended team won
            if rec["home_team"] in recommendation and home_won:
                rec["won"] = True
            elif rec["away_team"] in recommendation and not home_won:
                rec["won"] = True
            else:
                rec["won"] = False
        
        elif bet_type == "Puck Line":
            # Parse puck line (e.g., "TOR -1.5" or "MTL +1.5")
            if "-1.5" in recommendation:
                # Team needs to win by 2+
                team = recommendation.split()[0]
                if team == rec["home_team"]:
                    rec["won"] = (home_goals - away_goals) >= 2
                else:
                    rec["won"] = (away_goals - home_goals) >= 2
            elif "+1.5" in recommendation:
                # Team needs to lose by 1 or win
                team = recommendation.split()[0]
                if team == rec["home_team"]:
                    rec["won"] = (home_goals - away_goals) >= -1
                else:
                    rec["won"] = (away_goals - home_goals) >= -1
        
        elif bet_type == "Over":
            # Parse total (e.g., "Over 6.0")
            try:
                total_line = float(recommendation.split()[-1])
                rec["won"] = total_goals > total_line
            except (ValueError, IndexError):
                rec["won"] = None
        
        elif bet_type == "Under":
            # Parse total (e.g., "Under 6.0")
            try:
                total_line = float(recommendation.split()[-1])
                rec["won"] = total_goals < total_line
            except (ValueError, IndexError):
                rec["won"] = None
        
        updated = True
    
    if updated:
        save_recommendations(recommendations)


def calculate_profit(odds: str, stake: float = 1.0) -> float:
    """
    Calculate profit from American odds.
    
    Args:
        odds: American odds string (e.g., "-150", "+120")
        stake: Stake amount (default 1 unit)
    
    Returns:
        Profit in units
    """
    try:
        odds_int = int(odds)
        
        if odds_int > 0:
            # Positive odds: (odds / 100) * stake
            return (odds_int / 100) * stake
        else:
            # Negative odds: (100 / abs(odds)) * stake
            return (100 / abs(odds_int)) * stake
    except (ValueError, ZeroDivisionError):
        return 0.0


def get_performance_metrics(recommendations: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Calculate performance metrics from recommendations.
    
    Args:
        recommendations: List of recommendations to analyze (loads all if None)
    
    Returns:
        Dictionary with performance metrics
    """
    if recommendations is None:
        recommendations = load_recommendations()
    
    # Filter for evaluated recommendations only
    evaluated_recs = [r for r in recommendations if r.get("won") is not None]
    pending_recs = [r for r in recommendations if r.get("won") is None]
    
    if not evaluated_recs:
        return {
            "total_recommendations": len(recommendations),
            "evaluated": 0,
            "pending": len(pending_recs),
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "total_profit": 0.0,
            "roi": 0.0,
            "avg_edge": 0.0,
            "avg_odds": 0.0
        }
    
    wins = len([r for r in evaluated_recs if r["won"]])
    losses = len(evaluated_recs) - wins
    
    # Calculate profit (1 unit stake per bet)
    total_profit = 0.0
    for rec in evaluated_recs:
        if rec["won"]:
            total_profit += calculate_profit(rec["odds"], 1.0)
        else:
            total_profit -= 1.0
    
    total_staked = len(evaluated_recs) * 1.0  # 1 unit per bet
    
    win_rate = (wins / len(evaluated_recs)) * 100 if evaluated_recs else 0.0
    roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0.0
    
    avg_edge = sum(r.get("edge_percent", 0) for r in evaluated_recs) / len(evaluated_recs)
    
    return {
        "total_recommendations": len(recommendations),
        "evaluated": len(evaluated_recs),
        "pending": len(pending_recs),
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_profit": total_profit,
        "roi": roi,
        "avg_edge": avg_edge,
        "total_staked": total_staked
    }


def get_recommendations_by_type(bet_type_filter: str, recommendations: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Filter recommendations by type.
    
    Args:
        bet_type_filter: Type to filter ("Moneyline", "Puck Line", "Over", "Under")
        recommendations: List to filter (loads all if None)
    
    Returns:
        Filtered list of recommendations
    """
    if recommendations is None:
        recommendations = load_recommendations()
    
    return [r for r in recommendations if r.get("bet_type") == bet_type_filter]


def get_recommendations_by_date_range(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Get recommendations within a date range.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        Filtered list of recommendations
    """
    recommendations = load_recommendations()
    return [
        r for r in recommendations 
        if start_date <= r["date"] <= end_date
    ]
