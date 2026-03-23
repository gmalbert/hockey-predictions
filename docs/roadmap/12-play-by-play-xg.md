# 12 — Play-by-Play Data & Shot Analytics

## Status: Proposed

## Overview

The NHL API provides **play-by-play** data for every game, containing event-level detail with **x/y coordinates** on the ice surface. This endpoint is completely untapped in our codebase and enables advanced shot analytics, expected goals (xG) modeling, and situational analysis.

### Endpoint

| Endpoint | URL Pattern | Description |
|----------|-------------|-------------|
| **Play-by-Play** | `GET /v1/gamecenter/{gameId}/play-by-play` | Every event in a game with coordinates |

### Sample URL

`https://api-web.nhle.com/v1/gamecenter/2023021153/play-by-play`

---

## What Data Is Available

### Event Types (typeDescKey values)

| Type Code | Key | Description | Has Coordinates |
|-----------|-----|-------------|-----------------|
| 502 | `faceoff` | Faceoff | ✅ |
| 503 | `hit` | Hit | ✅ |
| 504 | `giveaway` | Giveaway | ✅ |
| 505 | `goal` | Goal scored | ✅ |
| 506 | `shot-on-goal` | Shot on goal | ✅ |
| 507 | `missed-shot` | Missed shot | ✅ |
| 508 | `blocked-shot` | Blocked shot | ✅ |
| 509 | `penalty` | Penalty | ✅ |
| 516 | `stoppage` | Stoppage of play | ❌ |
| 520 | `period-start` | Period start | ❌ |
| 521 | `period-end` | Period end | ❌ |
| 524 | `game-end` | Game end | ❌ |
| 525 | `takeaway` | Takeaway | ✅ |

### Key Fields Per Event

```json
{
  "eventId": 109,
  "periodDescriptor": {"number": 1, "periodType": "REG"},
  "timeInPeriod": "00:36",
  "timeRemaining": "19:24",
  "situationCode": "1541",
  "homeTeamDefendingSide": "left",
  "typeCode": 505,
  "typeDescKey": "goal",
  "details": {
    "xCoord": 63,
    "yCoord": -10,
    "zoneCode": "O",
    "shotType": "wrist",
    "scoringPlayerId": 8473512,
    "assist1PlayerId": 8480879,
    "eventOwnerTeamId": 9,
    "goalieInNetId": 8475852,
    "awayScore": 0,
    "homeScore": 1
  }
}
```

### Situation Code Format

The `situationCode` field is a 4-digit string: `AAHH` where:
- First 2 digits = away team skaters on ice (including goalie)
- Last 2 digits = home team skaters on ice (including goalie)
- `1551` = 5v5 (normal play, both goalies in)
- `1451` = away on power play (4 home + goalie vs 5 away + goalie)
- `1541` = home on power play
- `0651` = home pulled goalie (6 skaters, no goalie vs 5 + goalie)

### Coordinate System

- **x range**: -100 to 100 (center ice = 0)
- **y range**: -42.5 to 42.5
- `homeTeamDefendingSide` indicates which side the home team defends
- Offensive zone: `zoneCode = "O"`, Defensive: `"D"`, Neutral: `"N"`

---

## Value for Our Platform

### 1. Expected Goals (xG) Model

Shot location is the #1 predictor of goal probability. With x/y coordinates we can build a proper xG model:

- Shots from the slot (close to net, center) have ~15-20% goal probability
- Shots from the point (far, wide) have ~3-5% goal probability
- Shot type matters: deflections > wrist > snap > slap (from distance)

**This directly supports our roadmap item 02-modeling.md** for building a more sophisticated prediction model.

### 2. Shooting Heatmaps

Visual shot maps for each team showing where they tend to score from — useful for identifying teams that generate high-quality chances vs. perimeter shooters.

### 3. Power Play / Penalty Kill Deep Analysis

With situation codes, we can isolate:
- 5v5 scoring rates (more predictive than all-situations stats)
- PP conversion with shot locations
- PK aggressiveness (blocked shots, zone locations)

### 4. Faceoff Analysis

Faceoff locations and winners per game help predict:
- Which teams control neutral-zone starts
- Zone-start advantages (offensive vs defensive)

---

## Implementation

### Phase 1: Add Play-by-Play Method to NHLClient

```python
# src/api/nhl_client.py — add to NHLClient class

def get_play_by_play(self, game_id: int) -> dict:
    """
    Get full play-by-play data for a game.

    Args:
        game_id: NHL game ID (e.g., 2025020123)

    Returns:
        Play-by-play data with all events
    """
    url = f"{self.BASE_WEB_API}/gamecenter/{game_id}/play-by-play"
    return self._fetch_sync(url, ttl=self.schedule_cache_ttl)

def get_game_shots(self, game_id: int) -> list[dict]:
    """
    Extract all shot events (goals, SOG, missed, blocked) from a game.

    Args:
        game_id: NHL game ID

    Returns:
        List of shot event dicts with coordinates and metadata
    """
    pbp = self.get_play_by_play(game_id)
    shot_types = {"goal", "shot-on-goal", "missed-shot", "blocked-shot"}

    shots = []
    for play in pbp.get("plays", []):
        if play.get("typeDescKey") not in shot_types:
            continue

        details = play.get("details", {})
        shots.append({
            "event_id": play.get("eventId"),
            "period": play.get("periodDescriptor", {}).get("number"),
            "time_in_period": play.get("timeInPeriod"),
            "type": play.get("typeDescKey"),
            "x": details.get("xCoord"),
            "y": details.get("yCoord"),
            "zone": details.get("zoneCode"),
            "shot_type": details.get("shotType"),
            "shooting_player_id": details.get(
                "scoringPlayerId",
                details.get("shootingPlayerId"),
            ),
            "goalie_id": details.get("goalieInNetId"),
            "team_id": details.get("eventOwnerTeamId"),
            "situation": play.get("situationCode"),
            "home_defending_side": play.get("homeTeamDefendingSide"),
            # For blocked shots
            "blocking_player_id": details.get("blockingPlayerId"),
            # For missed shots
            "miss_reason": details.get("reason"),
        })

    return shots
```

### Phase 2: Shot Data Collection & Processing

```python
# src/utils/shot_analysis.py — Shot analytics from play-by-play data

import math
from collections import defaultdict


# NHL rink constants (feet)
GOAL_X = 89  # Goal line distance from center
GOAL_Y = 0   # Goal is centered


def shot_distance(x: float, y: float, defending_side: str, is_home_team: bool) -> float:
    """
    Calculate shot distance to the goal in feet.

    Args:
        x: Shot x-coordinate
        y: Shot y-coordinate
        defending_side: Which side home team defends ("left" or "right")
        is_home_team: Whether the shooting team is the home team

    Returns:
        Distance in feet from shot to goal
    """
    # Determine which goal the team is shooting at
    # Home team shoots at the goal OPPOSITE their defending side
    if is_home_team:
        target_x = GOAL_X if defending_side == "left" else -GOAL_X
    else:
        target_x = -GOAL_X if defending_side == "left" else GOAL_X

    return math.sqrt((x - target_x) ** 2 + (y - GOAL_Y) ** 2)


def shot_angle(x: float, y: float, defending_side: str, is_home_team: bool) -> float:
    """
    Calculate the angle of a shot relative to the goal.

    Returns value in degrees. 0 = straight on, 90 = from the side.
    """
    if is_home_team:
        target_x = GOAL_X if defending_side == "left" else -GOAL_X
    else:
        target_x = -GOAL_X if defending_side == "left" else GOAL_X

    dx = abs(x - target_x)
    dy = abs(y - GOAL_Y)

    if dx == 0:
        return 90.0
    return math.degrees(math.atan(dy / dx))


def naive_xg(distance: float, angle: float, shot_type: str | None = None) -> float:
    """
    Simple expected goals estimate based on distance and angle.

    This is a naive model — a proper xG model would use logistic regression
    trained on historical data. This serves as a starting point.

    Args:
        distance: Shot distance in feet
        angle: Shot angle in degrees
        shot_type: Type of shot (wrist, slap, snap, tip-in, backhand, deflected)

    Returns:
        Estimated goal probability (0 to 1)
    """
    # Base probability from distance (exponential decay)
    base = max(0.01, 0.4 * math.exp(-0.035 * distance))

    # Angle penalty (wider angle = harder to score)
    angle_factor = max(0.2, 1.0 - (angle / 90.0) * 0.6)

    # Shot type multiplier
    type_multipliers = {
        "tip-in": 1.3,
        "deflected": 1.25,
        "wrist": 1.0,
        "snap": 0.95,
        "backhand": 0.85,
        "slap": 0.75,
    }
    type_mult = type_multipliers.get(shot_type, 1.0) if shot_type else 1.0

    return min(0.95, base * angle_factor * type_mult)


def compute_game_xg(shots: list[dict], home_team_id: int) -> dict:
    """
    Compute expected goals for both teams from shot data.

    Args:
        shots: List of shot dicts from get_game_shots()
        home_team_id: Team ID of the home team

    Returns:
        Dict with home_xg, away_xg, and per-shot details
    """
    home_xg = 0.0
    away_xg = 0.0
    enriched_shots = []

    for shot in shots:
        x, y = shot.get("x"), shot.get("y")
        if x is None or y is None:
            continue

        is_home = shot["team_id"] == home_team_id
        defending_side = shot.get("home_defending_side", "left")

        dist = shot_distance(x, y, defending_side, is_home)
        ang = shot_angle(x, y, defending_side, is_home)
        xg = naive_xg(dist, ang, shot.get("shot_type"))

        if is_home:
            home_xg += xg
        else:
            away_xg += xg

        enriched_shots.append({
            **shot,
            "distance": round(dist, 1),
            "angle": round(ang, 1),
            "xg": round(xg, 4),
            "is_home": is_home,
        })

    return {
        "home_xg": round(home_xg, 2),
        "away_xg": round(away_xg, 2),
        "shots": enriched_shots,
    }


def team_5v5_stats(shots: list[dict], team_id: int) -> dict:
    """
    Filter to 5v5 (even strength) shots only for a given team.

    The situation code '1551' indicates standard 5v5 play.

    Args:
        shots: List of shot dicts
        team_id: Team ID to filter for

    Returns:
        Dict with 5v5 shot count, goal count, and shooting %
    """
    ev_shots = [
        s for s in shots
        if s.get("situation") == "1551" and s["team_id"] == team_id
    ]
    goals = sum(1 for s in ev_shots if s["type"] == "goal")
    sog = sum(1 for s in ev_shots if s["type"] in ("goal", "shot-on-goal"))

    return {
        "total_shot_attempts": len(ev_shots),
        "shots_on_goal": sog,
        "goals": goals,
        "shooting_pct": round(goals / sog * 100, 1) if sog else 0,
    }
```

### Phase 3: Shot Map Visualization (Streamlit)

```python
# Example: Add shot map to a game detail view
# Could be integrated into pages/1_📅_Todays_Games.py or a new page

import streamlit as st
import pandas as pd
import altair as alt
from src.api.nhl_client import NHLClient


def render_shot_map(shots: list[dict], home_team: str, away_team: str) -> None:
    """
    Render a shot location chart using Altair.

    Args:
        shots: Enriched shot list from compute_game_xg()
        home_team: Home team abbreviation
        away_team: Away team abbreviation
    """
    if not shots:
        st.info("No shot data available.")
        return

    df = pd.DataFrame(shots)
    df["team"] = df["is_home"].map({True: home_team, False: away_team})
    df["is_goal"] = df["type"] == "goal"
    df["size"] = df["xg"] * 100 + 10  # Scale xG for dot size

    chart = (
        alt.Chart(df)
        .mark_circle()
        .encode(
            x=alt.X("x:Q", scale=alt.Scale(domain=[-100, 100]), title=""),
            y=alt.Y("y:Q", scale=alt.Scale(domain=[-43, 43]), title=""),
            color=alt.Color("team:N", legend=alt.Legend(title="Team")),
            size=alt.Size("size:Q", legend=None),
            shape=alt.Shape(
                "is_goal:N",
                scale=alt.Scale(domain=[True, False], range=["diamond", "circle"]),
                legend=alt.Legend(title="Goal?"),
            ),
            tooltip=["team", "type", "shot_type", "xg", "distance", "angle", "time_in_period"],
        )
        .properties(width=600, height=300, title="Shot Map")
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)
```

### Phase 4: Batch xG Collection for Historical Analysis

```python
# collect_xg.py — Compute and store xG for every game in a season

import json
import time
from pathlib import Path
from src.api.nhl_client import NHLClient
from src.utils.shot_analysis import compute_game_xg


def collect_season_xg(
    client: NHLClient,
    season: str = "20252026",
    delay: float = 0.5,
) -> list[dict]:
    """
    Compute xG for all completed regular-season games.

    Returns list of per-game xG summaries.
    """
    teams = list(client.TEAM_ID_MAP.keys())
    game_ids_processed: set[int] = set()
    results = []

    # Use one team's schedule to get all game IDs (avoid duplicates)
    for team in teams[:16]:  # Only need half the teams to cover all games
        schedule = client.get_team_schedule(team, season)
        for game in schedule.get("games", []):
            gid = game["id"]
            state = game.get("gameState", "")
            game_type = game.get("gameType", 0)

            if state != "OFF" or game_type != 2:
                continue
            if gid in game_ids_processed:
                continue

            game_ids_processed.add(gid)
            try:
                shots = client.get_game_shots(gid)
                home_id = game["homeTeam"]["id"] if "id" in game.get("homeTeam", {}) else None

                if home_id and shots:
                    xg_data = compute_game_xg(shots, home_id)
                    results.append({
                        "game_id": gid,
                        "game_date": game.get("gameDate"),
                        "home_team": game["homeTeam"]["abbrev"],
                        "away_team": game["awayTeam"]["abbrev"],
                        "home_score": game["homeTeam"].get("score", 0),
                        "away_score": game["awayTeam"].get("score", 0),
                        "home_xg": xg_data["home_xg"],
                        "away_xg": xg_data["away_xg"],
                        "total_shots": len(xg_data["shots"]),
                    })
                    print(f"  ✓ {gid}: {results[-1]['away_team']}({xg_data['away_xg']}) @ "
                          f"{results[-1]['home_team']}({xg_data['home_xg']})")
            except Exception as e:
                print(f"  ✗ {gid}: {e}")

            time.sleep(delay)

    return results


if __name__ == "__main__":
    client = NHLClient()
    print("Computing xG for 2025-26 season...")
    xg_results = collect_season_xg(client)

    output = Path("data_files/historical/xg_2025_26.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(xg_results, indent=2))
    print(f"\nSaved {len(xg_results)} game xG records to {output}")
```

---

## Future Enhancements

1. **Train a proper xG model** using logistic regression on historical shot data (distance, angle, shot type, situation, rebound, rush) instead of the naive formula
2. **Corsi/Fenwick metrics** — all shot attempts (SOG + missed + blocked) as possession proxy
3. **High-danger chance tracking** — shots from the slot area (|y| < 10, |x - goal| < 25)
4. **Rebound detection** — shots within 3 seconds of a previous save

---

## API Rate Considerations

- Play-by-play responses are **large** (~200-500 KB per game)
- A full season would be ~250-650 MB of raw data
- **Always use 24-hour cache TTL** for completed games
- Consider extracting and storing only shot events to reduce storage
- Batch collection: use 0.5s delay between requests

---

## Dependencies

- No new packages for core functionality
- `altair` (already available via Streamlit) for shot map visualization
- `pandas` (already installed) for data manipulation
