# NHL API Reference

## Overview
Unofficial NHL API endpoints used in this project. These APIs are not officially documented and may change.

---

## Base URLs

| API | Base URL | Purpose |
|-----|----------|---------|
| Web API | `https://api-web.nhle.com/v1` | Schedules, standings, player info |
| Stats API | `https://api.nhle.com/stats/rest/en` | Statistical summaries |

---

## Web API Endpoints

### Schedule

#### Get Schedule by Date
```
GET /schedule/{date}
```

**Parameters**:
- `date` (string): Date in `YYYY-MM-DD` format

**Example**:
```python
import httpx

url = "https://api-web.nhle.com/v1/schedule/2026-02-02"
response = httpx.get(url)
data = response.json()
```

**Response Structure**:
```json
{
  "gameWeek": [
    {
      "date": "2026-02-02",
      "games": [
        {
          "id": 2025020750,
          "gameType": 2,
          "gameState": "FUT",
          "startTimeUTC": "2026-02-03T00:00:00Z",
          "homeTeam": {
            "id": 8,
            "abbrev": "MTL",
            "score": null
          },
          "awayTeam": {
            "id": 10,
            "abbrev": "TOR",
            "score": null
          },
          "venue": {
            "default": "Centre Bell"
          }
        }
      ]
    }
  ]
}
```

**Game Types**:
- `1` = Preseason
- `2` = Regular Season
- `3` = Playoffs

**Game States**:
- `FUT` = Future/Scheduled
- `PRE` = Pre-game
- `LIVE` = In Progress
- `OFF` = Final
- `CRIT` = Critical (close game)

---

### Standings

#### Get Current Standings
```
GET /standings/now
```

**Example**:
```python
url = "https://api-web.nhle.com/v1/standings/now"
response = httpx.get(url)
standings = response.json()
```

**Response Structure**:
```json
{
  "standings": [
    {
      "teamAbbrev": {"default": "TOR"},
      "teamName": {"default": "Toronto Maple Leafs"},
      "divisionName": "Atlantic",
      "conferenceName": "Eastern",
      "gamesPlayed": 50,
      "wins": 30,
      "losses": 15,
      "otLosses": 5,
      "points": 65,
      "goalFor": 170,
      "goalAgainst": 140,
      "goalDifferential": 30,
      "streakCode": "W3",
      "l10Wins": 7,
      "l10Losses": 2,
      "l10OtLosses": 1
    }
  ]
}
```

---

### Team Information

#### Get Team Schedule for Season
```
GET /club-schedule-season/{team}/{season}
```

**Parameters**:
- `team` (string): Team abbreviation (e.g., `TOR`, `MTL`)
- `season` (string): Season ID in `YYYYYYYY` format (e.g., `20252026`)

**Example**:
```python
url = "https://api-web.nhle.com/v1/club-schedule-season/TOR/20252026"
response = httpx.get(url)
games = response.json()
```

**Response includes**:
- All games for the team in the season
- Home/away indicator
- Opponent info
- Final scores (for completed games)

---

#### Get Team Roster
```
GET /roster/{team}/current
```

**Example**:
```python
url = "https://api-web.nhle.com/v1/roster/TOR/current"
response = httpx.get(url)
roster = response.json()
```

---

### Player Information

#### Get Player Game Log
```
GET /player/{playerId}/game-log/{season}/{gameType}
```

**Parameters**:
- `playerId` (int): NHL player ID
- `season` (string): Season ID
- `gameType` (int): 2 = regular season, 3 = playoffs

**Example**:
```python
# Auston Matthews player ID: 8479318
url = "https://api-web.nhle.com/v1/player/8479318/game-log/20252026/2"
response = httpx.get(url)
game_log = response.json()
```

---

## Stats API Endpoints

### Team Statistics

#### Get Team Summary
```
GET /team/summary
```

**Query Parameters**:
- `cayenneExp` (string): Filter expression, e.g., `seasonId=20252026`
- `sort` (string): Sort field, e.g., `points`
- `direction` (string): `ASC` or `DESC`

**Example**:
```python
url = "https://api.nhle.com/stats/rest/en/team/summary"
params = {
    "cayenneExp": "seasonId=20252026",
    "sort": "points",
    "direction": "DESC"
}
response = httpx.get(url, params=params)
team_stats = response.json()
```

**Response includes**:
```json
{
  "data": [
    {
      "teamId": 10,
      "teamAbbrev": "TOR",
      "gamesPlayed": 50,
      "wins": 30,
      "losses": 15,
      "otLosses": 5,
      "goalsFor": 170,
      "goalsAgainst": 140,
      "goalsForPerGame": 3.4,
      "goalsAgainstPerGame": 2.8,
      "powerPlayPct": 25.5,
      "penaltyKillPct": 82.3,
      "shotsForPerGame": 32.5,
      "shotsAgainstPerGame": 28.0
    }
  ]
}
```

---

### Skater Statistics

#### Get Skater Summary
```
GET /skater/summary
```

**Query Parameters**:
- `cayenneExp` (string): Season filter
- `limit` (int): Number of results
- `sort` (string): Sort field (e.g., `points`, `goals`)
- `direction` (string): `ASC` or `DESC`

**Example**:
```python
url = "https://api.nhle.com/stats/rest/en/skater/summary"
params = {
    "cayenneExp": "seasonId=20252026",
    "limit": 50,
    "sort": "points",
    "direction": "DESC"
}
response = httpx.get(url, params=params)
skaters = response.json()
```

**Key fields**:
- `skaterFullName`, `playerId`, `teamAbbrevs`
- `gamesPlayed`, `goals`, `assists`, `points`
- `plusMinus`, `shots`, `shootingPct`
- `timeOnIcePerGame`, `powerPlayGoals`, `gameWinningGoals`

---

### Goalie Statistics

#### Get Goalie Summary
```
GET /goalie/summary
```

**Query Parameters**: Same as skater summary

**Example**:
```python
url = "https://api.nhle.com/stats/rest/en/goalie/summary"
params = {
    "cayenneExp": "seasonId=20252026",
    "limit": 50,
    "sort": "wins",
    "direction": "DESC"
}
response = httpx.get(url, params=params)
goalies = response.json()
```

**Key fields**:
- `goalieFullName`, `playerId`
- `gamesPlayed`, `gamesStarted`, `wins`, `losses`, `otLosses`
- `savePct`, `goalsAgainstAverage`
- `shutouts`, `saves`, `shotsAgainst`

---

## Common Patterns

### Caching Strategy
```python
from pathlib import Path
from datetime import datetime, timedelta
import json

CACHE_DIR = Path("data_files/cache")
CACHE_TTL = timedelta(minutes=5)

def get_cached_or_fetch(url: str) -> dict:
    cache_file = CACHE_DIR / f"{hash(url)}.json"
    
    if cache_file.exists():
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - mtime < CACHE_TTL:
            return json.loads(cache_file.read_text())
    
    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()
    data = response.json()
    
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(data))
    return data
```

### Error Handling
```python
import httpx
from typing import Optional

def safe_fetch(url: str) -> Optional[dict]:
    """Fetch with error handling."""
    try:
        response = httpx.get(url, timeout=30.0)
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException:
        print(f"Timeout fetching {url}")
        return None
    except httpx.HTTPStatusError as e:
        print(f"HTTP error {e.response.status_code} for {url}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

---

## Team Abbreviations

| Abbreviation | Team |
|--------------|------|
| ANA | Anaheim Ducks |
| ARI | Arizona Coyotes |
| BOS | Boston Bruins |
| BUF | Buffalo Sabres |
| CAR | Carolina Hurricanes |
| CBJ | Columbus Blue Jackets |
| CGY | Calgary Flames |
| CHI | Chicago Blackhawks |
| COL | Colorado Avalanche |
| DAL | Dallas Stars |
| DET | Detroit Red Wings |
| EDM | Edmonton Oilers |
| FLA | Florida Panthers |
| LAK | Los Angeles Kings |
| MIN | Minnesota Wild |
| MTL | Montreal Canadiens |
| NJD | New Jersey Devils |
| NSH | Nashville Predators |
| NYI | New York Islanders |
| NYR | New York Rangers |
| OTT | Ottawa Senators |
| PHI | Philadelphia Flyers |
| PIT | Pittsburgh Penguins |
| SEA | Seattle Kraken |
| SJS | San Jose Sharks |
| STL | St. Louis Blues |
| TBL | Tampa Bay Lightning |
| TOR | Toronto Maple Leafs |
| VAN | Vancouver Canucks |
| VGK | Vegas Golden Knights |
| WPG | Winnipeg Jets |
| WSH | Washington Capitals |

---

## Rate Limiting

The NHL API does not publish rate limits, but recommended practices:
- Cache responses aggressively
- Limit to ~30 requests/minute
- Add delays between batch requests
- Handle 429 errors gracefully

---

## Notes

⚠️ **These are unofficial APIs** - endpoints may change without notice. Monitor for breaking changes and have fallback logic.
