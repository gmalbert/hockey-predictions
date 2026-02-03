"""Model evaluation metrics."""
import math
import statistics
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from collections import defaultdict


@dataclass
class PredictionResult:
    """Single prediction with outcome."""
    game_id: str
    date: str
    home_team: str
    away_team: str
    predicted_home_goals: float
    predicted_away_goals: float
    actual_home_goals: int
    actual_away_goals: int
    predicted_home_win_prob: float
    home_won: bool
    
    @property
    def predicted_total(self) -> float:
        return self.predicted_home_goals + self.predicted_away_goals
    
    @property
    def actual_total(self) -> int:
        return self.actual_home_goals + self.actual_away_goals
    
    @property
    def home_goal_error(self) -> float:
        return abs(self.predicted_home_goals - self.actual_home_goals)
    
    @property
    def away_goal_error(self) -> float:
        return abs(self.predicted_away_goals - self.actual_away_goals)
    
    @property
    def total_error(self) -> float:
        return abs(self.predicted_total - self.actual_total)


def calculate_mae(
    predictions: List[PredictionResult],
    target: str = "total"
) -> float:
    """
    Calculate Mean Absolute Error.
    
    Args:
        predictions: List of prediction results
        target: "total", "home_goals", or "away_goals"
    
    Returns:
        MAE value (average absolute difference)
    
    Interpretation:
        MAE < 1.0: Excellent
        MAE 1.0-1.5: Good
        MAE 1.5-2.0: Fair
        MAE > 2.0: Poor
    """
    if not predictions:
        return 0.0
    
    errors = []
    for pred in predictions:
        if target == "total":
            errors.append(pred.total_error)
        elif target == "home_goals":
            errors.append(pred.home_goal_error)
        elif target == "away_goals":
            errors.append(pred.away_goal_error)
        else:
            raise ValueError(f"Unknown target: {target}")
    
    return round(statistics.mean(errors), 3)


def calculate_rmse(
    predictions: List[PredictionResult],
    target: str = "total"
) -> float:
    """
    Calculate Root Mean Square Error.
    
    RMSE penalizes large errors more than MAE.
    """
    if not predictions:
        return 0.0
    
    squared_errors = []
    for pred in predictions:
        if target == "total":
            error = pred.predicted_total - pred.actual_total
        elif target == "home_goals":
            error = pred.predicted_home_goals - pred.actual_home_goals
        else:
            error = pred.predicted_away_goals - pred.actual_away_goals
        
        squared_errors.append(error ** 2)
    
    return round(math.sqrt(statistics.mean(squared_errors)), 3)


def calculate_accuracy(predictions: List[PredictionResult]) -> float:
    """
    Calculate win prediction accuracy.
    
    Returns:
        Accuracy as decimal (0-1)
    """
    if not predictions:
        return 0.0
    
    correct = sum(
        1 for pred in predictions
        if (pred.predicted_home_win_prob > 0.5) == pred.home_won
    )
    
    return round(correct / len(predictions), 4)


def calibration_buckets(
    predictions: List[PredictionResult],
    n_buckets: int = 10
) -> List[Tuple[float, float, int]]:
    """
    Group predictions by probability and compare to actual win rate.
    
    Returns:
        List of (bucket_center, actual_win_rate, count)
    
    Well-calibrated model: predicted prob ≈ actual win rate
    """
    buckets = defaultdict(list)
    bucket_size = 1.0 / n_buckets
    
    for pred in predictions:
        bucket_idx = min(int(pred.predicted_home_win_prob / bucket_size), n_buckets - 1)
        buckets[bucket_idx].append(1 if pred.home_won else 0)
    
    results = []
    for i in range(n_buckets):
        if buckets[i]:
            center = (i + 0.5) * bucket_size
            actual_rate = sum(buckets[i]) / len(buckets[i])
            results.append((round(center, 2), round(actual_rate, 3), len(buckets[i])))
    
    return results


def calibration_error(predictions: List[PredictionResult]) -> float:
    """
    Calculate Expected Calibration Error (ECE).
    
    Lower is better. Well-calibrated models have ECE < 0.05
    """
    if not predictions:
        return 0.0
    
    buckets = calibration_buckets(predictions)
    total_samples = len(predictions)
    ece = 0.0
    
    for center, actual_rate, count in buckets:
        weight = count / total_samples
        ece += weight * abs(center - actual_rate)
    
    return round(ece, 4)


@dataclass
class ModelPerformance:
    """Comprehensive model performance metrics."""
    n_predictions: int
    accuracy: float
    mae_total: float
    mae_home: float
    mae_away: float
    rmse_total: float
    calibration_error: float
    
    @classmethod
    def from_predictions(cls, predictions: List[PredictionResult]) -> "ModelPerformance":
        """Calculate all metrics from predictions."""
        return cls(
            n_predictions=len(predictions),
            accuracy=calculate_accuracy(predictions),
            mae_total=calculate_mae(predictions, "total"),
            mae_home=calculate_mae(predictions, "home_goals"),
            mae_away=calculate_mae(predictions, "away_goals"),
            rmse_total=calculate_rmse(predictions, "total"),
            calibration_error=calibration_error(predictions)
        )
    
    def summary(self) -> str:
        """Return formatted summary string."""
        return f"""
Model Performance ({self.n_predictions} predictions)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Accuracy:        {self.accuracy:.1%}
MAE (Total):     {self.mae_total:.2f} goals
MAE (Home):      {self.mae_home:.2f} goals
MAE (Away):      {self.mae_away:.2f} goals
RMSE (Total):    {self.rmse_total:.2f} goals
Calibration:     {self.calibration_error:.3f}
"""
