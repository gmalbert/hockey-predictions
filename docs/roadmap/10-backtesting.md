# Backtesting Roadmap

## Overview
Validate prediction models against historical data to measure real-world performance before risking money.

---

## Why Backtest?

| Benefit | Description |
|---------|-------------|
| **Validate Edge** | Confirm model predictions outperform random guessing |
| **Tune Parameters** | Optimize thresholds (min edge, Kelly fraction) |
| **Identify Weaknesses** | Find situations where model underperforms |
| **Set Expectations** | Understand variance and drawdown patterns |

---

## Phase 1: Historical Data Collection

### Task 1.1: Game Results Storage
**File**: `src/data/game_results.py`

```python
"""Historical game results storage."""
import json
from pathlib import Path
from datetime import date
from dataclasses import dataclass, asdict
from typing import List, Optional

RESULTS_DIR = Path("data_files/results")

@dataclass
class GameResult:
    """Completed game result."""
    game_id: str
    date: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    home_won: bool
    went_to_ot: bool
    home_margin: int
    total_goals: int
    
    @classmethod
    def from_api(cls, game: dict) -> "GameResult":
        """Create from API response."""
        home_score = game.get("home_score", 0)
        away_score = game.get("away_score", 0)
        
        return cls(
            game_id=str(game["game_id"]),
            date=game.get("date", ""),
            home_team=game["home_team"],
            away_team=game["away_team"],
            home_score=home_score,
            away_score=away_score,
            home_won=home_score > away_score,
            went_to_ot=game.get("game_state") in ["OT", "SO"],
            home_margin=home_score - away_score,
            total_goals=home_score + away_score
        )

def save_results(results: List[GameResult], season: str = "20252026") -> None:
    """Save game results to JSON."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    file_path = RESULTS_DIR / f"{season}_results.json"
    
    # Load existing
    existing = []
    if file_path.exists():
        existing = json.loads(file_path.read_text())
    
    # Merge (avoid duplicates)
    existing_ids = {r["game_id"] for r in existing}
    new_results = [asdict(r) for r in results if r.game_id not in existing_ids]
    
    all_results = existing + new_results
    file_path.write_text(json.dumps(all_results, indent=2))

def load_results(season: str = "20252026") -> List[GameResult]:
    """Load game results from JSON."""
    file_path = RESULTS_DIR / f"{season}_results.json"
    
    if not file_path.exists():
        return []
    
    data = json.loads(file_path.read_text())
    return [GameResult(**r) for r in data]

def get_results_for_team(team: str, season: str = "20252026") -> List[GameResult]:
    """Get all results involving a team."""
    results = load_results(season)
    return [r for r in results if r.home_team == team or r.away_team == team]
```

### Task 1.2: Prediction Storage
**File**: `src/data/predictions.py`

```python
"""Historical predictions storage."""
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional

PREDICTIONS_DIR = Path("data_files/predictions")

@dataclass
class StoredPrediction:
    """Stored model prediction."""
    game_id: str
    date: str
    home_team: str
    away_team: str
    home_xg: float
    away_xg: float
    home_win_prob: float
    home_ml_odds: Optional[int]
    away_ml_odds: Optional[int]
    total_line: Optional[float]
    home_puck_line_prob: float  # Home -1.5
    model_version: str
    timestamp: str

def save_prediction(prediction: StoredPrediction) -> None:
    """Save a prediction."""
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Store by date
    date_file = PREDICTIONS_DIR / f"{prediction.date}.json"
    
    existing = []
    if date_file.exists():
        existing = json.loads(date_file.read_text())
    
    # Update or append
    updated = False
    for i, p in enumerate(existing):
        if p["game_id"] == prediction.game_id:
            existing[i] = asdict(prediction)
            updated = True
            break
    
    if not updated:
        existing.append(asdict(prediction))
    
    date_file.write_text(json.dumps(existing, indent=2))

def load_predictions(start_date: str, end_date: str) -> List[StoredPrediction]:
    """Load predictions for date range."""
    from datetime import datetime, timedelta
    
    predictions = []
    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        date_file = PREDICTIONS_DIR / f"{date_str}.json"
        
        if date_file.exists():
            data = json.loads(date_file.read_text())
            predictions.extend([StoredPrediction(**p) for p in data])
        
        current += timedelta(days=1)
    
    return predictions
```

---

## Phase 2: Backtesting Engine

### Task 2.1: Core Backtest Class
**File**: `src/backtest/engine.py`

```python
"""Backtesting engine."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from datetime import date

@dataclass
class BacktestConfig:
    """Backtesting configuration."""
    start_date: str
    end_date: str
    initial_bankroll: float = 1000.0
    unit_size: float = 10.0  # 1% of bankroll
    min_edge: float = 0.02  # 2% minimum edge to bet
    max_kelly_fraction: float = 0.25  # Max 25% Kelly
    bet_types: List[str] = field(default_factory=lambda: ["moneyline"])

@dataclass
class BacktestBet:
    """Single bet in backtest."""
    game_id: str
    date: str
    bet_type: str  # "home_ml", "away_ml", "home_pl", "away_pl", "over", "under"
    odds: int
    stake: float
    model_prob: float
    edge: float
    won: Optional[bool] = None
    profit: Optional[float] = None

@dataclass 
class BacktestResults:
    """Backtesting results summary."""
    config: BacktestConfig
    bets: List[BacktestBet]
    
    @property
    def total_bets(self) -> int:
        return len([b for b in self.bets if b.won is not None])
    
    @property
    def wins(self) -> int:
        return sum(1 for b in self.bets if b.won is True)
    
    @property
    def losses(self) -> int:
        return sum(1 for b in self.bets if b.won is False)
    
    @property
    def win_rate(self) -> float:
        if self.total_bets == 0:
            return 0.0
        return self.wins / self.total_bets
    
    @property
    def total_staked(self) -> float:
        return sum(b.stake for b in self.bets if b.won is not None)
    
    @property
    def total_profit(self) -> float:
        return sum(b.profit for b in self.bets if b.profit is not None)
    
    @property
    def roi(self) -> float:
        if self.total_staked == 0:
            return 0.0
        return (self.total_profit / self.total_staked) * 100
    
    @property
    def units_profit(self) -> float:
        return self.total_profit / self.config.unit_size
    
    def max_drawdown(self) -> float:
        """Calculate maximum drawdown."""
        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0
        
        for bet in self.bets:
            if bet.profit is not None:
                cumulative += bet.profit
                peak = max(peak, cumulative)
                drawdown = peak - cumulative
                max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def longest_losing_streak(self) -> int:
        """Find longest consecutive losing streak."""
        max_streak = 0
        current_streak = 0
        
        for bet in self.bets:
            if bet.won is False:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def summary(self) -> str:
        """Return formatted summary."""
        return f"""
Backtest Results: {self.config.start_date} to {self.config.end_date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Bets:        {self.total_bets}
Record:            {self.wins}-{self.losses} ({self.win_rate:.1%})
Total Staked:      ${self.total_staked:,.2f}
Total Profit:      ${self.total_profit:+,.2f}
ROI:               {self.roi:+.2f}%
Units:             {self.units_profit:+.1f}u
Max Drawdown:      ${self.max_drawdown():,.2f}
Longest Losing:    {self.longest_losing_streak()} bets
"""


class BacktestEngine:
    """Run backtests against historical data."""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.bets: List[BacktestBet] = []
    
    def run(
        self,
        predictions: List[Dict],
        results: List[Dict],
        odds_history: Optional[Dict] = None
    ) -> BacktestResults:
        """
        Run backtest.
        
        Args:
            predictions: List of prediction dicts with game_id, probs, etc.
            results: List of game result dicts
            odds_history: Optional dict of game_id -> odds snapshot
        
        Returns:
            BacktestResults with all metrics
        """
        # Index results by game_id
        results_map = {str(r["game_id"]): r for r in results}
        
        for pred in predictions:
            game_id = str(pred["game_id"])
            
            if game_id not in results_map:
                continue
            
            result = results_map[game_id]
            
            # Get odds (use provided or estimate from probability)
            if odds_history and game_id in odds_history:
                odds = odds_history[game_id]
            else:
                # Estimate odds from no-vig line
                odds = self._estimate_odds(pred)
            
            # Check for moneyline value
            if "moneyline" in self.config.bet_types:
                self._evaluate_moneyline_bet(pred, result, odds)
            
            # Check for puck line value
            if "puck_line" in self.config.bet_types:
                self._evaluate_puck_line_bet(pred, result, odds)
        
        return BacktestResults(config=self.config, bets=self.bets)
    
    def _evaluate_moneyline_bet(self, pred: Dict, result: Dict, odds: Dict) -> None:
        """Evaluate moneyline betting opportunity."""
        from src.utils.odds import american_to_implied, calculate_edge
        
        home_prob = pred.get("home_win_prob", 0.5)
        away_prob = 1 - home_prob
        
        home_odds = odds.get("home_ml", -110)
        away_odds = odds.get("away_ml", -110)
        
        # Check home ML
        home_edge = calculate_edge(home_prob, home_odds)
        if home_edge["edge_pct"] / 100 >= self.config.min_edge:
            stake = self._calculate_stake(home_edge["kelly_fraction"])
            won = result.get("home_won", False)
            profit = self._calculate_profit(stake, home_odds, won)
            
            self.bets.append(BacktestBet(
                game_id=str(pred["game_id"]),
                date=pred.get("date", ""),
                bet_type="home_ml",
                odds=home_odds,
                stake=stake,
                model_prob=home_prob,
                edge=home_edge["edge_pct"] / 100,
                won=won,
                profit=profit
            ))
        
        # Check away ML
        away_edge = calculate_edge(away_prob, away_odds)
        if away_edge["edge_pct"] / 100 >= self.config.min_edge:
            stake = self._calculate_stake(away_edge["kelly_fraction"])
            won = not result.get("home_won", True)
            profit = self._calculate_profit(stake, away_odds, won)
            
            self.bets.append(BacktestBet(
                game_id=str(pred["game_id"]),
                date=pred.get("date", ""),
                bet_type="away_ml",
                odds=away_odds,
                stake=stake,
                model_prob=away_prob,
                edge=away_edge["edge_pct"] / 100,
                won=won,
                profit=profit
            ))
    
    def _evaluate_puck_line_bet(self, pred: Dict, result: Dict, odds: Dict) -> None:
        """Evaluate puck line betting opportunity."""
        from src.utils.odds import calculate_edge
        
        home_pl_prob = pred.get("home_puck_line_prob", 0.35)
        away_pl_prob = 1 - home_pl_prob
        
        home_pl_odds = odds.get("home_pl_odds", 150)
        away_pl_odds = odds.get("away_pl_odds", -180)
        
        margin = result.get("home_margin", 0)
        
        # Home -1.5
        home_edge = calculate_edge(home_pl_prob, home_pl_odds)
        if home_edge["edge_pct"] / 100 >= self.config.min_edge:
            stake = self._calculate_stake(home_edge["kelly_fraction"])
            won = margin >= 2
            profit = self._calculate_profit(stake, home_pl_odds, won)
            
            self.bets.append(BacktestBet(
                game_id=str(pred["game_id"]),
                date=pred.get("date", ""),
                bet_type="home_pl",
                odds=home_pl_odds,
                stake=stake,
                model_prob=home_pl_prob,
                edge=home_edge["edge_pct"] / 100,
                won=won,
                profit=profit
            ))
        
        # Away +1.5
        away_edge = calculate_edge(away_pl_prob, away_pl_odds)
        if away_edge["edge_pct"] / 100 >= self.config.min_edge:
            stake = self._calculate_stake(away_edge["kelly_fraction"])
            won = margin <= 1
            profit = self._calculate_profit(stake, away_pl_odds, won)
            
            self.bets.append(BacktestBet(
                game_id=str(pred["game_id"]),
                date=pred.get("date", ""),
                bet_type="away_pl",
                odds=away_pl_odds,
                stake=stake,
                model_prob=away_pl_prob,
                edge=away_edge["edge_pct"] / 100,
                won=won,
                profit=profit
            ))
    
    def _calculate_stake(self, kelly_fraction: float) -> float:
        """Calculate bet stake using Kelly criterion."""
        kelly = min(kelly_fraction, self.config.max_kelly_fraction)
        return self.config.unit_size * (kelly / 0.05)  # Normalize to 5% Kelly = 1 unit
    
    def _calculate_profit(self, stake: float, odds: int, won: bool) -> float:
        """Calculate profit/loss for a bet."""
        if not won:
            return -stake
        
        if odds > 0:
            return stake * (odds / 100)
        else:
            return stake * (100 / abs(odds))
    
    def _estimate_odds(self, pred: Dict) -> Dict:
        """Estimate odds from model probability (no-vig)."""
        from src.utils.odds import implied_to_american
        
        home_prob = pred.get("home_win_prob", 0.5)
        
        return {
            "home_ml": implied_to_american(home_prob),
            "away_ml": implied_to_american(1 - home_prob),
            "home_pl_odds": 150,  # Default puck line odds
            "away_pl_odds": -180
        }
```

---

## Phase 3: Analysis & Visualization

### Task 3.1: Performance by Situation
**File**: `src/backtest/analysis.py`

```python
"""Backtest analysis functions."""
from typing import List, Dict
from collections import defaultdict

def analyze_by_bet_type(bets: List[Dict]) -> Dict:
    """Analyze performance by bet type."""
    by_type = defaultdict(lambda: {"bets": 0, "wins": 0, "profit": 0})
    
    for bet in bets:
        bt = bet["bet_type"]
        by_type[bt]["bets"] += 1
        if bet["won"]:
            by_type[bt]["wins"] += 1
        by_type[bt]["profit"] += bet["profit"]
    
    results = {}
    for bt, data in by_type.items():
        results[bt] = {
            "bets": data["bets"],
            "win_rate": data["wins"] / data["bets"] if data["bets"] > 0 else 0,
            "profit": data["profit"],
            "roi": (data["profit"] / (data["bets"] * 10)) * 100 if data["bets"] > 0 else 0
        }
    
    return results

def analyze_by_edge_bucket(bets: List[Dict]) -> Dict:
    """Analyze performance by edge size."""
    buckets = {
        "2-5%": {"min": 0.02, "max": 0.05},
        "5-10%": {"min": 0.05, "max": 0.10},
        "10%+": {"min": 0.10, "max": 1.0}
    }
    
    results = {}
    for name, bounds in buckets.items():
        bucket_bets = [
            b for b in bets 
            if bounds["min"] <= b["edge"] < bounds["max"]
        ]
        
        if bucket_bets:
            results[name] = {
                "bets": len(bucket_bets),
                "win_rate": sum(1 for b in bucket_bets if b["won"]) / len(bucket_bets),
                "profit": sum(b["profit"] for b in bucket_bets),
                "avg_edge": sum(b["edge"] for b in bucket_bets) / len(bucket_bets)
            }
    
    return results

def analyze_by_odds_range(bets: List[Dict]) -> Dict:
    """Analyze performance by odds range."""
    ranges = {
        "Heavy Favorite (<-200)": lambda o: o < -200,
        "Favorite (-200 to -110)": lambda o: -200 <= o < -110,
        "Even (-110 to +110)": lambda o: -110 <= o <= 110,
        "Underdog (+110 to +200)": lambda o: 110 < o <= 200,
        "Big Underdog (>+200)": lambda o: o > 200
    }
    
    results = {}
    for name, check in ranges.items():
        range_bets = [b for b in bets if check(b["odds"])]
        
        if range_bets:
            results[name] = {
                "bets": len(range_bets),
                "win_rate": sum(1 for b in range_bets if b["won"]) / len(range_bets),
                "profit": sum(b["profit"] for b in range_bets)
            }
    
    return results

def cumulative_profit_series(bets: List[Dict]) -> List[float]:
    """Get cumulative profit over time."""
    cumulative = []
    total = 0.0
    
    for bet in sorted(bets, key=lambda b: b["date"]):
        total += bet["profit"]
        cumulative.append(total)
    
    return cumulative
```

### Task 3.2: Streamlit Backtest Page
**File**: `src/pages/11_🔬_Backtest.py`

```python
"""Backtesting interface."""
import streamlit as st
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="Backtest", page_icon="🔬", layout="wide")
st.title("🔬 Backtesting")

st.markdown("""
Test model performance against historical data to validate predictions
before betting real money.
""")

# Configuration
st.sidebar.subheader("Backtest Settings")

col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input(
        "Start Date",
        value=date.today() - timedelta(days=90)
    )
with col2:
    end_date = st.date_input(
        "End Date",
        value=date.today() - timedelta(days=1)
    )

min_edge = st.sidebar.slider("Minimum Edge %", 1, 15, 3) / 100
bet_types = st.sidebar.multiselect(
    "Bet Types",
    ["moneyline", "puck_line"],
    default=["moneyline"]
)

if st.sidebar.button("Run Backtest", type="primary"):
    with st.spinner("Running backtest..."):
        # Placeholder - replace with actual backtest
        st.success("Backtest complete!")

# Results display
st.subheader("Results Summary")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Bets", "0")
with col2:
    st.metric("Win Rate", "0%")
with col3:
    st.metric("ROI", "0%")
with col4:
    st.metric("Units", "0")

# Equity curve
st.subheader("Equity Curve")
st.line_chart({"Cumulative Profit": [0]})

# Breakdown tables
tab1, tab2, tab3 = st.tabs(["By Bet Type", "By Edge", "By Odds"])

with tab1:
    st.markdown("Performance breakdown by bet type")
    
with tab2:
    st.markdown("Performance breakdown by edge bucket")
    
with tab3:
    st.markdown("Performance breakdown by odds range")
```

---

## Best Practices

### Avoiding Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| **Look-ahead bias** | Only use data available at prediction time |
| **Survivorship bias** | Include all games, not just memorable ones |
| **Overfitting** | Use out-of-sample testing (70/30 split) |
| **Ignoring variance** | Run multiple simulations with different parameters |
| **Unrealistic odds** | Use actual closing lines when possible |

### Sample Size Guidelines

| Metric | Minimum Bets | Confidence |
|--------|--------------|------------|
| Win Rate | 100 | ±5% |
| ROI | 500 | ±2% |
| Edge validation | 1000 | High |

---

## Next Steps
- Connect to [09-model-evaluation.md](09-model-evaluation.md) for metrics
- See [02-modeling.md](02-modeling.md) for model improvements
