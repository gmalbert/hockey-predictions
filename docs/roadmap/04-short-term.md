# Short-Term Roadmap (MVP)

## Overview
Tasks to get a working MVP within 2-4 weeks. Focus on core functionality that provides immediate value.

---

## Week 1: Foundation

### ✅ Task 1: Project Setup
- [x] Create virtual environment (Python 3.13)
- [x] Create README with project overview
- [x] Set up docs folder structure
- [ ] Create `requirements.txt`

**File**: `requirements.txt`
```
streamlit>=1.30.0
httpx>=0.26.0
pandas>=2.1.0
plotly>=5.18.0
python-dateutil>=2.8.0
```

**Command**:
```powershell
pip install streamlit httpx pandas plotly python-dateutil
pip freeze > requirements.txt
```

### ✅ Task 2: Basic App Structure
Create the Streamlit app skeleton.

```powershell
mkdir src
mkdir src/api
mkdir src/models
mkdir src/utils
mkdir src/pages
```

**Files to create**:
- `src/app.py` - Main entry point
- `src/__init__.py` - Package marker
- `src/api/__init__.py`
- `src/models/__init__.py`
- `src/utils/__init__.py`

---

## Week 2: Data Layer

### Task 3: NHL API Client
Implement the base API client from [01-data-gathering.md](01-data-gathering.md).

**Priority endpoints**:
1. `/schedule/{date}` - Today's games
2. `/standings/now` - Current standings
3. `/team/summary` - Team statistics

**File**: `src/api/nhl_client.py`
```python
"""NHL API Client - See 01-data-gathering.md for full implementation."""
import httpx
from pathlib import Path
import json
from datetime import datetime, timedelta
from typing import Any

class NHLClient:
    BASE_WEB_API = "https://api-web.nhle.com/v1"
    BASE_STATS_API = "https://api.nhle.com/stats/rest/en"
    CACHE_DIR = Path("data_files/cache")
    
    def __init__(self, cache_ttl_minutes: int = 5):
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def get_schedule(self, date: str) -> dict:
        """Get games for a date (YYYY-MM-DD)."""
        return self._fetch_sync(f"{self.BASE_WEB_API}/schedule/{date}")
    
    def get_standings(self) -> dict:
        """Get current standings."""
        return self._fetch_sync(f"{self.BASE_WEB_API}/standings/now")
    
    def _fetch_sync(self, url: str) -> dict[str, Any]:
        """Synchronous fetch with caching."""
        cache_path = self._get_cache_path(url)
        
        if self._is_cache_valid(cache_path):
            return json.loads(cache_path.read_text())
        
        response = httpx.get(url, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        
        cache_path.write_text(json.dumps(data, indent=2))
        return data
    
    def _get_cache_path(self, url: str) -> Path:
        safe_name = url.replace("/", "_").replace(":", "_").replace("?", "_")
        return self.CACHE_DIR / f"{safe_name[-100:]}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        if not cache_path.exists():
            return False
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - mtime < self.cache_ttl
```

### Task 4: Data Transformers
Convert raw API responses to pandas DataFrames.

**File**: `src/utils/transformers.py`
```python
"""Transform API responses to DataFrames."""
import pandas as pd
from typing import Any

def schedule_to_df(schedule_data: dict) -> pd.DataFrame:
    """Convert schedule API response to DataFrame."""
    games = []
    
    for game_day in schedule_data.get("gameWeek", []):
        for game in game_day.get("games", []):
            games.append({
                "game_id": game["id"],
                "date": game_day.get("date"),
                "start_time": game.get("startTimeUTC"),
                "home_team": game["homeTeam"]["abbrev"],
                "away_team": game["awayTeam"]["abbrev"],
                "home_score": game.get("homeTeam", {}).get("score"),
                "away_score": game.get("awayTeam", {}).get("score"),
                "game_state": game.get("gameState"),
                "venue": game.get("venue", {}).get("default", ""),
            })
    
    return pd.DataFrame(games)

def standings_to_df(standings_data: dict) -> pd.DataFrame:
    """Convert standings API response to DataFrame."""
    teams = []
    
    for team in standings_data.get("standings", []):
        teams.append({
            "team": team.get("teamAbbrev", {}).get("default"),
            "team_name": team.get("teamName", {}).get("default"),
            "division": team.get("divisionName"),
            "conference": team.get("conferenceName"),
            "games_played": team.get("gamesPlayed", 0),
            "wins": team.get("wins", 0),
            "losses": team.get("losses", 0),
            "ot_losses": team.get("otLosses", 0),
            "points": team.get("points", 0),
            "goals_for": team.get("goalFor", 0),
            "goals_against": team.get("goalAgainst", 0),
            "goal_diff": team.get("goalDifferential", 0),
            "streak": team.get("streakCode"),
            "l10_wins": team.get("l10Wins", 0),
            "l10_losses": team.get("l10Losses", 0),
            "l10_ot": team.get("l10OtLosses", 0),
        })
    
    return pd.DataFrame(teams)
```

---

## Week 3: Core UI

### Task 5: Today's Games Page
Implement the games dashboard with real API data.

**File**: `src/pages/1_📅_Todays_Games.py`
```python
"""Today's games dashboard."""
import streamlit as st
from datetime import date
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.nhl_client import NHLClient
from utils.transformers import schedule_to_df

st.set_page_config(page_title="Today's Games", page_icon="📅", layout="wide")

@st.cache_data(ttl=300)  # 5 minute cache
def get_games(date_str: str):
    client = NHLClient()
    data = client.get_schedule(date_str)
    return schedule_to_df(data)

st.title("📅 Today's Games")

selected_date = st.date_input("Select Date", value=date.today())
date_str = selected_date.strftime("%Y-%m-%d")

try:
    games_df = get_games(date_str)
    
    if games_df.empty:
        st.info(f"No games scheduled for {date_str}")
    else:
        # Display games
        for _, game in games_df.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 2])
                with col1:
                    st.markdown(f"### {game['away_team']}")
                with col2:
                    st.markdown("**@**")
                with col3:
                    st.markdown(f"### {game['home_team']}")
                st.divider()
                
except Exception as e:
    st.error(f"Error loading games: {e}")
```

### Task 6: Standings Page
Display current NHL standings.

**File**: `src/pages/2_🏆_Standings.py`
```python
"""NHL Standings page."""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.nhl_client import NHLClient
from utils.transformers import standings_to_df

st.set_page_config(page_title="Standings", page_icon="🏆", layout="wide")

@st.cache_data(ttl=300)
def get_standings():
    client = NHLClient()
    data = client.get_standings()
    return standings_to_df(data)

st.title("🏆 NHL Standings")

try:
    standings = get_standings()
    
    # Group by division
    divisions = standings["division"].unique()
    
    tabs = st.tabs(list(divisions))
    for tab, div in zip(tabs, divisions):
        with tab:
            div_standings = standings[standings["division"] == div].sort_values(
                "points", ascending=False
            )
            st.dataframe(
                div_standings[["team", "games_played", "wins", "losses", 
                              "ot_losses", "points", "goal_diff", "streak"]],
                use_container_width=True,
                hide_index=True
            )

except Exception as e:
    st.error(f"Error loading standings: {e}")
```

---

## Week 4: Basic Predictions

### Task 7: Simple Prediction Model
Implement basic xG and win probability from [02-modeling.md](02-modeling.md).

### Task 8: Value Identification
- Calculate implied probability from odds
- Compare to model predictions
- Highlight edges > 2%

### Task 9: Testing
**File**: `tests/test_api.py`
```python
"""Tests for NHL API client."""
import pytest
from src.api.nhl_client import NHLClient

def test_client_initialization():
    client = NHLClient()
    assert client.CACHE_DIR.exists()

def test_schedule_fetch():
    client = NHLClient()
    # Use a known date with games
    data = client.get_schedule("2026-01-15")
    assert "gameWeek" in data

def test_standings_fetch():
    client = NHLClient()
    data = client.get_standings()
    assert "standings" in data
```

**Run tests**:
```powershell
pip install pytest
pytest tests/ -v
```

---

## MVP Checklist

| Feature | Status | File |
|---------|--------|------|
| Project structure | ✅ | Multiple |
| NHL API client | 🔲 | `src/api/nhl_client.py` |
| Today's games page | 🔲 | `src/pages/1_*.py` |
| Standings page | 🔲 | `src/pages/2_*.py` |
| Basic xG model | 🔲 | `src/models/expected_goals.py` |
| Win probability | 🔲 | `src/models/win_probability.py` |
| Value finder | 🔲 | `src/pages/4_*.py` |
| Basic tests | 🔲 | `tests/` |

---

## Launch Command
```powershell
streamlit run src/app.py
```

---

## Next Steps
After MVP, see [05-long-term.md](05-long-term.md) for advanced features.
