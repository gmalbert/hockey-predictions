# 13 — Player Profiles & Recent Form

## Status: Proposed

## Overview

The NHL Player Landing endpoint provides **complete player profiles** — biography, career stats, season-by-season breakdowns, last 5 game logs, and awards. This data enables richer player prop analysis, form-based adjustments, and biographical context missing from our current skater/goalie stats.

### Endpoint

| Endpoint | URL Pattern | Description |
|----------|-------------|-------------|
| **Player Landing** | `GET /v1/player/{playerId}/landing` | Full player profile |

### Sample URL

`https://api-web.nhle.com/v1/player/8478402/landing` (Connor McDavid)

---

## What Data Is Available

### Player Biography

```json
{
  "playerId": 8478402,
  "isActive": true,
  "firstName": {"default": "Connor"},
  "lastName": {"default": "McDavid"},
  "position": "C",
  "sweaterNumber": 97,
  "heightInInches": 73,
  "weightInPounds": 194,
  "birthDate": "1997-01-13",
  "birthCity": {"default": "Richmond Hill"},
  "birthStateProvince": {"default": "Ontario"},
  "birthCountry": "CAN",
  "shootsCatches": "L",
  "draftDetails": {"year": 2015, "teamAbbrev": "EDM", "round": 1, "pickInRound": 1, "overallPick": 1},
  "teamLogo": "https://assets.nhle.com/logos/nhl/svg/EDM_light.svg",
  "currentTeamAbbrev": "EDM",
  "currentTeamId": 22,
  "headshot": "https://assets.nhle.com/mugshotsvdefault-light/8478402.png"
}
```

### Featured Stats (Current Season)

```json
{
  "featuredStats": {
    "season": 20252026,
    "regularSeason": {
      "subSeason": {
        "gamesPlayed": 56,
        "goals": 24,
        "assists": 55,
        "points": 79,
        "plusMinus": 14,
        "pim": 22,
        "gameWinningGoals": 5,
        "otGoals": 1,
        "shots": 195,
        "shootingPctg": 0.123,
        "powerPlayGoals": 11,
        "powerPlayPoints": 36,
        "shorthandedGoals": 0,
        "shorthandedPoints": 0
      },
      "career": {
        "gamesPlayed": 659,
        "goals": 335,
        "assists": 614,
        "points": 949,
        "plusMinus": 124,
        "pim": 130,
        "gameWinningGoals": 51,
        "otGoals": 12,
        "shots": 2241,
        "shootingPctg": 0.149
      }
    }
  }
}
```

### Last 5 Games

```json
{
  "last5Games": [
    {
      "gameId": 2025020850,
      "gameDate": "2026-02-15",
      "goals": 1,
      "assists": 2,
      "points": 3,
      "plusMinus": 2,
      "pim": 0,
      "shots": 5,
      "toi": "21:43",
      "powerPlayGoals": 0,
      "gameTypeId": 2,
      "teamAbbrev": "EDM",
      "opponentAbbrev": "CGY"
    }
  ]
}
```

### Season Totals (Career History)

```json
{
  "seasonTotals": [
    {
      "season": 20252026,
      "leagueAbbrev": "NHL",
      "gameTypeId": 2,
      "teamName": {"default": "Edmonton Oilers"},
      "gamesPlayed": 56,
      "goals": 24,
      "assists": 55,
      "points": 79,
      "avgToi": "21:36",
      "faceoffWinningPctg": 0.521,
      "powerPlayGoals": 11,
      "shorthandedGoals": 0,
      "shots": 195,
      "plusMinus": 14,
      "pim": 22
    }
  ]
}
```

### Awards

```json
{
  "awards": [
    {
      "trophy": {"default": "Hart Memorial Trophy"},
      "seasons": [
        {"seasonId": 20162017, "numberOfSeasons": 1},
        {"seasonId": 20202021, "numberOfSeasons": 1},
        {"seasonId": 20222023, "numberOfSeasons": 1}
      ]
    }
  ]
}
```

### Goalie-Specific Fields

For goalie players, the endpoint returns goalie-specific stats:

```json
{
  "featuredStats": {
    "regularSeason": {
      "subSeason": {
        "gamesPlayed": 40,
        "wins": 25,
        "losses": 10,
        "otLosses": 5,
        "goalsAgainstAvg": 2.45,
        "savePctg": 0.918,
        "shutouts": 3,
        "gamesStarted": 38
      }
    }
  },
  "last5Games": [
    {
      "gameId": 2025020820,
      "decision": "W",
      "shotsAgainst": 32,
      "goalsAgainst": 2,
      "savePctg": 0.938,
      "toi": "60:00"
    }
  ]
}
```

---

## Value for Our Platform

### 1. Player Props Enhancement (Page 5 — Player Props)

The `last5Games` data provides **recent form** that's crucial for player prop predictions:
- A player with 3+ points in 3 of his last 5 games is hot
- A player with 0 goals in last 5 is cold — bet the under
- SOG trends in last 5 directly predict shots-on-goal props

### 2. Goalie Matchup Details (Page 7 — Goalies)

Full goalie profiles with recent starts, save percentage trends, and career splits vs. specific opponents.

### 3. Career Context for Model Weights

Career stats let us weight regression toward career averages:
- A player shooting 18% this season with a 10% career rate → expect regression
- Career PPG rate can anchor short-sample projections

### 4. Player Comparison Tool

Side-by-side player comparison feature showing:
- Current season vs career rates
- Last 5 games trend
- Draft pedigree and age context

---

## Implementation

### Phase 1: Add Player Profile Method to NHLClient

```python
# src/api/nhl_client.py — add to NHLClient class

def get_player_profile(self, player_id: int) -> dict:
    """
    Get full player profile including career stats, last 5 games, and awards.

    Args:
        player_id: NHL player ID (e.g., 8478402 for Connor McDavid)

    Returns:
        Full player landing page data
    """
    url = f"{self.BASE_WEB_API}/player/{player_id}/landing"
    return self._fetch_sync(url, ttl=self.default_cache_ttl)

def get_player_recent_form(self, player_id: int) -> list[dict]:
    """
    Get last 5 game logs for a player.

    Args:
        player_id: NHL player ID

    Returns:
        List of recent game stat dicts
    """
    profile = self.get_player_profile(player_id)
    return profile.get("last5Games", [])

def get_player_season_stats(self, player_id: int) -> dict | None:
    """
    Get current season stats for a player.

    Returns:
        Current season stats dict or None
    """
    profile = self.get_player_profile(player_id)
    featured = profile.get("featuredStats", {})
    reg = featured.get("regularSeason", {})
    return reg.get("subSeason")
```

### Phase 2: Recent Form Analysis Utility

```python
# src/utils/player_form.py — Recent form analysis from player profiles

import pandas as pd
from src.api.nhl_client import NHLClient


def player_form_summary(client: NHLClient, player_id: int) -> dict:
    """
    Compute a summary of a player's recent form vs season average.

    Returns dict with form indicators useful for prop adjustments.
    """
    profile = client.get_player_profile(player_id)
    last5 = profile.get("last5Games", [])
    featured = profile.get("featuredStats", {})
    season = featured.get("regularSeason", {}).get("subSeason", {})
    position = profile.get("position", "")

    if not last5 or not season:
        return {}

    gp = season.get("gamesPlayed", 1)

    if position == "G":
        # Goalie form
        recent_sv_pct = sum(g.get("savePctg", 0) for g in last5) / len(last5)
        season_sv_pct = season.get("savePctg", 0)
        recent_gaa = sum(g.get("goalsAgainst", 0) for g in last5) / len(last5)

        return {
            "player_id": player_id,
            "name": f"{profile['firstName']['default']} {profile['lastName']['default']}",
            "position": "G",
            "games_played": gp,
            "recent_sv_pct": round(recent_sv_pct, 3),
            "season_sv_pct": round(season_sv_pct, 3),
            "sv_pct_trend": round(recent_sv_pct - season_sv_pct, 3),
            "recent_gaa": round(recent_gaa, 2),
            "form_rating": "hot" if recent_sv_pct > season_sv_pct + 0.01 else
                          "cold" if recent_sv_pct < season_sv_pct - 0.01 else "neutral",
        }
    else:
        # Skater form
        recent_ppg = sum(g.get("points", 0) for g in last5) / len(last5)
        season_ppg = season.get("points", 0) / gp if gp else 0
        recent_spg = sum(g.get("shots", 0) for g in last5) / len(last5)
        season_spg = season.get("shots", 0) / gp if gp else 0
        recent_gpg = sum(g.get("goals", 0) for g in last5) / len(last5)

        return {
            "player_id": player_id,
            "name": f"{profile['firstName']['default']} {profile['lastName']['default']}",
            "position": position,
            "games_played": gp,
            "recent_ppg": round(recent_ppg, 2),
            "season_ppg": round(season_ppg, 2),
            "ppg_trend": round(recent_ppg - season_ppg, 2),
            "recent_spg": round(recent_spg, 2),
            "season_spg": round(season_spg, 2),
            "recent_gpg": round(recent_gpg, 2),
            "season_gpg": round(season.get("goals", 0) / gp, 2) if gp else 0,
            "form_rating": "hot" if recent_ppg > season_ppg * 1.3 else
                          "cold" if recent_ppg < season_ppg * 0.7 else "neutral",
        }


def roster_form_report(
    client: NHLClient,
    player_ids: list[int],
) -> pd.DataFrame:
    """
    Generate form report for a list of players.

    Args:
        client: NHLClient instance
        player_ids: List of player IDs

    Returns:
        DataFrame with form indicators for each player
    """
    forms = []
    for pid in player_ids:
        try:
            summary = player_form_summary(client, pid)
            if summary:
                forms.append(summary)
        except Exception:
            continue

    if not forms:
        return pd.DataFrame()

    df = pd.DataFrame(forms)
    return df.sort_values("form_rating", ascending=False)
```

### Phase 3: Player Props Page Integration

```python
# Enhancement for pages/5_🎯_Player_Props.py
# Add recent form indicators next to prop lines

import streamlit as st
from src.utils.player_form import player_form_summary


def show_prop_with_form(client, player_id: int, prop_type: str, prop_line: float) -> None:
    """
    Display a player prop with recent form context.

    Args:
        client: NHLClient instance
        player_id: Player ID
        prop_type: Type of prop ("points", "shots", "goals")
        prop_line: The betting line value
    """
    form = player_form_summary(client, player_id)
    if not form:
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label=f"{form['name']} — {prop_type.title()} Line",
            value=prop_line,
        )

    with col2:
        if prop_type == "points":
            recent = form.get("recent_ppg", 0)
            season = form.get("season_ppg", 0)
        elif prop_type == "shots":
            recent = form.get("recent_spg", 0)
            season = form.get("season_spg", 0)
        elif prop_type == "goals":
            recent = form.get("recent_gpg", 0)
            season = form.get("season_gpg", 0)
        else:
            return

        st.metric(
            label="Recent (5G) / Season Avg",
            value=f"{recent:.1f}",
            delta=f"{recent - season:+.2f} vs season",
        )

    with col3:
        form_rating = form.get("form_rating", "neutral")
        if form_rating == "hot":
            st.success(f"🔥 HOT — consider OVER {prop_line}")
        elif form_rating == "cold":
            st.warning(f"❄️ COLD — consider UNDER {prop_line}")
        else:
            st.info(f"➖ Neutral form")
```

### Phase 4: Goalie Recent Form for Predictions

```python
# Enhancement for goalie analysis
# Quick lookup of a goalie's recent form to adjust game predictions

def adjust_goals_for_goalie_form(
    predicted_goals: float,
    client: NHLClient,
    goalie_id: int,
    max_adjustment: float = 0.3,
) -> float:
    """
    Adjust predicted goals based on goalie's recent form.

    If goalie is performing above their season average recently,
    slightly decrease expected goals against them (and vice versa).

    Args:
        predicted_goals: Base expected goals from the model
        client: NHLClient instance
        goalie_id: Goalie player ID
        max_adjustment: Maximum ± adjustment in goals

    Returns:
        Adjusted goal prediction
    """
    form = player_form_summary(client, goalie_id)
    if not form or form.get("position") != "G":
        return predicted_goals

    sv_trend = form.get("sv_pct_trend", 0)

    # Each 0.01 improvement in save % drops ~0.15 goals
    # (based on ~30 shots/game: 0.01 * 30 = 0.3 fewer goals)
    adjustment = -sv_trend * 15  # Scale factor

    # Clamp to max
    adjustment = max(-max_adjustment, min(max_adjustment, adjustment))

    return round(predicted_goals + adjustment, 2)
```

---

## Discovering Player IDs

Player IDs are embedded in game data we already fetch. Here's how to extract them:

```python
# Get player IDs from today's game schedule
def get_game_player_ids(client: NHLClient, game_id: int) -> dict:
    """
    Extract player IDs from a boxscore.

    Returns dict with 'home' and 'away' lists of player IDs.
    """
    boxscore = client.get_boxscore(game_id)
    result = {"home": [], "away": []}

    for side in ("homeTeam", "awayTeam"):
        key = "home" if side == "homeTeam" else "away"
        team = boxscore.get("playerByGameStats", {}).get(side, {})
        for group in ("forwards", "defense", "goalies"):
            for player in team.get(group, []):
                result[key].append(player["playerId"])

    return result
```

---

## API Rate Considerations

- Player profile responses are moderate in size (~15-30 KB each)
- Use standard 5-minute cache TTL for player profiles
- When fetching form for an entire roster (~25 players), expect 25 API calls
- Consider pre-fetching rosters for today's games and caching the results

---

## Dependencies

- No new packages required
- Uses existing `NHLClient`, `pandas`
- Depends on `get_boxscore()` method from roadmap 11 for player ID discovery
