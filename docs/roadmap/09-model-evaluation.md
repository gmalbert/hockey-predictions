# Model Evaluation Roadmap

## Overview
Track model performance using appropriate metrics to validate predictions and identify areas for improvement.

---

## Key Metrics

### Classification Metrics (Moneyline/Puck Line)
| Metric | Description | Target |
|--------|-------------|--------|
| **Accuracy** | % of correct predictions | > 52% for profit |
| **Log Loss** | Probability calibration | Lower is better |
| **AUC-ROC** | Discrimination ability | > 0.55 for edge |
| **Brier Score** | Probabilistic accuracy | Lower is better |

### Regression Metrics (Totals/Goals)
| Metric | Description | Target |
|--------|-------------|--------|
| **MAE** | Mean Absolute Error | < 1.2 goals |
| **RMSE** | Root Mean Square Error | < 1.5 goals |
| **R²** | Variance explained | > 0.15 |

### Betting Performance
| Metric | Description | Target |
|--------|-------------|--------|
| **ROI** | Return on Investment | > 3% |
| **Win Rate** | Winning bet percentage | > 52.4% at -110 |
| **CLV** | Closing Line Value | Positive |
| **Drawdown** | Max losing streak | Monitor |

---

## Phase 1: Core Evaluation Functions

### Task 1.1: MAE Calculator
**File**: `src/models/evaluation.py`

```python
"""Model evaluation metrics."""
import math
from typing import List, Tuple
from dataclasses import dataclass
import statistics

@dataclass
class PredictionResult:
    """Single prediction with outcome."""
    game_id: str
    predicted_home_goals: float
    predicted_away_goals: float
    actual_home_goals: int
    actual_away_goals: int
    predicted_total: float
    actual_total: int
    predicted_home_win_prob: float
    home_won: bool

def calculate_mae(predictions: List[PredictionResult], target: str = "total") -> float:
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
            predicted = pred.predicted_total
            actual = pred.actual_total
        elif target == "home_goals":
            predicted = pred.predicted_home_goals
            actual = pred.actual_home_goals
        elif target == "away_goals":
            predicted = pred.predicted_away_goals
            actual = pred.actual_away_goals
        else:
            raise ValueError(f"Unknown target: {target}")
        
        errors.append(abs(predicted - actual))
    
    return round(statistics.mean(errors), 3)

def calculate_rmse(predictions: List[PredictionResult], target: str = "total") -> float:
    """
    Calculate Root Mean Square Error.
    
    RMSE penalizes large errors more than MAE.
    """
    if not predictions:
        return 0.0
    
    squared_errors = []
    for pred in predictions:
        if target == "total":
            predicted = pred.predicted_total
            actual = pred.actual_total
        elif target == "home_goals":
            predicted = pred.predicted_home_goals
            actual = pred.actual_home_goals
        else:
            predicted = pred.predicted_away_goals
            actual = pred.actual_away_goals
        
        squared_errors.append((predicted - actual) ** 2)
    
    return round(math.sqrt(statistics.mean(squared_errors)), 3)

def calculate_accuracy(predictions: List[PredictionResult]) -> float:
    """Calculate win prediction accuracy."""
    if not predictions:
        return 0.0
    
    correct = 0
    for pred in predictions:
        predicted_home_win = pred.predicted_home_win_prob > 0.5
        if predicted_home_win == pred.home_won:
            correct += 1
    
    return round(correct / len(predictions), 4)
```

### Task 1.2: Calibration Analysis
```python
"""Check if predicted probabilities match actual outcomes."""
from typing import List, Tuple
from collections import defaultdict

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
    # Group by probability buckets
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
    buckets = calibration_buckets(predictions)
    
    total_samples = len(predictions)
    ece = 0.0
    
    for center, actual_rate, count in buckets:
        weight = count / total_samples
        ece += weight * abs(center - actual_rate)
    
    return round(ece, 4)
```

### Task 1.3: Betting Performance Metrics
```python
"""Track betting ROI and performance."""
from dataclasses import dataclass
from typing import List

@dataclass
class BetRecord:
    """Single bet record."""
    game_id: str
    bet_type: str  # "home_ml", "away_ml", "over", "under", "home_pl", "away_pl"
    odds: int
    stake: float
    won: bool
    
    @property
    def profit(self) -> float:
        """Calculate profit/loss."""
        if not self.won:
            return -self.stake
        
        if self.odds > 0:
            return self.stake * (self.odds / 100)
        else:
            return self.stake * (100 / abs(self.odds))

def calculate_roi(bets: List[BetRecord]) -> dict:
    """
    Calculate betting ROI and related metrics.
    
    Returns comprehensive betting performance stats.
    """
    if not bets:
        return {"roi": 0, "win_rate": 0, "total_bets": 0}
    
    total_staked = sum(b.stake for b in bets)
    total_profit = sum(b.profit for b in bets)
    wins = sum(1 for b in bets if b.won)
    
    # Calculate max drawdown
    cumulative = 0
    peak = 0
    max_drawdown = 0
    
    for bet in bets:
        cumulative += bet.profit
        peak = max(peak, cumulative)
        drawdown = peak - cumulative
        max_drawdown = max(max_drawdown, drawdown)
    
    return {
        "total_bets": len(bets),
        "wins": wins,
        "losses": len(bets) - wins,
        "win_rate": round(wins / len(bets), 4),
        "total_staked": round(total_staked, 2),
        "total_profit": round(total_profit, 2),
        "roi": round((total_profit / total_staked) * 100, 2) if total_staked > 0 else 0,
        "max_drawdown": round(max_drawdown, 2),
        "avg_odds": round(sum(b.odds for b in bets) / len(bets), 0)
    }
```

---

## Phase 2: Model Comparison

### Task 2.1: A/B Testing Framework
```python
"""Compare multiple models."""
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ModelPerformance:
    """Performance summary for a model."""
    model_name: str
    accuracy: float
    mae_total: float
    mae_home: float
    mae_away: float
    rmse_total: float
    calibration_error: float
    roi: float
    n_predictions: int

def compare_models(
    model_predictions: Dict[str, List[PredictionResult]]
) -> List[ModelPerformance]:
    """
    Compare multiple models on the same games.
    
    Args:
        model_predictions: Dict mapping model name to predictions
    
    Returns:
        List of ModelPerformance sorted by ROI
    """
    results = []
    
    for model_name, predictions in model_predictions.items():
        perf = ModelPerformance(
            model_name=model_name,
            accuracy=calculate_accuracy(predictions),
            mae_total=calculate_mae(predictions, "total"),
            mae_home=calculate_mae(predictions, "home_goals"),
            mae_away=calculate_mae(predictions, "away_goals"),
            rmse_total=calculate_rmse(predictions, "total"),
            calibration_error=calibration_error(predictions),
            roi=0.0,  # Calculate from bets if available
            n_predictions=len(predictions)
        )
        results.append(perf)
    
    # Sort by accuracy
    return sorted(results, key=lambda x: x.accuracy, reverse=True)
```

---

## Phase 3: Streamlit Dashboard

### Task 3.1: Evaluation Dashboard
**File**: `src/pages/10_📊_Model_Performance.py`

```python
"""Model performance dashboard."""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Model Performance", page_icon="📊", layout="wide")
st.title("📊 Model Performance")

# Summary metrics
st.subheader("Current Model Performance")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Accuracy", "54.2%", "+1.3%")
with col2:
    st.metric("MAE (Total Goals)", "1.18", "-0.05")
with col3:
    st.metric("ROI", "+5.8%", "+0.9%")
with col4:
    st.metric("Calibration Error", "0.032", "-0.008")

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["Prediction Accuracy", "Goal Predictions", "Betting Performance"])

with tab1:
    st.markdown("### Win Prediction Accuracy Over Time")
    # Placeholder
    accuracy_data = {
        "Week": list(range(1, 13)),
        "Accuracy": [0.52, 0.54, 0.51, 0.55, 0.53, 0.54, 0.56, 0.53, 0.55, 0.54, 0.55, 0.54]
    }
    st.line_chart(pd.DataFrame(accuracy_data).set_index("Week"))

with tab2:
    st.markdown("### Goal Prediction Error Distribution")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**MAE by Prediction Type**")
        mae_data = pd.DataFrame({
            "Type": ["Total Goals", "Home Goals", "Away Goals"],
            "MAE": [1.18, 0.92, 0.95]
        })
        st.dataframe(mae_data, hide_index=True)
    
    with col2:
        st.markdown("**RMSE Comparison**")
        rmse_data = pd.DataFrame({
            "Type": ["Total Goals", "Home Goals", "Away Goals"],
            "RMSE": [1.45, 1.15, 1.20]
        })
        st.dataframe(rmse_data, hide_index=True)

with tab3:
    st.markdown("### Betting Performance")
    
    betting_df = pd.DataFrame({
        "Bet Type": ["Moneyline", "Puck Line", "Totals"],
        "Bets": [85, 42, 68],
        "Win Rate": ["54.1%", "47.6%", "55.9%"],
        "ROI": ["+4.2%", "-2.1%", "+8.5%"],
        "Units": ["+3.6", "-0.9", "+5.8"]
    })
    st.dataframe(betting_df, use_container_width=True, hide_index=True)

# Calibration chart
st.subheader("Probability Calibration")
st.markdown("""
The dotted line represents perfect calibration. 
Points above the line = model underconfident, points below = overconfident.
""")

calibration_df = pd.DataFrame({
    "Predicted Probability": [0.35, 0.45, 0.55, 0.65, 0.75],
    "Actual Win Rate": [0.33, 0.47, 0.54, 0.62, 0.78]
})
st.line_chart(calibration_df.set_index("Predicted Probability"))
```

---

## Evaluation Best Practices

### Minimum Sample Sizes
| Metric | Min Samples | Reason |
|--------|-------------|--------|
| Accuracy | 100 games | Statistical significance |
| MAE | 50 games | Variance stabilization |
| ROI | 200 bets | Luck normalization |
| Calibration | 500 predictions | Bucket population |

### When to Retrain
1. **Accuracy drop** > 3% over 2 weeks
2. **MAE increase** > 0.2 goals sustained
3. **Calibration drift** > 0.05
4. **Season transitions** (playoffs different from regular)

### Avoiding Overfitting
```python
def train_test_split_temporal(
    games: List[dict],
    test_ratio: float = 0.2
) -> Tuple[List, List]:
    """
    Split data temporally (not randomly) for proper evaluation.
    
    Important: Never use future data to predict past!
    """
    games_sorted = sorted(games, key=lambda g: g["date"])
    split_idx = int(len(games_sorted) * (1 - test_ratio))
    
    return games_sorted[:split_idx], games_sorted[split_idx:]
```

---

## Integration Points

### Daily Evaluation Script
```python
"""Run daily to track model performance."""
from datetime import date, timedelta

def daily_evaluation() -> dict:
    """Evaluate yesterday's predictions."""
    yesterday = date.today() - timedelta(days=1)
    
    # Load predictions made for yesterday
    predictions = load_predictions_for_date(yesterday)
    
    # Load actual results
    results = load_game_results(yesterday)
    
    # Match and evaluate
    matched = match_predictions_to_results(predictions, results)
    
    return {
        "date": yesterday.isoformat(),
        "games_evaluated": len(matched),
        "accuracy": calculate_accuracy(matched),
        "mae_total": calculate_mae(matched, "total"),
        "calibration": calibration_error(matched)
    }
```

---

## Next Steps
- Connect to [02-modeling.md](02-modeling.md) for model updates
- Feed metrics to [betting-metrics.md](../features/betting-metrics.md) for bet sizing
