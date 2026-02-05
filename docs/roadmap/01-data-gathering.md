# Data Gathering Roadmap

## Overview
This document outlines the strategy for collecting NHL data from unofficial APIs to power betting analytics.

**Status**: ✅ **COMPLETED** - All tasks implemented and tested

---

## Phase 1: Core API Client Setup ✅

### Task 1.1: Create Base HTTP Client ✅
**Status**: ✅ COMPLETED  
**File**: `src/api/nhl_client.py`

**Implementation Notes**:
- Using synchronous `httpx.get()` with `follow_redirects=True` for Streamlit compatibility
- Cache implementation using `_fetch_sync()` method with 5-minute TTL
- All core methods implemented and tested
- Team ID to abbreviation mapping added for proper team lookup

**Key Features**:
- Automatic redirect handling for NHL API endpoints
- File-based caching in `data_files/cache/`
- 30-second timeout for requests
- Error handling for HTTP errors and timeouts

### Task 1.2: Create Synchronous Wrapper for Streamlit ✅
**Status**: ✅ NOT NEEDED - Using synchronous client directly

**Implementation Notes**:
- Using synchronous `httpx.get()` with `follow_redirects=True` for Streamlit compatibility
- Cache implementation using `_fetch_sync()` method with 5-minute TTL
- All core methods implemented and tested
- Team ID to abbreviation mapping added for proper team lookup

**Key Features**:
- Automatic redirect handling for NHL API endpoints
- File-based caching in `data_files/cache/`
- 30-second timeout for requests
- Error handling for HTTP errors and timeouts

### Task 1.2: Create Synchronous Wrapper for Streamlit ✅
**Status**: ✅ NOT NEEDED - Using synchronous client directly

**Rationale**: The NHLClient uses synchronous httpx calls directly, which work perfectly with Streamlit without needing async wrapper functions.

---

## Phase 2: Essential Data Endpoints ✅

### Task 2.1: Today's Schedule ✅
**Status**: ✅ COMPLETED  
**Method**: `get_todays_games()`

Fetches all games for betting analysis with key information:
- Game ID, start time, teams, scores
- Game state (live, final, scheduled)
- Venue information

**Tested**: ✅ Returns 17+ games for current date

### Task 2.2: Team Statistics ✅
**Status**: ✅ COMPLETED  
**Methods**: `get_team_stats()`, `get_team_summary()`

Key metrics for moneyline and puck line analysis:
- Win/loss records, points
- Goals for/against per game
- Power play and penalty kill percentages
- Shots for/against per game

**Tested**: ✅ Successfully retrieves all 32 NHL teams

**Implementation Notes**:
- Uses team ID mapping (TEAM_ID_MAP) to convert abbreviations to IDs
- Stats API uses teamId not teamAbbrev in responses
- Returns comprehensive stats dictionary per team

### Task 2.3: Player Statistics (for Props) ✅
**Status**: ✅ COMPLETED  
**Methods**: `get_skater_stats()`, `get_goalie_stats()`

Individual player data for prop bets:
- Skaters: goals, assists, points, shots, TOI
- Goalies: wins, save %, GAA, shutouts

**Tested**: ✅ Returns top 100 skaters and 50 goalies

---

## Phase 3: Historical Data Collection ✅

### Task 3.1: Game Results History ✅
**Status**: ✅ COMPLETED  
**Methods**: `get_team_schedule()`, `get_season_games()`

Store historical outcomes for backtesting:
- All completed games for a team in a season
- Game results (W/L), scores, home/away designation
- Date and opponent information

**Tested**: ✅ Returns 60+ completed games for current season

**Implementation Notes**:
- Filters for games with state "OFF" or "FINAL"
- Properly handles home vs away team perspective
- Returns structured game dictionaries ready for analysis

### Task 3.2: Cache Management Utility ✅
**Status**: ✅ COMPLETED  
**File**: `src/utils/cache.py`

Cache management functions:
- `clear_old_cache(max_age_hours)` - Remove old cache files
- `get_cache_size_mb()` - Get total cache size
- `clear_all_cache()` - Remove all cached data

**Also integrated into NHLClient**:
- `client.clear_cache(max_age_hours)`
- `client.get_cache_size_mb()`

**Tested**: ✅ Successfully manages cache directory

---

## Additional Implemented Features ✅

### ESPN Odds Integration ✅
**Method**: `get_espn_odds(days_ahead=7)`

Retrieves betting odds from ESPN API:
- Moneyline odds (home/away)
- Point spread (puck line)
- Total (over/under)
- Multiple provider support (DraftKings, etc.)

**Tested**: ✅ Returns odds for 14+ upcoming games

### Standings Endpoint ✅
**Method**: `get_standings()`

Current league standings with:
- Team records and points
- Division/conference rankings
- Handles API redirects properly

**Tested**: ✅ Returns all 32 teams with standings data

---

## Testing Summary

All roadmap tasks have been implemented and verified working:

```
✅ Phase 1: Core API Client Setup
  ✅ Task 1.1: Base HTTP Client
  ✅ Task 1.2: Synchronous Wrapper (not needed)

✅ Phase 2: Essential Data Endpoints
  ✅ Task 2.1: Today's Schedule (17 games)
  ✅ Task 2.2: Team Statistics (32 teams)
  ✅ Task 2.3: Player Statistics (100+ players)

✅ Phase 3: Historical Data Collection
  ✅ Task 3.1: Game Results History (60+ games/team)
  ✅ Task 3.2: Cache Management Utility

✅ Additional Features
  ✅ ESPN Odds Integration
  ✅ Goalie Statistics
  ✅ HTTP Redirect Handling
```

**Test Script**: `test_roadmap.py` - Comprehensive validation of all endpoints

---

## Next Steps
- See [02-modeling.md](02-modeling.md) for prediction model development
- See [nhl-api-reference.md](../api/nhl-api-reference.md) for complete endpoint documentation
