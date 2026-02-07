"""Store and retrieve prediction results for evaluation."""
import json
from pathlib import Path
from datetime import date, timedelta, datetime
from typing import List, Optional, Dict

PREDICTIONS_DIR = Path("data_files/predictions")
RESULTS_DIR = Path("data_files/results")

def save_prediction(
    game_id: str,
    game_date: date,
    home_team: str,
    away_team: str,
    predicted_home_goals: float,
    predicted_away_goals: float,
    predicted_total: float,
    predicted_home_win_prob: float
) -> None:
    """Save a prediction for later evaluation."""
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    date_dir = PREDICTIONS_DIR / game_date.isoformat()
    date_dir.mkdir(exist_ok=True)
    
    file_path = date_dir / f"{game_id}.json"
    
    data = {
        "game_id": game_id,
        "game_date": game_date.isoformat(),
        "home_team": home_team,
        "away_team": away_team,
        "predicted_home_goals": predicted_home_goals,
        "predicted_away_goals": predicted_away_goals,
        "predicted_total": predicted_total,
        "predicted_home_win_prob": predicted_home_win_prob,
        "prediction_timestamp": datetime.now().isoformat()
    }
    
    file_path.write_text(json.dumps(data, indent=2))

def save_bet_record(
    game_id: str,
    game_date: date,
    bet_type: str,
    odds: int,
    stake: float
) -> None:
    """Save a bet for later evaluation."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    bets_file = RESULTS_DIR / "bet_history.json"
    
    if bets_file.exists():
        data = json.loads(bets_file.read_text())
    else:
        data = {"bets": []}
    
    bet_record = {
        "game_id": game_id,
        "game_date": game_date.isoformat(),
        "bet_type": bet_type,
        "odds": odds,
        "stake": stake,
        "bet_timestamp": datetime.now().isoformat(),
        "won": None  # To be filled when result is known
    }
    
    data["bets"].append(bet_record)
    bets_file.write_text(json.dumps(data, indent=2))

def save_game_result(
    game_id: str,
    home_goals: int,
    away_goals: int,
    home_won: bool
) -> None:
    """Save actual game result."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    results_file = RESULTS_DIR / "game_results.json"
    
    if results_file.exists():
        data = json.loads(results_file.read_text())
    else:
        data = {"results": []}
    
    result = {
        "game_id": game_id,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "total_goals": home_goals + away_goals,
        "home_won": home_won,
        "result_timestamp": datetime.now().isoformat()
    }
    
    data["results"].append(result)
    results_file.write_text(json.dumps(data, indent=2))

def load_predictions_for_date(target_date: date) -> List[dict]:
    """Load all predictions made for a specific date."""
    date_dir = PREDICTIONS_DIR / target_date.isoformat()
    
    if not date_dir.exists():
        return []
    
    predictions = []
    for pred_file in date_dir.glob("*.json"):
        data = json.loads(pred_file.read_text())
        predictions.append(data)
    
    return predictions

def load_game_results() -> Dict[str, dict]:
    """Load all game results."""
    results_file = RESULTS_DIR / "game_results.json"
    
    if not results_file.exists():
        return {}
    
    data = json.loads(results_file.read_text())
    
    # Convert to dict keyed by game_id for easy lookup
    return {r["game_id"]: r for r in data.get("results", [])}

def match_predictions_to_results(
    predictions: List[dict],
    results: Dict[str, dict]
) -> List[dict]:
    """Match predictions with actual results."""
    from src.models.evaluation import PredictionResult
    
    matched = []
    
    for pred in predictions:
        game_id = pred["game_id"]
        if game_id in results:
            result = results[game_id]
            
            pr = PredictionResult(
                game_id=game_id,
                predicted_home_goals=pred["predicted_home_goals"],
                predicted_away_goals=pred["predicted_away_goals"],
                actual_home_goals=result["home_goals"],
                actual_away_goals=result["away_goals"],
                predicted_total=pred["predicted_total"],
                actual_total=result["total_goals"],
                predicted_home_win_prob=pred["predicted_home_win_prob"],
                home_won=result["home_won"]
            )
            matched.append(pr)
    
    return matched

def daily_evaluation(target_date: Optional[date] = None) -> dict:
    """Evaluate predictions for a specific date."""
    from src.models.evaluation import calculate_accuracy, calculate_mae, calibration_error
    
    if target_date is None:
        target_date = date.today() - timedelta(days=1)
    
    predictions = load_predictions_for_date(target_date)
    results = load_game_results()
    
    matched = match_predictions_to_results(predictions, results)
    
    if not matched:
        return {
            "date": target_date.isoformat(),
            "games_evaluated": 0,
            "accuracy": 0,
            "mae_total": 0,
            "calibration": 0,
            "message": "No complete prediction-result pairs found"
        }
    
    return {
        "date": target_date.isoformat(),
        "games_evaluated": len(matched),
        "accuracy": calculate_accuracy(matched),
        "mae_total": calculate_mae(matched, "total"),
        "mae_home": calculate_mae(matched, "home_goals"),
        "mae_away": calculate_mae(matched, "away_goals"),
        "calibration": calibration_error(matched)
    }
