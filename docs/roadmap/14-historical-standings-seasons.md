# 14 — Historical Standings, Seasons Metadata & Dynamic Team IDs

## Status: Proposed

## Overview

Three related "infrastructure" endpoints that improve our platform's foundations:
1. **Seasons Metadata** — Programmatic season ID discovery (currently hardcoded)
2. **Historical Standings by Date** — Standings snapshots for any date (trend analysis)
3. **Team Metadata** — Full team list from the API (replace hardcoded TEAM_ID_MAP)

### Endpoints

| Endpoint | URL Pattern | Description |
|----------|-------------|-------------|
| **Seasons Metadata** | `GET /v1/standings-season` | List of all seasons with date ranges |
| **Historical Standings** | `GET /v1/standings/{date}` | Standings as of a specific date |
| **Team Metadata** | `GET /stats/rest/en/team` | Full team list with IDs |

### Sample URLs

- `https://api-web.nhle.com/v1/standings-season`
- `https://api-web.nhle.com/v1/standings/2026-01-15`
- `https://api.nhle.com/stats/rest/en/team`

---

## What Data Is Available

### 1. Seasons Metadata

Returns all NHL seasons with their ID and start/end dates:

```json
{
  "seasons": [
    {
      "id": 20252026,
      "conferencesInUse": 1,
      "divisionsInUse": 1,
      "pointForOTlossInUse": 1,
      "regulationWinsInUse": 1,
      "rowInUse": 1,
      "standingsEnd": "2026-04-17",
      "standingsStart": "2025-10-04",
      "tiesInUse": 0,
      "wildcardInUse": 1
    },
    {
      "id": 20242025,
      "standingsEnd": "2025-04-17",
      "standingsStart": "2024-10-04"
    }
  ]
}
```

**Current problem**: Our codebase hardcodes the season string `"20252026"` in multiple places. This endpoint lets us discover the current season dynamically.

### 2. Historical Standings by Date

Returns full standings as of any date, identical format to `/v1/standings/now`:

```json
{
  "standings": [
    {
      "teamAbbrev": {"default": "WPG"},
      "teamName": {"default": "Winnipeg Jets"},
      "conferenceName": "Western",
      "divisionName": "Central",
      "gamesPlayed": 50,
      "wins": 35,
      "losses": 12,
      "otLosses": 3,
      "points": 73,
      "pointPctg": 0.730,
      "regulationWins": 28,
      "goalFor": 185,
      "goalAgainst": 128,
      "goalDifferential": 57,
      "streakCode": "W",
      "streakCount": 4,
      "l10Wins": 7,
      "l10Losses": 2,
      "l10OtLosses": 1,
      "homeWins": 20,
      "homeLosses": 4,
      "roadWins": 15,
      "roadLosses": 8
    }
  ]
}
```

### 3. Team Metadata

Complete team list with IDs, triCodes, and franchise info:

```json
{
  "data": [
    {
      "id": 1,
      "franchiseId": 23,
      "fullName": "New Jersey Devils",
      "leagueId": 133,
      "rawTricode": "NJD",
      "triCode": "NJD"
    },
    {
      "id": 55,
      "franchiseId": 40,
      "fullName": "Seattle Kraken",
      "rawTricode": "SEA",
      "triCode": "SEA"
    }
  ],
  "total": 32
}
```

**Current problem**: `NHLClient.TEAM_ID_MAP` and `ID_TO_TEAM_MAP` are hardcoded with 31 entries. This endpoint provides the authoritative mapping.

---

## Value for Our Platform

### 1. Eliminate Hardcoded Season IDs

Several places in the codebase pass `"20252026"` as a season string. With the seasons metadata endpoint, we can auto-detect the current season based on today's date.

### 2. Standings Trend Analysis

Track how teams' records have evolved over time:
- **Momentum tracking**: Team on a winning streak? Falling off?
- **Standings change**: Team rising or falling in playoff race
- **Mid-season vs. current**: Compare January form to February

This directly supports better predictions — recent form is a stronger predictor than full-season record.

### 3. Dynamic Team Metadata

- Always have the correct team list (no more missed expansions)
- Franchise IDs for linking to historical franchise data
- Validate our hardcoded maps are complete and correct

### 4. Backtesting Validation

Historical standings let us verify our model predictions against actual results over time periods.

---

## Implementation

### Phase 1: Season Discovery

```python
# src/api/nhl_client.py — add to NHLClient class

from datetime import date

def get_seasons(self) -> list[dict]:
    """
    Get all NHL seasons with their date ranges.

    Returns:
        List of season dicts with ids and date ranges.
        Most recent season first.
    """
    url = f"{self.BASE_WEB_API}/standings-season"
    data = self._fetch_sync(url, ttl=86400)  # Cache for 24 hours
    seasons = data.get("seasons", [])
    return sorted(seasons, key=lambda s: s["id"], reverse=True)

def get_current_season_id(self) -> int:
    """
    Determine the current NHL season ID based on today's date.

    Returns:
        Season ID (e.g., 20252026). Falls back to latest if no match.
    """
    seasons = self.get_seasons()
    today = date.today().isoformat()

    for season in seasons:
        start = season.get("standingsStart", "")
        end = season.get("standingsEnd", "")
        if start <= today <= end:
            return season["id"]

    # Offseason: return the most recent season
    return seasons[0]["id"] if seasons else 20252026

def get_current_season_str(self) -> str:
    """
    Get current season as a string (e.g., '20252026').
    Convenience wrapper for use in API calls.
    """
    return str(self.get_current_season_id())
```

### Phase 2: Historical Standings

```python
# src/api/nhl_client.py — add to NHLClient class

def get_standings_by_date(self, standings_date: str) -> list[dict]:
    """
    Get NHL standings as of a specific date.

    Args:
        standings_date: Date string in YYYY-MM-DD format

    Returns:
        List of team standings records
    """
    url = f"{self.BASE_WEB_API}/standings/{standings_date}"
    data = self._fetch_sync(url, ttl=86400)  # Historical data doesn't change
    return data.get("standings", [])
```

```python
# src/utils/standings_trends.py — Standings trend analysis

import pandas as pd
from datetime import date, timedelta
from src.api.nhl_client import NHLClient


def get_standings_trend(
    client: NHLClient,
    team_abbrev: str,
    days_back: int = 30,
    sample_interval: int = 7,
) -> pd.DataFrame:
    """
    Get standings trend for a team over a time period.

    Samples standings at regular intervals to show trajectory.

    Args:
        client: NHLClient instance
        team_abbrev: Team abbreviation (e.g., "WPG")
        days_back: How many days back to look
        sample_interval: Days between samples

    Returns:
        DataFrame with date, points, wins, losses, goal_diff columns
    """
    today = date.today()
    records = []

    for days_ago in range(days_back, -1, -sample_interval):
        sample_date = today - timedelta(days=days_ago)
        standings = client.get_standings_by_date(sample_date.isoformat())

        for team in standings:
            if team.get("teamAbbrev", {}).get("default") == team_abbrev:
                records.append({
                    "date": sample_date.isoformat(),
                    "points": team.get("points", 0),
                    "wins": team.get("wins", 0),
                    "losses": team.get("losses", 0),
                    "ot_losses": team.get("otLosses", 0),
                    "games_played": team.get("gamesPlayed", 0),
                    "point_pct": team.get("pointPctg", 0),
                    "goal_diff": team.get("goalDifferential", 0),
                    "streak": f"{team.get('streakCode', '')}{team.get('streakCount', '')}",
                    "l10_wins": team.get("l10Wins", 0),
                })
                break

    return pd.DataFrame(records)


def compare_team_trajectories(
    client: NHLClient,
    teams: list[str],
    days_back: int = 60,
    sample_interval: int = 7,
) -> pd.DataFrame:
    """
    Compare standings trajectories for multiple teams.

    Useful for divisional races or matchup context.

    Args:
        client: NHLClient instance
        teams: List of team abbreviations
        days_back: How many days back
        sample_interval: Days between samples

    Returns:
        DataFrame with team, date, and standings columns
    """
    all_records = []

    today = date.today()
    for days_ago in range(days_back, -1, -sample_interval):
        sample_date = today - timedelta(days=days_ago)
        standings = client.get_standings_by_date(sample_date.isoformat())

        for team in standings:
            abbrev = team.get("teamAbbrev", {}).get("default", "")
            if abbrev in teams:
                all_records.append({
                    "team": abbrev,
                    "date": sample_date.isoformat(),
                    "points": team.get("points", 0),
                    "point_pct": team.get("pointPctg", 0),
                    "games_played": team.get("gamesPlayed", 0),
                })

    return pd.DataFrame(all_records)
```

### Phase 3: Dynamic Team Metadata

```python
# src/api/nhl_client.py — add to NHLClient class

def get_team_metadata(self) -> list[dict]:
    """
    Get the official list of all NHL teams from the stats API.

    Returns:
        List of team dicts with id, fullName, and triCode
    """
    url = f"{self.BASE_STATS_API}/team"
    data = self._fetch_sync(url, ttl=86400)  # Rarely changes
    return data.get("data", [])

def build_team_maps(self) -> tuple[dict[str, int], dict[int, str]]:
    """
    Build team abbreviation/ID maps from the API.

    Returns:
        Tuple of (abbrev_to_id, id_to_abbrev) dicts
    """
    teams = self.get_team_metadata()
    abbrev_to_id = {t["triCode"]: t["id"] for t in teams}
    id_to_abbrev = {t["id"]: t["triCode"] for t in teams}
    return abbrev_to_id, id_to_abbrev
```

#### Validating Existing Maps

Before replacing hardcoded maps, run a validation:

```python
# validate_team_maps.py — One-time validation script

from src.api.nhl_client import NHLClient


def validate_team_maps() -> None:
    """Compare hardcoded team maps against the API."""
    client = NHLClient()
    api_teams = client.get_team_metadata()

    api_map = {t["triCode"]: t["id"] for t in api_teams}
    hardcoded = client.TEAM_ID_MAP

    # Check for teams in API but not in our map
    for code, tid in api_map.items():
        if code not in hardcoded:
            print(f"  MISSING from hardcoded: {code} (id={tid})")
        elif hardcoded[code] != tid:
            print(f"  MISMATCH: {code} — hardcoded={hardcoded[code]}, API={tid}")

    # Check for teams in our map but not in API
    for code in hardcoded:
        if code not in api_map:
            print(f"  EXTRA in hardcoded (not in API): {code}")

    print(f"\nAPI teams: {len(api_map)}, Hardcoded: {len(hardcoded)}")


if __name__ == "__main__":
    validate_team_maps()
```

### Phase 4: Standings Visualization (Streamlit)

```python
# Enhancement for pages/3_🏆_Standings.py
# Add a standings trend chart

import streamlit as st
import altair as alt
from src.utils.standings_trends import get_standings_trend, compare_team_trajectories


def render_standings_trend(client, team_abbrev: str) -> None:
    """Show a team's points trajectory over the last 60 days."""
    df = get_standings_trend(client, team_abbrev, days_back=60, sample_interval=7)
    if df.empty:
        return

    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("points:Q", title="Points"),
            tooltip=["date", "points", "games_played", "streak", "l10_wins"],
        )
        .properties(width=600, height=300, title=f"{team_abbrev} Points Trajectory")
    )
    st.altair_chart(chart, use_container_width=True)


def render_division_race(client, teams: list[str]) -> None:
    """Show point pct comparison for teams in a division/race."""
    df = compare_team_trajectories(client, teams, days_back=60)
    if df.empty:
        return

    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("point_pct:Q", title="Point %", scale=alt.Scale(zero=False)),
            color=alt.Color("team:N", legend=alt.Legend(title="Team")),
            tooltip=["team", "date", "points", "point_pct"],
        )
        .properties(width=600, height=300, title="Division Race")
    )
    st.altair_chart(chart, use_container_width=True)
```

### Phase 5: Replace Hardcoded Season References

Once `get_current_season_str()` is implemented, update all hardcoded season references:

```python
# BEFORE (multiple files):
schedule = client.get_team_schedule("TOR", "20252026")

# AFTER:
season = client.get_current_season_str()
schedule = client.get_team_schedule("TOR", season)
```

Key files to update:
- `predictions.py`
- `pages/1_📅_Todays_Games.py`
- `pages/10_📊_Model_Performance.py`
- `pages/11_🔬_Backtesting.py`
- `retrain_model.py`
- `auto_fetch_games.py`

---

## API Rate Considerations

- **Seasons metadata**: Very small response, cache for 24 hours
- **Historical standings**: ~40 KB per response, cache for 24 hours (data never changes)
- **Team metadata**: Small response (~5 KB), cache for 24 hours
- When fetching standings trend (e.g., 60 days at 7-day intervals = 9 requests), the long cache TTL means these only hit the API once

---

## Dependencies

- No new packages required
- `pandas` and `altair` (both already available)
- Independent of other roadmap items — can be implemented first as a quick infrastructure win
