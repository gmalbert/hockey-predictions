# Data Modeling Roadmap

## Overview
Prediction models for NHL betting, progressing from simple heuristics to ML-based approaches.

---

## Phase 1: Foundation Metrics

### Task 1.1: Expected Goals (xG) Calculator
**File**: `src/models/expected_goals.py`

```python
"""Expected goals calculations for game predictions."""
from dataclasses import dataclass
from typing import Optional

@dataclass
class TeamMetrics:
    """Core team statistics for predictions."""
    goals_for_pg: float
    goals_against_pg: float
    shots_for_pg: float
    shots_against_pg: float
    pp_pct: float
    pk_pct: float
    
    @property
    def shooting_pct(self) -> float:
        """Team shooting percentage."""
        if self.shots_for_pg == 0:
            return 0.0
        return (self.goals_for_pg / self.shots_for_pg) * 100
    
    @property
    def save_pct(self) -> float:
        """Implied save percentage against."""
        if self.shots_against_pg == 0:
            return 0.0
        goals_allowed_rate = self.goals_against_pg / self.shots_against_pg
        return (1 - goals_allowed_rate) * 100

def calculate_expected_goals(
    home_team: TeamMetrics,
    away_team: TeamMetrics,
    home_advantage: float = 0.15
) -> tuple[float, float]:
    """
    Calculate expected goals for each team.
    
    Args:
        home_team: Home team statistics
        away_team: Away team statistics
        home_advantage: Goal boost for home team (default 15%)
    
    Returns:
        Tuple of (home_expected_goals, away_expected_goals)
    """
    # Home team: their offense vs away defense
    home_xg = (
        (home_team.goals_for_pg + away_team.goals_against_pg) / 2
    ) * (1 + home_advantage)
    
    # Away team: their offense vs home defense
    away_xg = (
        (away_team.goals_for_pg + home_team.goals_against_pg) / 2
    ) * (1 - home_advantage / 2)  # Road disadvantage
    
    return round(home_xg, 2), round(away_xg, 2)
```

### Task 1.2: Win Probability Model
**File**: `src/models/win_probability.py`

```python
"""Win probability calculations using Poisson distribution."""
import math
from typing import NamedTuple

class GameProbabilities(NamedTuple):
    """Probabilities for game outcomes."""
    home_win: float
    away_win: float
    home_regulation: float
    away_regulation: float
    overtime: float

def poisson_prob(expected: float, actual: int) -> float:
    """Calculate Poisson probability P(X = actual)."""
    return (math.exp(-expected) * (expected ** actual)) / math.factorial(actual)

def calculate_win_probability(
    home_xg: float,
    away_xg: float,
    max_goals: int = 10
) -> GameProbabilities:
    """
    Calculate win probabilities using Poisson model.
    
    Args:
        home_xg: Expected goals for home team
        away_xg: Expected goals for away team
        max_goals: Maximum goals to consider per team
    
    Returns:
        GameProbabilities with all outcome probabilities
    """
    home_reg_win = 0.0
    away_reg_win = 0.0
    tie_prob = 0.0
    
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            prob = poisson_prob(home_xg, h) * poisson_prob(away_xg, a)
            
            if h > a:
                home_reg_win += prob
            elif a > h:
                away_reg_win += prob
            else:
                tie_prob += prob
    
    # OT/SO split: assume 50/50 for ties
    ot_home_win = tie_prob * 0.52  # Slight home advantage in OT
    ot_away_win = tie_prob * 0.48
    
    return GameProbabilities(
        home_win=round(home_reg_win + ot_home_win, 4),
        away_win=round(away_reg_win + ot_away_win, 4),
        home_regulation=round(home_reg_win, 4),
        away_regulation=round(away_reg_win, 4),
        overtime=round(tie_prob, 4)
    )
```

---

## Phase 2: Betting Value Calculator

### Task 2.1: Odds Converter
**File**: `src/utils/odds.py`

```python
"""Odds conversion and value calculation utilities."""
from typing import Optional

def american_to_implied(american_odds: int) -> float:
    """Convert American odds to implied probability."""
    if american_odds > 0:
        return 100 / (american_odds + 100)
    else:
        return abs(american_odds) / (abs(american_odds) + 100)

def implied_to_american(probability: float) -> int:
    """Convert implied probability to American odds."""
    if probability >= 0.5:
        return int(-100 * probability / (1 - probability))
    else:
        return int(100 * (1 - probability) / probability)

def calculate_edge(
    model_prob: float,
    book_odds: int
) -> dict[str, float]:
    """
    Calculate betting edge.
    
    Args:
        model_prob: Model's predicted probability (0-1)
        book_odds: Bookmaker's American odds
    
    Returns:
        Dictionary with edge metrics
    """
    implied_prob = american_to_implied(book_odds)
    edge = model_prob - implied_prob
    
    # Kelly criterion for optimal bet sizing
    if edge > 0 and book_odds != 0:
        if book_odds > 0:
            decimal_odds = (book_odds / 100) + 1
        else:
            decimal_odds = (100 / abs(book_odds)) + 1
        
        kelly = (decimal_odds * model_prob - 1) / (decimal_odds - 1)
        kelly = max(0, kelly)  # No negative bets
    else:
        kelly = 0.0
    
    return {
        "model_prob": round(model_prob * 100, 1),
        "implied_prob": round(implied_prob * 100, 1),
        "edge_pct": round(edge * 100, 1),
        "kelly_fraction": round(kelly, 4),
        "has_value": edge > 0.02  # 2% minimum edge
    }
```

### Task 2.2: Total Goals Model (Over/Under)
**File**: `src/models/totals.py`

```python
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
```

---

## Phase 3: Advanced Models (Future)

### Task 3.1: Situational Adjustments
Factors to incorporate:
- **Back-to-back games**: -0.2 goals expected
- **Rest advantage**: +0.1 per extra rest day
- **Travel distance**: Penalty for cross-country travel
- **Goalie status**: Starter vs backup adjustments

### Task 3.2: Machine Learning Pipeline (Future)
**File**: `src/models/ml_predictor.py`

```python
"""Machine learning model for game predictions (skeleton)."""
from pathlib import Path
from typing import Optional
import pickle

class NHLPredictor:
    """ML-based game outcome predictor."""
    
    MODEL_PATH = Path("data_files/models/predictor.pkl")
    
    def __init__(self):
        self.model = None
        self.feature_columns: list[str] = []
    
    def load(self) -> bool:
        """Load trained model from disk."""
        if self.MODEL_PATH.exists():
            with open(self.MODEL_PATH, "rb") as f:
                saved = pickle.load(f)
                self.model = saved["model"]
                self.feature_columns = saved["features"]
            return True
        return False
    
    def save(self) -> None:
        """Save trained model to disk."""
        self.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.MODEL_PATH, "wb") as f:
            pickle.dump({
                "model": self.model,
                "features": self.feature_columns
            }, f)
    
    # TODO: Implement training pipeline with historical data
    # TODO: Feature engineering from team/player stats
    # TODO: Hyperparameter tuning
```

---

## Model Validation

### Backtesting Framework
**File**: `src/models/backtest.py`

```python
"""Backtesting framework for model validation."""
from dataclasses import dataclass, field
from typing import List

@dataclass
class BetResult:
    """Single bet outcome."""
    game_id: str
    prediction: str  # "home", "away", "over", "under"
    odds: int
    stake: float
    won: bool
    profit: float

@dataclass
class BacktestResults:
    """Aggregated backtesting results."""
    total_bets: int = 0
    wins: int = 0
    losses: int = 0
    total_staked: float = 0.0
    total_profit: float = 0.0
    bets: List[BetResult] = field(default_factory=list)
    
    @property
    def win_rate(self) -> float:
        if self.total_bets == 0:
            return 0.0
        return self.wins / self.total_bets
    
    @property
    def roi(self) -> float:
        if self.total_staked == 0:
            return 0.0
        return (self.total_profit / self.total_staked) * 100
    
    def add_bet(self, bet: BetResult) -> None:
        self.bets.append(bet)
        self.total_bets += 1
        self.total_staked += bet.stake
        self.total_profit += bet.profit
        if bet.won:
            self.wins += 1
        else:
            self.losses += 1
```

---

## Next Steps
- See [03-layout.md](03-layout.md) for Streamlit UI implementation
- See [betting-metrics.md](../features/betting-metrics.md) for key statistics
