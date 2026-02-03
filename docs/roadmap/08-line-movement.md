# Line Movement Tracking Roadmap

## Overview
Line movement analysis helps identify sharp money and market inefficiencies. Significant line moves often indicate informed betting activity.

---

## Key Concepts

### Line Types
| Line Type | Description | Movement Significance |
|-----------|-------------|----------------------|
| **Moneyline** | Win probability | 10+ cent moves notable |
| **Puck Line** | -1.5/+1.5 spread | Juice moves meaningful |
| **Total** | Over/Under goals | 0.5 goal moves significant |

### Movement Types
| Movement | Description | Implication |
|----------|-------------|-------------|
| **Steam move** | Sharp, fast movement | Professional money |
| **Reverse line** | Move against public | Sharp action |
| **Line freeze** | No movement despite action | Books uncertain |

---

## Phase 1: Line Data Structure

### Task 1.1: Odds Data Models
**File**: `src/models/odds.py`

```python
"""Odds and line movement data models."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class OddsFormat(Enum):
    AMERICAN = "american"
    DECIMAL = "decimal"
    
@dataclass
class OddsSnapshot:
    """Point-in-time odds capture."""
    timestamp: datetime
    home_ml: int
    away_ml: int
    home_puck_line: float  # Usually -1.5
    home_pl_odds: int
    away_puck_line: float  # Usually +1.5
    away_pl_odds: int
    total: float
    over_odds: int
    under_odds: int
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "home_ml": self.home_ml,
            "away_ml": self.away_ml,
            "home_pl": self.home_puck_line,
            "home_pl_odds": self.home_pl_odds,
            "away_pl": self.away_puck_line,
            "away_pl_odds": self.away_pl_odds,
            "total": self.total,
            "over": self.over_odds,
            "under": self.under_odds
        }

@dataclass
class GameOdds:
    """All odds snapshots for a game."""
    game_id: str
    home_team: str
    away_team: str
    game_time: datetime
    snapshots: List[OddsSnapshot] = field(default_factory=list)
    
    @property
    def opening_odds(self) -> Optional[OddsSnapshot]:
        """First recorded odds."""
        return self.snapshots[0] if self.snapshots else None
    
    @property
    def current_odds(self) -> Optional[OddsSnapshot]:
        """Most recent odds."""
        return self.snapshots[-1] if self.snapshots else None
    
    @property
    def moneyline_movement(self) -> Optional[int]:
        """Change in home ML from open to current."""
        if self.opening_odds and self.current_odds:
            return self.current_odds.home_ml - self.opening_odds.home_ml
        return None
    
    @property
    def total_movement(self) -> Optional[float]:
        """Change in total from open to current."""
        if self.opening_odds and self.current_odds:
            return self.current_odds.total - self.opening_odds.total
        return None
```

### Task 1.2: Line Movement Analyzer
**File**: `src/models/line_movement.py`

```python
"""Analyze line movements for betting signals."""
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class MovementType(Enum):
    STEAM = "steam"          # Sharp, fast move
    DRIFT = "drift"          # Gradual move
    REVERSE = "reverse"      # Against public betting
    STABLE = "stable"        # No significant movement

@dataclass
class LineMovementAnalysis:
    """Analysis of line movement."""
    game_id: str
    movement_type: MovementType
    direction: str  # "home", "away", "over", "under"
    magnitude: float
    is_sharp_action: bool
    confidence: str
    recommendation: str

def analyze_moneyline_movement(
    opening_home_ml: int,
    current_home_ml: int,
    hours_until_game: float
) -> LineMovementAnalysis:
    """
    Analyze moneyline movement for sharp action.
    
    Sharp indicators:
    - Movement against public team
    - Fast, significant moves (>15 cents)
    - Late movement (within 2 hours of game)
    """
    movement = current_home_ml - opening_home_ml
    
    # Determine direction
    if movement < -10:  # Home became more favored
        direction = "home"
    elif movement > 10:
        direction = "away"
    else:
        direction = "none"
    
    magnitude = abs(movement)
    
    # Classify movement type
    if magnitude >= 20 and hours_until_game < 2:
        movement_type = MovementType.STEAM
        is_sharp = True
        confidence = "high"
    elif magnitude >= 15:
        movement_type = MovementType.STEAM
        is_sharp = True
        confidence = "medium"
    elif magnitude >= 8:
        movement_type = MovementType.DRIFT
        is_sharp = False
        confidence = "low"
    else:
        movement_type = MovementType.STABLE
        is_sharp = False
        confidence = "low"
    
    # Recommendation
    if is_sharp and direction != "none":
        recommendation = f"Consider {direction} ML - sharp movement detected"
    else:
        recommendation = "No clear signal from line movement"
    
    return LineMovementAnalysis(
        game_id="",
        movement_type=movement_type,
        direction=direction,
        magnitude=magnitude,
        is_sharp_action=is_sharp,
        confidence=confidence,
        recommendation=recommendation
    )

def analyze_total_movement(
    opening_total: float,
    current_total: float,
    opening_over_odds: int,
    current_over_odds: int
) -> LineMovementAnalysis:
    """Analyze total movement."""
    total_move = current_total - opening_total
    juice_move = current_over_odds - opening_over_odds
    
    # Total moved up = sharp over action
    # Total moved down = sharp under action
    if total_move >= 0.5:
        direction = "over"
        is_sharp = True
    elif total_move <= -0.5:
        direction = "under"
        is_sharp = True
    elif abs(juice_move) >= 15:
        # Juice move without total move
        direction = "over" if juice_move > 0 else "under"
        is_sharp = True
    else:
        direction = "none"
        is_sharp = False
    
    return LineMovementAnalysis(
        game_id="",
        movement_type=MovementType.STEAM if is_sharp else MovementType.STABLE,
        direction=direction,
        magnitude=abs(total_move),
        is_sharp_action=is_sharp,
        confidence="medium" if is_sharp else "low",
        recommendation=f"Sharp action on {direction}" if is_sharp else "No clear signal"
    )
```

---

## Phase 2: Storage & Tracking

### Task 2.1: Odds Storage
**File**: `src/utils/odds_storage.py`

```python
"""Store and retrieve historical odds."""
import json
from pathlib import Path
from datetime import datetime, date
from typing import List, Optional

ODDS_DIR = Path("data_files/odds")

def save_odds_snapshot(
    game_id: str,
    home_team: str,
    away_team: str,
    home_ml: int,
    away_ml: int,
    total: float,
    over_odds: int,
    under_odds: int
) -> None:
    """Save current odds snapshot."""
    ODDS_DIR.mkdir(parents=True, exist_ok=True)
    
    file_path = ODDS_DIR / f"{game_id}.json"
    
    # Load existing or create new
    if file_path.exists():
        data = json.loads(file_path.read_text())
    else:
        data = {
            "game_id": game_id,
            "home_team": home_team,
            "away_team": away_team,
            "snapshots": []
        }
    
    # Add new snapshot
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "home_ml": home_ml,
        "away_ml": away_ml,
        "total": total,
        "over_odds": over_odds,
        "under_odds": under_odds
    }
    data["snapshots"].append(snapshot)
    
    file_path.write_text(json.dumps(data, indent=2))

def get_game_odds_history(game_id: str) -> Optional[dict]:
    """Get all odds snapshots for a game."""
    file_path = ODDS_DIR / f"{game_id}.json"
    if file_path.exists():
        return json.loads(file_path.read_text())
    return None

def get_todays_movements() -> List[dict]:
    """Get line movements for today's games."""
    movements = []
    
    for odds_file in ODDS_DIR.glob("*.json"):
        data = json.loads(odds_file.read_text())
        snapshots = data.get("snapshots", [])
        
        if len(snapshots) < 2:
            continue
        
        opening = snapshots[0]
        current = snapshots[-1]
        
        ml_move = current["home_ml"] - opening["home_ml"]
        total_move = current["total"] - opening["total"]
        
        if abs(ml_move) >= 10 or abs(total_move) >= 0.5:
            movements.append({
                "game_id": data["game_id"],
                "matchup": f"{data['away_team']} @ {data['home_team']}",
                "ml_move": ml_move,
                "total_move": total_move,
                "opening_ml": opening["home_ml"],
                "current_ml": current["home_ml"],
                "opening_total": opening["total"],
                "current_total": current["total"]
            })
    
    return movements
```

---

## Phase 3: Streamlit Integration

### Task 3.1: Line Movement Page
**File**: `src/pages/9_📉_Line_Movement.py`

```python
"""Line movement tracking page."""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Line Movement", page_icon="📉", layout="wide")
st.title("📉 Line Movement Tracker")

st.markdown("""
Track line movements to identify sharp action and betting opportunities.
- **Steam moves**: Fast, significant line changes (sharp money)
- **Reverse line**: Movement against public betting
""")

# Today's significant moves
st.subheader("Today's Notable Movements")

# Placeholder data
movements_df = pd.DataFrame({
    "Game": ["TOR @ MTL", "BOS @ NYR", "COL @ VGK"],
    "Open ML": [-140, +120, -150],
    "Current ML": [-165, +105, -145],
    "ML Move": [-25, -15, +5],
    "Open Total": [6.0, 5.5, 6.5],
    "Current Total": [6.5, 5.5, 6.0],
    "Total Move": [0.5, 0.0, -0.5],
    "Signal": ["🔥 Steam Home", "Sharp Away", "⬇️ Sharp Under"]
})

st.dataframe(movements_df, use_container_width=True, hide_index=True)

# Movement visualization
st.subheader("Movement Chart")
game = st.selectbox("Select Game", ["TOR @ MTL", "BOS @ NYR", "COL @ VGK"])

col1, col2 = st.columns(2)
with col1:
    st.markdown("### Moneyline Movement")
    # Placeholder chart
    st.line_chart({"Home ML": [-140, -145, -155, -160, -165]})

with col2:
    st.markdown("### Total Movement")
    st.line_chart({"Total": [6.0, 6.0, 6.0, 6.5, 6.5]})

# Manual odds entry
st.subheader("Record Odds")
with st.form("record_odds"):
    col1, col2, col3 = st.columns(3)
    with col1:
        home_ml = st.number_input("Home ML", value=-150)
        away_ml = st.number_input("Away ML", value=130)
    with col2:
        total = st.number_input("Total", value=6.0, step=0.5)
        over_odds = st.number_input("Over Odds", value=-110)
    with col3:
        under_odds = st.number_input("Under Odds", value=-110)
    
    if st.form_submit_button("Save Snapshot"):
        st.success("Odds snapshot saved!")
```

---

## Integration with Predictions

### Compare Model vs Market
```python
def model_vs_market_edge(
    model_home_prob: float,
    current_home_ml: int,
    opening_home_ml: int
) -> dict:
    """
    Compare model prediction to market movement.
    
    Best signals:
    - Model agrees with line movement direction
    - Model probability exceeds market by 5%+
    """
    from src.utils.odds import american_to_implied
    
    current_implied = american_to_implied(current_home_ml)
    opening_implied = american_to_implied(opening_home_ml)
    
    model_edge = model_home_prob - current_implied
    market_moved_toward = current_implied > opening_implied
    model_agrees = (model_home_prob > 0.5) == market_moved_toward
    
    return {
        "model_prob": round(model_home_prob * 100, 1),
        "market_implied": round(current_implied * 100, 1),
        "edge": round(model_edge * 100, 1),
        "market_direction": "home" if market_moved_toward else "away",
        "model_agrees_with_market": model_agrees,
        "signal_strength": "strong" if model_agrees and model_edge > 0.05 else "weak"
    }
```

---

## Data Sources

### Odds Data Options
Since live odds APIs typically require paid subscriptions:

1. **Manual Entry**: Track odds manually throughout day
2. **Odds API**: Free tier offers limited historical data
3. **Scraping**: Check terms of service first

### Recommended Tracking Schedule
- Opening lines (morning of game)
- Midday check
- 2 hours before game
- 30 minutes before game (steam move detection)

---

## Next Steps
- Integrate with [betting-metrics.md](../features/betting-metrics.md) for value calculations
- Connect to main prediction pipeline in [02-modeling.md](02-modeling.md)
