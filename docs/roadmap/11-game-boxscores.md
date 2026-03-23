# 11 — Game Boxscores & Landing Endpoints

## Status: Proposed

## Overview

The NHL API exposes **per-game boxscores** and **game landing** pages that we are **not currently using**. These endpoints contain granular player-level and goalie-level stats for each game, scoring summaries, three-star selections, and penalty details—all of which can significantly improve our Poisson model, goalie analysis, and player props.

### Endpoints

| Endpoint | URL Pattern | Description |
|----------|-------------|-------------|
| **Boxscore** | `GET /v1/gamecenter/{gameId}/boxscore` | Full player stats per game |
| **Landing** | `GET /v1/gamecenter/{gameId}/landing` | Scoring summary, three stars, penalties |

### Sample URLs

- Boxscore: `https://api-web.nhle.com/v1/gamecenter/2023021153/boxscore`
- Landing: `https://api-web.nhle.com/v1/gamecenter/2023021153/landing`

> **Game IDs** follow the format `{season}{gameType}{gameNumber}`, e.g., `2025020001` = 2025-26 regular season game 1. We already collect game IDs from the schedule endpoint.

---

## What Data Is Available

### Boxscore Response — Per-Player Stats

For **each skater** (grouped by forwards/defense/goalies, home/away):

```
playerId, sweaterNumber, name, position,
goals, assists, points, plusMinus, pim, hits,
powerPlayGoals, sog (shots on goal), faceoffWinningPctg,
toi (time on ice), blockedShots, shifts, giveaways, takeaways
```

For **each goalie**:

```
playerId, name, position,
evenStrengthShotsAgainst (e.g., "30/31"),
powerPlayShotsAgainst, shorthandedShotsAgainst,
saveShotsAgainst (e.g., "32/34"), savePctg,
evenStrengthGoalsAgainst, powerPlayGoalsAgainst,
shorthandedGoalsAgainst, goalsAgainst, toi,
starter (boolean), decision ("W"/"L"), shotsAgainst, saves
```

### Landing Response — Game Summary

```
scoring: [{period, goals: [{playerId, strength, shotType, assists, timeInPeriod}]}]
threeStars: [{star, playerId, name, position, goals/assists/savePctg}]
penalties: [{period, penalties: [{timeInPeriod, type, duration, committedByPlayer, drawnBy, descKey}]}]
```

---

## Value for Our Platform

### 1. Improved Poisson Model Inputs

Currently our Poisson model uses **team-level seasons stats** (goals for/against per game). With boxscores, we can compute:

- **Rolling averages** (last 5/10 games) instead of season-long averages
- **Home vs. Away goal splits** from actual game data
- **Strength-adjusted scoring** (even strength vs. power play vs. shorthanded)
- **Shot quality signals** (high SOG + low goals = unlucky / regression candidate)

### 2. Goalie Matchup Enhancement

Our goalie page currently shows season-level save% and GAA. With boxscores we get:

- **Recent form**: Save% over last 5 starts
- **Even-strength save%** (isolates goalie from PP/PK effects)
- **Starter identification**: Know who started each game
- **Workload tracking**: Shots-against per game trends

### 3. Player Props Data

For the Player Props page, boxscores provide:

- **Game-level hit counts** — for hits prop modeling
- **Blocked shots per game** — for blocked shots props
- **SOG consistency** — rolling SOG averages for shots props
- **TOI trends** — spot increasing/decreasing ice time

### 4. Penalty & Discipline Tracking

Landing endpoint gives us penalty details per game, enabling:

- **PIM trends** for players
- **Penalty frequency** per team (helps predict PP/PK opportunities)

---

## Implementation

### Phase 1: Add Methods to NHLClient

```python
# src/api/nhl_client.py — add to NHLClient class

# -------------------------------------------------------------------------
# Game Detail Endpoints
# -------------------------------------------------------------------------

def get_boxscore(self, game_id: int) -> dict:
    """
    Get detailed boxscore for a completed game.

    Args:
        game_id: NHL game ID (e.g., 2025020123)

    Returns:
        Boxscore data with player-by-game stats
    """
    url = f"{self.BASE_WEB_API}/gamecenter/{game_id}/boxscore"
    return self._fetch_sync(url, ttl=self.schedule_cache_ttl)

def get_game_landing(self, game_id: int) -> dict:
    """
    Get game landing page with scoring summary, three stars, penalties.

    Args:
        game_id: NHL game ID

    Returns:
        Landing page data
    """
    url = f"{self.BASE_WEB_API}/gamecenter/{game_id}/landing"
    return self._fetch_sync(url, ttl=self.schedule_cache_ttl)

def get_boxscore_players(self, game_id: int) -> dict[str, list[dict]]:
    """
    Get simplified player stats from a boxscore.

    Args:
        game_id: NHL game ID

    Returns:
        Dict with 'home_skaters', 'away_skaters', 'home_goalies', 'away_goalies'
    """
    box = self.get_boxscore(game_id)
    stats = box.get("playerByGameStats", {})

    def parse_skaters(team_data: dict) -> list[dict]:
        skaters = []
        for group in ("forwards", "defense"):
            for p in team_data.get(group, []):
                skaters.append({
                    "player_id": p.get("playerId"),
                    "name": p.get("name", {}).get("default", ""),
                    "position": p.get("position"),
                    "goals": p.get("goals", 0),
                    "assists": p.get("assists", 0),
                    "points": p.get("points", 0),
                    "plus_minus": p.get("plusMinus", 0),
                    "pim": p.get("pim", 0),
                    "hits": p.get("hits", 0),
                    "sog": p.get("sog", 0),
                    "blocked_shots": p.get("blockedShots", 0),
                    "toi": p.get("toi", "0:00"),
                    "pp_goals": p.get("powerPlayGoals", 0),
                    "faceoff_pct": p.get("faceoffWinningPctg", 0),
                    "giveaways": p.get("giveaways", 0),
                    "takeaways": p.get("takeaways", 0),
                    "shifts": p.get("shifts", 0),
                })
        return skaters

    def parse_goalies(team_data: dict) -> list[dict]:
        return [
            {
                "player_id": g.get("playerId"),
                "name": g.get("name", {}).get("default", ""),
                "save_pct": g.get("savePctg", 0),
                "goals_against": g.get("goalsAgainst", 0),
                "shots_against": g.get("shotsAgainst", 0),
                "saves": g.get("saves", 0),
                "toi": g.get("toi", "0:00"),
                "starter": g.get("starter", False),
                "decision": g.get("decision"),
                "es_goals_against": g.get("evenStrengthGoalsAgainst", 0),
                "pp_goals_against": g.get("powerPlayGoalsAgainst", 0),
                "sh_goals_against": g.get("shorthandedGoalsAgainst", 0),
            }
            for g in team_data.get("goalies", [])
        ]

    return {
        "home_skaters": parse_skaters(stats.get("homeTeam", {})),
        "away_skaters": parse_skaters(stats.get("awayTeam", {})),
        "home_goalies": parse_goalies(stats.get("homeTeam", {})),
        "away_goalies": parse_goalies(stats.get("awayTeam", {})),
    }
```

### Phase 2: Historical Boxscore Collection Script

```python
# collect_boxscores.py — Bulk historical data collection

"""Collect boxscores for completed games from the current season."""

import time
from datetime import date, timedelta
from src.api.nhl_client import NHLClient


def collect_season_boxscores(
    client: NHLClient,
    start_date: str = "2025-10-04",
    end_date: str | None = None,
    delay: float = 0.5,
) -> list[dict]:
    """
    Collect boxscores for all completed regular-season games in a date range.

    Args:
        client: NHLClient instance
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (defaults to today)
        delay: Seconds between API requests to avoid rate limiting

    Returns:
        List of (game_id, boxscore) tuples
    """
    if end_date is None:
        end_date = date.today().isoformat()

    current = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    game_ids_seen: set[int] = set()
    results = []

    while current <= end:
        schedule = client.get_schedule(current.isoformat())

        for week in schedule.get("gameWeek", []):
            for game in week.get("games", []):
                gid = game["id"]
                state = game.get("gameState", "")
                game_type = game.get("gameType", 0)

                # Only completed regular-season games
                if state != "OFF" or game_type != 2:
                    continue
                if gid in game_ids_seen:
                    continue

                game_ids_seen.add(gid)
                try:
                    box = client.get_boxscore_players(gid)
                    box["game_id"] = gid
                    box["game_date"] = game.get("gameDate", "")
                    box["home_team"] = game["homeTeam"]["abbrev"]
                    box["away_team"] = game["awayTeam"]["abbrev"]
                    box["home_score"] = game["homeTeam"].get("score", 0)
                    box["away_score"] = game["awayTeam"].get("score", 0)
                    results.append(box)
                    print(f"  ✓ {gid} ({box['away_team']} @ {box['home_team']})")
                except Exception as e:
                    print(f"  ✗ {gid}: {e}")

                time.sleep(delay)

        current += timedelta(days=7)  # Schedule endpoint returns full weeks

    return results


if __name__ == "__main__":
    import json
    from pathlib import Path

    client = NHLClient()
    print("Collecting boxscores for 2025-26 season...")
    boxscores = collect_season_boxscores(client)

    output = Path("data_files/historical/boxscores_2025_26.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(boxscores, indent=2))
    print(f"\nSaved {len(boxscores)} boxscores to {output}")
```

### Phase 3: Rolling Averages Utility

```python
# src/utils/rolling_stats.py — Compute rolling player/team averages from boxscores

import json
from pathlib import Path
from collections import defaultdict


def load_boxscores(path: str = "data_files/historical/boxscores_2025_26.json") -> list[dict]:
    """Load boxscore data from JSON file."""
    return json.loads(Path(path).read_text())


def team_rolling_goals(
    boxscores: list[dict],
    team: str,
    window: int = 10,
) -> list[dict]:
    """
    Compute rolling goal averages for a team over their last N games.

    Args:
        boxscores: List of boxscore dicts (sorted by date)
        team: Team abbreviation
        window: Number of games in rolling window

    Returns:
        List of dicts: [{date, goals_for, goals_against, rolling_gf, rolling_ga}]
    """
    team_games = []
    for box in sorted(boxscores, key=lambda b: b.get("game_date", "")):
        if box["home_team"] == team:
            team_games.append({
                "date": box["game_date"],
                "goals_for": box["home_score"],
                "goals_against": box["away_score"],
            })
        elif box["away_team"] == team:
            team_games.append({
                "date": box["game_date"],
                "goals_for": box["away_score"],
                "goals_against": box["home_score"],
            })

    # Compute rolling averages
    for i, game in enumerate(team_games):
        start = max(0, i - window + 1)
        recent = team_games[start : i + 1]
        n = len(recent)
        game["rolling_gf"] = round(sum(g["goals_for"] for g in recent) / n, 2)
        game["rolling_ga"] = round(sum(g["goals_against"] for g in recent) / n, 2)

    return team_games


def goalie_recent_form(
    boxscores: list[dict],
    goalie_name: str,
    last_n: int = 5,
) -> dict:
    """
    Get a goalie's recent form from boxscore data.

    Args:
        boxscores: List of boxscore dicts
        goalie_name: Goalie's display name (e.g., "I. Sorokin")
        last_n: Number of recent starts to consider

    Returns:
        Dict with aggregated recent stats
    """
    starts = []
    for box in sorted(boxscores, key=lambda b: b.get("game_date", ""), reverse=True):
        for side in ("home_goalies", "away_goalies"):
            for g in box.get(side, []):
                if g["name"] == goalie_name and g.get("starter"):
                    starts.append({
                        "date": box["game_date"],
                        "save_pct": g["save_pct"],
                        "goals_against": g["goals_against"],
                        "shots_against": g["shots_against"],
                        "saves": g["saves"],
                        "decision": g.get("decision"),
                        "es_goals_against": g.get("es_goals_against", 0),
                    })
        if len(starts) >= last_n:
            break

    starts = starts[:last_n]
    if not starts:
        return {"starts": 0}

    total_shots = sum(s["shots_against"] for s in starts)
    total_saves = sum(s["saves"] for s in starts)
    total_ga = sum(s["goals_against"] for s in starts)
    total_es_ga = sum(s["es_goals_against"] for s in starts)

    return {
        "starts": len(starts),
        "recent_save_pct": round(total_saves / total_shots, 4) if total_shots else 0,
        "recent_gaa": round(total_ga / len(starts), 2),
        "recent_es_ga_avg": round(total_es_ga / len(starts), 2),
        "wins": sum(1 for s in starts if s.get("decision") == "W"),
        "losses": sum(1 for s in starts if s.get("decision") == "L"),
        "games": [
            {"date": s["date"], "sv%": s["save_pct"], "ga": s["goals_against"]}
            for s in starts
        ],
    }


def player_hit_trends(
    boxscores: list[dict],
    player_name: str,
    last_n: int = 10,
) -> dict:
    """
    Compute a player's recent hit and SOG trends for prop betting.

    Args:
        boxscores: List of boxscore dicts
        player_name: Player display name
        last_n: Number of recent games

    Returns:
        Dict with hit/SOG averages and game log
    """
    games = []
    for box in sorted(boxscores, key=lambda b: b.get("game_date", ""), reverse=True):
        for side in ("home_skaters", "away_skaters"):
            for p in box.get(side, []):
                if p["name"] == player_name:
                    games.append({
                        "date": box["game_date"],
                        "hits": p["hits"],
                        "sog": p["sog"],
                        "blocked_shots": p["blocked_shots"],
                        "toi": p["toi"],
                        "points": p["points"],
                    })
        if len(games) >= last_n:
            break

    games = games[:last_n]
    if not games:
        return {"games_found": 0}

    n = len(games)
    return {
        "games_found": n,
        "avg_hits": round(sum(g["hits"] for g in games) / n, 1),
        "avg_sog": round(sum(g["sog"] for g in games) / n, 1),
        "avg_blocked": round(sum(g["blocked_shots"] for g in games) / n, 1),
        "game_log": games,
    }
```

### Phase 4: Integration with Existing Pages

#### Today's Games — Show Recent Form

```python
# In pages/1_📅_Todays_Games.py — add a "Recent Form" expander under each game

# After loading today's games:
from src.utils.rolling_stats import team_rolling_goals, load_boxscores

boxscores = load_boxscores()

for game in todays_games:
    home = game["home_team"]
    away = game["away_team"]

    home_rolling = team_rolling_goals(boxscores, home, window=5)
    away_rolling = team_rolling_goals(boxscores, away, window=5)

    with st.expander(f"📈 Recent Form: {away} @ {home}"):
        col1, col2 = st.columns(2)
        with col1:
            if home_rolling:
                last = home_rolling[-1]
                st.metric(f"{home} GF/G (5-game)", last["rolling_gf"])
                st.metric(f"{home} GA/G (5-game)", last["rolling_ga"])
        with col2:
            if away_rolling:
                last = away_rolling[-1]
                st.metric(f"{away} GF/G (5-game)", last["rolling_gf"])
                st.metric(f"{away} GA/G (5-game)", last["rolling_ga"])
```

#### Goalies Page — Recent Form Breakdown

```python
# In pages/7_🥅_Goalies.py — add recent-start breakdown

from src.utils.rolling_stats import goalie_recent_form, load_boxscores
import pandas as pd

boxscores = load_boxscores()

# After goalie selection:
form = goalie_recent_form(boxscores, selected_goalie_name, last_n=5)

if form["starts"] > 0:
    st.subheader(f"Last {form['starts']} Starts")
    st.metric("Recent Save %", f"{form['recent_save_pct']:.3f}")
    st.metric("Recent GAA", form["recent_gaa"])
    st.metric("Record", f"{form['wins']}W - {form['losses']}L")

    df = pd.DataFrame(form["games"])
    st.dataframe(df, use_container_width=True)
```

---

## API Rate Considerations

- Boxscore responses are ~50-100 KB each
- With ~1,300 regular season games, a full season is ~65-130 MB
- Use **24-hour cache TTL** for completed games (they never change)
- For live/future games, use the standard 5-minute TTL
- Batch collection should add `time.sleep(0.5)` between requests

---

## Dependencies

- No new packages required
- Uses existing `httpx`, `json`, `pathlib` stack
- Boxscore data integrates with existing `data_files/historical/` structure
