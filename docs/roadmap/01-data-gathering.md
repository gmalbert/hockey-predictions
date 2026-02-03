# Data Gathering Roadmap

## Overview
This document outlines the strategy for collecting NHL data from unofficial APIs to power betting analytics.

---

## Phase 1: Core API Client Setup

### Task 1.1: Create Base HTTP Client
**File**: `src/api/nhl_client.py`

```python
"""NHL API client with caching and error handling."""
import httpx
from pathlib import Path
from datetime import datetime, timedelta
import json
from typing import Any

class NHLClient:
    """Async client for NHL API endpoints."""
    
    BASE_WEB_API = "https://api-web.nhle.com/v1"
    BASE_STATS_API = "https://api.nhle.com/stats/rest/en"
    CACHE_DIR = Path("data_files/cache")
    
    def __init__(self, cache_ttl_minutes: int = 5):
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, endpoint: str) -> Path:
        """Generate cache file path from endpoint."""
        safe_name = endpoint.replace("/", "_").replace("?", "_")
        return self.CACHE_DIR / f"{safe_name}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cached data is still fresh."""
        if not cache_path.exists():
            return False
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - mtime < self.cache_ttl
    
    async def _fetch(self, base_url: str, endpoint: str) -> dict[str, Any]:
        """Fetch data with caching."""
        cache_path = self._get_cache_path(endpoint)
        
        if self._is_cache_valid(cache_path):
            return json.loads(cache_path.read_text())
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{base_url}{endpoint}")
            response.raise_for_status()
            data = response.json()
            
            cache_path.write_text(json.dumps(data, indent=2))
            return data
    
    async def get_schedule(self, date: str) -> dict:
        """Get games for a specific date (YYYY-MM-DD)."""
        return await self._fetch(self.BASE_WEB_API, f"/schedule/{date}")
    
    async def get_standings(self) -> dict:
        """Get current league standings."""
        return await self._fetch(self.BASE_WEB_API, "/standings/now")
    
    async def get_team_stats(self, season: str = "20252026") -> dict:
        """Get team statistics for a season."""
        endpoint = f"/team/summary?cayenneExp=seasonId={season}"
        return await self._fetch(self.BASE_STATS_API, endpoint)
```

### Task 1.2: Create Synchronous Wrapper for Streamlit
**File**: `src/api/sync_client.py`

```python
"""Synchronous wrapper for Streamlit compatibility."""
import asyncio
from functools import wraps
from typing import Callable, Any

def run_async(func: Callable) -> Callable:
    """Decorator to run async functions synchronously."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        return asyncio.run(func(*args, **kwargs))
    return wrapper

# Usage in Streamlit:
# from src.api.nhl_client import NHLClient
# from src.api.sync_client import run_async
#
# client = NHLClient()
# schedule = run_async(client.get_schedule)("2026-02-02")
```

---

## Phase 2: Essential Data Endpoints

### Task 2.1: Today's Schedule
Fetches all games for betting analysis.

```python
async def get_todays_games(self) -> list[dict]:
    """Get today's games with betting-relevant data."""
    from datetime import date
    today = date.today().isoformat()
    schedule = await self.get_schedule(today)
    
    games = []
    for game_week in schedule.get("gameWeek", []):
        for game in game_week.get("games", []):
            games.append({
                "game_id": game["id"],
                "start_time": game["startTimeUTC"],
                "home_team": game["homeTeam"]["abbrev"],
                "away_team": game["awayTeam"]["abbrev"],
                "venue": game.get("venue", {}).get("default", ""),
                "game_type": game.get("gameType", 2),  # 2 = regular season
            })
    return games
```

### Task 2.2: Team Statistics
Key metrics for moneyline and puck line analysis.

```python
async def get_team_summary(self, team_abbrev: str) -> dict:
    """Get comprehensive team stats."""
    stats = await self.get_team_stats()
    
    for team in stats.get("data", []):
        if team.get("teamAbbrev") == team_abbrev:
            return {
                "wins": team.get("wins", 0),
                "losses": team.get("losses", 0),
                "ot_losses": team.get("otLosses", 0),
                "goals_for_pg": team.get("goalsForPerGame", 0),
                "goals_against_pg": team.get("goalsAgainstPerGame", 0),
                "pp_pct": team.get("powerPlayPct", 0),
                "pk_pct": team.get("penaltyKillPct", 0),
                "shots_for_pg": team.get("shotsForPerGame", 0),
                "shots_against_pg": team.get("shotsAgainstPerGame", 0),
            }
    return {}
```

### Task 2.3: Player Statistics (for Props)
Individual player data for prop bets.

```python
async def get_skater_stats(self, season: str = "20252026", limit: int = 100) -> list[dict]:
    """Get top skaters by points."""
    endpoint = f"/skater/summary?limit={limit}&cayenneExp=seasonId={season}&sort=points&direction=DESC"
    data = await self._fetch(self.BASE_STATS_API, endpoint)
    
    return [
        {
            "player_id": p.get("playerId"),
            "name": p.get("skaterFullName"),
            "team": p.get("teamAbbrevs"),
            "games": p.get("gamesPlayed", 0),
            "goals": p.get("goals", 0),
            "assists": p.get("assists", 0),
            "points": p.get("points", 0),
            "shots": p.get("shots", 0),
            "toi_pg": p.get("timeOnIcePerGame", 0),
        }
        for p in data.get("data", [])
    ]
```

---

## Phase 3: Historical Data Collection

### Task 3.1: Game Results History
Store historical outcomes for backtesting.

```python
async def get_season_games(self, team_abbrev: str, season: str = "20252026") -> list[dict]:
    """Get all games for a team in a season."""
    endpoint = f"/club-schedule-season/{team_abbrev}/{season}"
    data = await self._fetch(self.BASE_WEB_API, endpoint)
    
    completed = []
    for game in data.get("games", []):
        if game.get("gameState") == "OFF":  # Completed games only
            completed.append({
                "game_id": game["id"],
                "date": game["gameDate"],
                "opponent": game["opponentAbbrev"]["default"],
                "home_away": "home" if game["homeTeam"]["abbrev"] == team_abbrev else "away",
                "team_score": game.get("teamScore", 0),
                "opponent_score": game.get("opponentScore", 0),
                "result": "W" if game.get("teamScore", 0) > game.get("opponentScore", 0) else "L",
            })
    return completed
```

### Task 3.2: Cache Management Utility
**File**: `src/utils/cache.py`

```python
"""Cache management utilities."""
from pathlib import Path
from datetime import datetime, timedelta
import json

CACHE_DIR = Path("data_files/cache")

def clear_old_cache(max_age_hours: int = 24) -> int:
    """Remove cache files older than specified hours."""
    if not CACHE_DIR.exists():
        return 0
    
    removed = 0
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    
    for cache_file in CACHE_DIR.glob("*.json"):
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if mtime < cutoff:
            cache_file.unlink()
            removed += 1
    
    return removed

def get_cache_size_mb() -> float:
    """Get total cache size in megabytes."""
    if not CACHE_DIR.exists():
        return 0.0
    
    total_bytes = sum(f.stat().st_size for f in CACHE_DIR.glob("*.json"))
    return total_bytes / (1024 * 1024)
```

---

## Next Steps
- See [02-modeling.md](02-modeling.md) for prediction model development
- See [nhl-api-reference.md](../api/nhl-api-reference.md) for complete endpoint documentation
