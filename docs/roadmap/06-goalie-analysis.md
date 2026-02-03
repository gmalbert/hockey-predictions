# Goalie Analysis Roadmap

## Overview
Goalie performance is one of the most impactful factors in NHL betting. A hot goalie can cover poor team defense, while a struggling starter can tank a favorite.

---

## Key Goalie Metrics

### Core Stats
| Metric | Description | Betting Impact |
|--------|-------------|----------------|
| **Save Percentage (SV%)** | Saves / Shots Against | Primary quality indicator |
| **Goals Against Average (GAA)** | Goals per 60 min | Raw performance measure |
| **Quality Start %** | Games with >91.7% SV% | Consistency indicator |
| **High Danger SV%** | SV% on scoring chances | True skill measure |

### Workload Indicators
| Metric | Description | Why It Matters |
|--------|-------------|----------------|
| **Games Started** | Total starts this season | Fatigue tracking |
| **Shots Against/Game** | Defensive burden | Workload context |
| **Days Since Last Start** | Rest indicator | Freshness factor |

---

## Phase 1: Goalie Data Collection

### Task 1.1: Fetch Goalie Stats
**File**: `src/api/goalie_client.py`

```python
"""Goalie-specific API calls."""
import httpx
from typing import Optional
from dataclasses import dataclass

@dataclass
class GoalieStats:
    """Goalie performance data."""
    player_id: int
    name: str
    team: str
    games_played: int
    games_started: int
    wins: int
    losses: int
    ot_losses: int
    save_pct: float
    gaa: float
    shutouts: int
    saves: int
    shots_against: int
    toi: int  # Time on ice in seconds
    
    @property
    def quality_start_estimate(self) -> float:
        """Estimate QS% from save percentage."""
        # Goalies with >0.915 SV% tend to have 60%+ QS rate
        if self.save_pct >= 0.920:
            return 0.70
        elif self.save_pct >= 0.910:
            return 0.55
        elif self.save_pct >= 0.900:
            return 0.40
        else:
            return 0.25

async def fetch_goalie_stats(season: str = "20252026") -> list[GoalieStats]:
    """Fetch all goalie stats for a season."""
    url = "https://api.nhle.com/stats/rest/en/goalie/summary"
    params = {
        "cayenneExp": f"seasonId={season}",
        "sort": "wins",
        "direction": "DESC"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        data = response.json()
    
    goalies = []
    for g in data.get("data", []):
        goalies.append(GoalieStats(
            player_id=g.get("playerId", 0),
            name=g.get("goalieFullName", ""),
            team=g.get("teamAbbrevs", ""),
            games_played=g.get("gamesPlayed", 0),
            games_started=g.get("gamesStarted", 0),
            wins=g.get("wins", 0),
            losses=g.get("losses", 0),
            ot_losses=g.get("otLosses", 0),
            save_pct=g.get("savePct", 0.0),
            gaa=g.get("goalsAgainstAverage", 0.0),
            shutouts=g.get("shutouts", 0),
            saves=g.get("saves", 0),
            shots_against=g.get("shotsAgainst", 0),
            toi=g.get("timeOnIce", 0)
        ))
    
    return goalies
```

### Task 1.2: Goalie Starter Detection
**File**: `src/utils/goalie_starter.py`

```python
"""Detect probable starting goalie."""
from datetime import date, timedelta
from typing import Optional

def get_probable_starter(
    team: str,
    game_date: date,
    team_goalies: list,
    recent_games: list
) -> Optional[dict]:
    """
    Determine probable starting goalie.
    
    Logic:
    1. Check if team has announced starter
    2. Look at recent start pattern
    3. Consider back-to-back situations
    """
    if not team_goalies:
        return None
    
    # Sort by games started (most = starter)
    sorted_goalies = sorted(
        team_goalies, 
        key=lambda g: g.get("games_started", 0), 
        reverse=True
    )
    
    starter = sorted_goalies[0]
    backup = sorted_goalies[1] if len(sorted_goalies) > 1 else None
    
    # Check for back-to-back
    yesterday = game_date - timedelta(days=1)
    played_yesterday = any(
        g.get("date") == yesterday.isoformat() 
        for g in recent_games
    )
    
    if played_yesterday and backup:
        # Back-to-back often means backup starts
        return {
            "probable_starter": backup,
            "confidence": "low",
            "reason": "Back-to-back situation"
        }
    
    return {
        "probable_starter": starter,
        "confidence": "medium",
        "reason": "Based on season starts"
    }
```

---

## Phase 2: Goalie Impact Model

### Task 2.1: Goals Adjustment
Adjust expected goals based on goalie quality.

**File**: `src/models/goalie_adjustment.py`

```python
"""Adjust predictions based on goalie matchup."""
from dataclasses import dataclass

LEAGUE_AVG_SAVE_PCT = 0.905

@dataclass
class GoalieAdjustment:
    """Adjustment to opponent's expected goals."""
    goalie_name: str
    save_pct: float
    adjustment: float  # Negative = fewer goals expected
    confidence: str

def calculate_goalie_adjustment(
    goalie_save_pct: float,
    sample_size: int
) -> GoalieAdjustment:
    """
    Calculate goal adjustment based on goalie vs league average.
    
    Each 1% above/below average SV% ≈ 0.3 goals difference
    """
    diff_from_avg = goalie_save_pct - LEAGUE_AVG_SAVE_PCT
    
    # Base adjustment: 30 shots/game * SV% difference
    base_adjustment = -diff_from_avg * 30
    
    # Reduce confidence for small sample sizes
    if sample_size < 10:
        confidence = "low"
        adjustment = base_adjustment * 0.5  # Regress heavily
    elif sample_size < 20:
        confidence = "medium"
        adjustment = base_adjustment * 0.75
    else:
        confidence = "high"
        adjustment = base_adjustment
    
    return GoalieAdjustment(
        goalie_name="",  # Fill in caller
        save_pct=goalie_save_pct,
        adjustment=round(adjustment, 2),
        confidence=confidence
    )

def adjusted_xg_for_matchup(
    base_team_xg: float,
    opposing_goalie_sv_pct: float,
    opposing_goalie_games: int
) -> float:
    """
    Adjust a team's expected goals based on opposing goalie.
    
    Example:
        Team xG: 3.2
        Opposing goalie: 0.925 SV% (elite)
        Adjustment: -0.6 goals
        Adjusted xG: 2.6
    """
    adj = calculate_goalie_adjustment(opposing_goalie_sv_pct, opposing_goalie_games)
    return round(base_team_xg + adj.adjustment, 2)
```

### Task 2.2: Goalie Matchup Score
**File**: `src/models/goalie_matchup.py`

```python
"""Compare goalie matchups for betting edge."""
from dataclasses import dataclass
from typing import Tuple

@dataclass
class MatchupEdge:
    """Goalie matchup comparison."""
    home_goalie: str
    away_goalie: str
    home_sv_pct: float
    away_sv_pct: float
    edge_team: str  # Which team has goalie advantage
    edge_magnitude: float  # Expected goal difference from goalies

def compare_goalie_matchup(
    home_goalie_sv_pct: float,
    away_goalie_sv_pct: float,
    home_goalie_name: str = "Home",
    away_goalie_name: str = "Away"
) -> MatchupEdge:
    """
    Compare goalie quality and determine edge.
    
    Returns which team benefits from goalie matchup.
    """
    # Calculate expected goals saved above average for each
    home_goals_saved = (home_goalie_sv_pct - 0.905) * 30  # vs 30 shots
    away_goals_saved = (away_goalie_sv_pct - 0.905) * 30
    
    # Net edge (positive = home advantage)
    net_edge = home_goals_saved - away_goals_saved
    
    if abs(net_edge) < 0.1:
        edge_team = "Even"
    elif net_edge > 0:
        edge_team = "Home"
    else:
        edge_team = "Away"
    
    return MatchupEdge(
        home_goalie=home_goalie_name,
        away_goalie=away_goalie_name,
        home_sv_pct=home_goalie_sv_pct,
        away_sv_pct=away_goalie_sv_pct,
        edge_team=edge_team,
        edge_magnitude=abs(round(net_edge, 2))
    )
```

---

## Phase 3: Goalie Trends

### Recent Form Analysis
Track goalie performance over last 5-10 starts.

```python
def goalie_recent_form(game_log: list, n_games: int = 5) -> dict:
    """Analyze goalie's recent form."""
    recent = game_log[-n_games:] if len(game_log) >= n_games else game_log
    
    if not recent:
        return {"games": 0, "recent_sv_pct": None}
    
    total_saves = sum(g.get("saves", 0) for g in recent)
    total_shots = sum(g.get("shots_against", 0) for g in recent)
    
    recent_sv_pct = total_saves / total_shots if total_shots > 0 else 0
    
    return {
        "games": len(recent),
        "recent_sv_pct": round(recent_sv_pct, 3),
        "recent_gaa": sum(g.get("goals_against", 0) for g in recent) / len(recent),
        "wins": sum(1 for g in recent if g.get("decision") == "W"),
        "quality_starts": sum(
            1 for g in recent 
            if g.get("saves", 0) / max(g.get("shots_against", 1), 1) > 0.917
        )
    }
```

---

## Streamlit Page

### Task 3.1: Goalie Dashboard
**File**: `src/pages/7_🥅_Goalies.py`

```python
"""Goalie analysis page."""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Goalie Analysis", page_icon="🥅", layout="wide")
st.title("🥅 Goalie Analysis")

# Goalie comparison tool
st.subheader("Goalie Matchup Comparison")

col1, col2 = st.columns(2)
with col1:
    st.markdown("### Home Goalie")
    home_sv_pct = st.slider("Save %", 0.880, 0.940, 0.910, 0.001, key="home")
    st.metric("Expected Goals Saved", f"{(home_sv_pct - 0.905) * 30:+.2f}")

with col2:
    st.markdown("### Away Goalie")
    away_sv_pct = st.slider("Save %", 0.880, 0.940, 0.910, 0.001, key="away")
    st.metric("Expected Goals Saved", f"{(away_sv_pct - 0.905) * 30:+.2f}")

# Edge calculation
edge = (home_sv_pct - away_sv_pct) * 30
if abs(edge) < 0.1:
    st.info("**Matchup is even** - no significant goalie edge")
elif edge > 0:
    st.success(f"**Home goalie edge**: {edge:.2f} expected goals advantage")
else:
    st.warning(f"**Away goalie edge**: {abs(edge):.2f} expected goals advantage")

# League goalie rankings
st.subheader("League Goalie Rankings")
# TODO: Pull from API
```

---

## Next Steps
- Integrate with [02-modeling.md](02-modeling.md) for prediction adjustments
- See [06-injury-tracking.md](06-injury-tracking.md) for injury impact on goalies
