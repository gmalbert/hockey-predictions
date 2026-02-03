# Long-Term Roadmap

## Overview
Advanced features and scaling improvements for months 2-6 and beyond.

---

## Phase 1: Enhanced Predictions (Month 2)

### Situational Modeling
Adjust predictions based on context.

**File**: `src/models/situational.py`
```python
"""Situational adjustments for predictions."""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

@dataclass
class GameContext:
    """Contextual factors for a game."""
    home_team: str
    away_team: str
    game_date: date
    home_last_game: Optional[date] = None
    away_last_game: Optional[date] = None
    home_travel_miles: float = 0
    away_travel_miles: float = 0

def calculate_rest_adjustment(last_game: Optional[date], game_date: date) -> float:
    """
    Calculate goal adjustment based on rest days.
    
    Returns:
        Adjustment factor (positive = more goals expected)
    """
    if last_game is None:
        return 0.0
    
    rest_days = (game_date - last_game).days - 1  # -1 because day before counts
    
    if rest_days == 0:  # Back-to-back
        return -0.20  # Expect 0.2 fewer goals
    elif rest_days == 1:  # Normal rest
        return 0.0
    elif rest_days == 2:  # Extra rest
        return 0.05
    else:  # Extended rest (3+)
        return 0.08

def calculate_travel_adjustment(miles: float) -> float:
    """
    Calculate goal adjustment based on travel distance.
    
    Cross-country travel (2500+ miles) has fatigue impact.
    """
    if miles < 500:
        return 0.0
    elif miles < 1500:
        return -0.05
    elif miles < 2500:
        return -0.10
    else:  # Cross-country
        return -0.15

def apply_situational_adjustments(
    base_xg: float,
    context: GameContext,
    is_home_team: bool
) -> float:
    """Apply all situational adjustments to expected goals."""
    if is_home_team:
        rest_adj = calculate_rest_adjustment(context.home_last_game, context.game_date)
        travel_adj = calculate_travel_adjustment(context.home_travel_miles)
    else:
        rest_adj = calculate_rest_adjustment(context.away_last_game, context.game_date)
        travel_adj = calculate_travel_adjustment(context.away_travel_miles)
    
    return base_xg + rest_adj + travel_adj
```

### Goalie Impact Model
**File**: `src/models/goalie.py`
```python
"""Goalie-based adjustments."""
from dataclasses import dataclass
from typing import Optional

@dataclass
class GoalieStats:
    """Goalie performance metrics."""
    player_id: int
    name: str
    games_started: int
    save_pct: float
    goals_against_avg: float
    quality_starts: int
    
    @property
    def quality_start_pct(self) -> float:
        if self.games_started == 0:
            return 0.0
        return self.quality_starts / self.games_started

def goalie_adjustment(
    goalie: Optional[GoalieStats],
    league_avg_save_pct: float = 0.905
) -> float:
    """
    Calculate goals adjustment based on goalie vs league average.
    
    Returns:
        Adjustment to opponent's expected goals
    """
    if goalie is None:
        return 0.0
    
    save_pct_diff = goalie.save_pct - league_avg_save_pct
    
    # Each 1% better save pct = ~0.3 fewer goals allowed per game
    return -save_pct_diff * 30
```

---

## Phase 2: Advanced Analytics (Month 3)

### Head-to-Head Analysis
**File**: `src/models/head_to_head.py`
```python
"""Head-to-head matchup analysis."""
import pandas as pd
from typing import Optional

def analyze_h2h(
    games_df: pd.DataFrame,
    team1: str,
    team2: str,
    last_n_games: int = 10
) -> dict:
    """
    Analyze recent head-to-head matchups.
    
    Args:
        games_df: DataFrame with historical game data
        team1: First team abbreviation
        team2: Second team abbreviation
        last_n_games: Number of recent games to analyze
    
    Returns:
        Dictionary with H2H statistics
    """
    # Filter for matchups between these teams
    h2h = games_df[
        ((games_df["home_team"] == team1) & (games_df["away_team"] == team2)) |
        ((games_df["home_team"] == team2) & (games_df["away_team"] == team1))
    ].tail(last_n_games)
    
    if h2h.empty:
        return {"games": 0, "team1_wins": 0, "team2_wins": 0}
    
    team1_wins = 0
    team2_wins = 0
    total_goals = 0
    
    for _, game in h2h.iterrows():
        home_score = game.get("home_score", 0)
        away_score = game.get("away_score", 0)
        total_goals += home_score + away_score
        
        if game["home_team"] == team1:
            if home_score > away_score:
                team1_wins += 1
            else:
                team2_wins += 1
        else:
            if away_score > home_score:
                team1_wins += 1
            else:
                team2_wins += 1
    
    return {
        "games": len(h2h),
        "team1_wins": team1_wins,
        "team2_wins": team2_wins,
        "avg_total_goals": round(total_goals / len(h2h), 2) if len(h2h) > 0 else 0,
        "team1_win_pct": round(team1_wins / len(h2h), 3) if len(h2h) > 0 else 0.5
    }
```

### Player Props Engine
**File**: `src/models/player_props.py`
```python
"""Player prop betting analysis."""
import pandas as pd
from dataclasses import dataclass
from typing import List

@dataclass
class PropPrediction:
    """Player prop prediction."""
    player_id: int
    player_name: str
    prop_type: str  # "goals", "assists", "points", "shots"
    line: float
    over_probability: float
    under_probability: float
    expected_value: float

def predict_player_goals(
    player_stats: dict,
    opponent_stats: dict,
    line: float = 0.5
) -> PropPrediction:
    """
    Predict probability of a player going over/under goals line.
    
    Uses player's goals per game vs opponent's goals against per game.
    """
    import math
    
    # Player's scoring rate
    player_gpg = player_stats.get("goals", 0) / max(player_stats.get("games", 1), 1)
    
    # Adjust for opponent defense
    opp_ga_pg = opponent_stats.get("goals_against_pg", 3.0)
    league_avg_goals = 3.0
    
    # Adjusted expected goals
    defensive_factor = opp_ga_pg / league_avg_goals
    expected_goals = player_gpg * defensive_factor
    
    # Poisson probability of scoring at least 'line' goals
    over_prob = 0.0
    for goals in range(int(line) + 1, 8):  # Cap at 7 goals
        prob = (math.exp(-expected_goals) * (expected_goals ** goals)) / math.factorial(goals)
        over_prob += prob
    
    return PropPrediction(
        player_id=player_stats.get("player_id", 0),
        player_name=player_stats.get("name", "Unknown"),
        prop_type="goals",
        line=line,
        over_probability=round(over_prob, 4),
        under_probability=round(1 - over_prob, 4),
        expected_value=round(expected_goals, 3)
    )
```

---

## Phase 3: Machine Learning (Month 4-5)

### Feature Engineering
**File**: `src/models/features.py`
```python
"""Feature engineering for ML models."""
import pandas as pd
from typing import List

def create_game_features(
    game: dict,
    home_stats: dict,
    away_stats: dict,
    home_recent: pd.DataFrame,
    away_recent: pd.DataFrame
) -> dict:
    """
    Create feature vector for a game prediction.
    
    Returns:
        Dictionary of features for ML model
    """
    features = {
        # Team strength indicators
        "home_goal_diff": home_stats.get("goals_for_pg", 0) - home_stats.get("goals_against_pg", 0),
        "away_goal_diff": away_stats.get("goals_for_pg", 0) - away_stats.get("goals_against_pg", 0),
        "home_pp_pct": home_stats.get("pp_pct", 0),
        "away_pp_pct": away_stats.get("pp_pct", 0),
        "home_pk_pct": home_stats.get("pk_pct", 0),
        "away_pk_pct": away_stats.get("pk_pct", 0),
        
        # Recent form (last 10 games)
        "home_l10_win_pct": _calculate_win_pct(home_recent),
        "away_l10_win_pct": _calculate_win_pct(away_recent),
        "home_l10_goals_avg": home_recent["team_score"].mean() if not home_recent.empty else 0,
        "away_l10_goals_avg": away_recent["team_score"].mean() if not away_recent.empty else 0,
        
        # Situational
        "home_rest_days": game.get("home_rest_days", 1),
        "away_rest_days": game.get("away_rest_days", 1),
        "is_back_to_back_home": game.get("home_rest_days", 1) == 0,
        "is_back_to_back_away": game.get("away_rest_days", 1) == 0,
    }
    
    return features

def _calculate_win_pct(recent_games: pd.DataFrame) -> float:
    if recent_games.empty:
        return 0.5
    wins = (recent_games["result"] == "W").sum()
    return wins / len(recent_games)
```

### Model Training Pipeline
**File**: `src/models/training.py`
```python
"""Model training and evaluation."""
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, log_loss
import pickle

MODEL_PATH = Path("data_files/models")

def train_game_outcome_model(
    features_df: pd.DataFrame,
    target: str = "home_win"
) -> dict:
    """
    Train a model to predict game outcomes.
    
    Args:
        features_df: DataFrame with features and target
        target: Target column name
    
    Returns:
        Dictionary with model and metrics
    """
    MODEL_PATH.mkdir(parents=True, exist_ok=True)
    
    # Prepare data
    X = features_df.drop(columns=[target, "game_id"], errors="ignore")
    y = features_df[target]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train model
    model = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)
    test_proba = model.predict_proba(X_test)
    
    metrics = {
        "train_accuracy": accuracy_score(y_train, train_pred),
        "test_accuracy": accuracy_score(y_test, test_pred),
        "log_loss": log_loss(y_test, test_proba),
        "cv_scores": cross_val_score(model, X, y, cv=5).tolist()
    }
    
    # Save model
    with open(MODEL_PATH / "game_outcome.pkl", "wb") as f:
        pickle.dump({"model": model, "features": list(X.columns)}, f)
    
    return {"model": model, "metrics": metrics}
```

---

## Phase 4: Production Features (Month 6+)

### Line Movement Tracking
- Store historical odds from external source
- Track line movement patterns
- Identify sharp money indicators

### Real-Time Updates
- WebSocket connection for live scores
- In-play betting insights
- Live probability updates

### Notification System
**File**: `src/utils/notifications.py`
```python
"""Notification system for alerts."""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class BetAlert:
    """Alert for betting opportunity."""
    game_id: str
    alert_type: str  # "value_bet", "line_movement", "injury"
    message: str
    edge: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

def create_value_alert(
    game: dict,
    bet_type: str,
    edge: float,
    model_prob: float,
    odds: int
) -> BetAlert:
    """Create alert for value betting opportunity."""
    home = game.get("home_team", "HOME")
    away = game.get("away_team", "AWAY")
    
    return BetAlert(
        game_id=game.get("game_id", ""),
        alert_type="value_bet",
        message=f"Value: {away}@{home} - {bet_type} at {odds} (edge: {edge:.1f}%)",
        edge=edge
    )
```

### API Rate Limiting
**File**: `src/api/rate_limiter.py`
```python
"""Rate limiting for API calls."""
import time
from collections import deque
from threading import Lock

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, requests_per_minute: int = 30):
        self.rate = requests_per_minute
        self.window = 60  # seconds
        self.requests = deque()
        self.lock = Lock()
    
    def acquire(self) -> None:
        """Wait until request is allowed."""
        with self.lock:
            now = time.time()
            
            # Remove old requests outside window
            while self.requests and self.requests[0] < now - self.window:
                self.requests.popleft()
            
            # Wait if at limit
            if len(self.requests) >= self.rate:
                sleep_time = self.requests[0] + self.window - now
                time.sleep(max(0, sleep_time))
            
            self.requests.append(time.time())
```

---

## Infrastructure Improvements

### Caching Strategy
- Redis for shared cache (multi-user)
- TTL policies: live data (1 min), stats (1 hour), historical (24 hours)

### Database
- SQLite for MVP
- PostgreSQL for production
- Store: games, predictions, bet results

### Deployment
- Docker containerization
- Cloud hosting (Streamlit Cloud or Railway)
- CI/CD with GitHub Actions

---

## Feature Wishlist

| Feature | Priority | Effort | Impact |
|---------|----------|--------|--------|
| Goalie-adjusted predictions | High | Medium | High |
| Player props engine | High | High | High |
| Historical backtesting UI | Medium | Medium | Medium |
| Line movement alerts | Medium | Low | Medium |
| ML-based predictions | Medium | High | High |
| Mobile-responsive UI | Low | Medium | Low |
| Discord/email alerts | Low | Low | Medium |
| Multiple sportsbook odds | Low | High | High |

---

## Success Metrics

- **Model accuracy**: Target 55%+ on moneyline picks
- **ROI**: Target positive ROI over 100+ bets
- **User engagement**: Track page views, feature usage
- **Prediction calibration**: Predicted probabilities match actual outcomes
