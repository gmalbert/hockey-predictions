# hockeyR Review: Ideas, Data Sources & Enhancement Opportunities

**Source:** https://hockeyr.netlify.app/ (R package by Daniel Morse)  
**GitHub:** https://github.com/danmorse314/hockeyR  
**Data Repo:** https://github.com/danmorse314/hockeyR-data  
**Models Repo:** https://github.com/danmorse314/hockeyR-models  

---

## What hockeyR Is

An R package that scrapes and cleans NHL play-by-play (PBP) event data from the NHL JSON API and hockey-reference.com. The key value is not the R package itself — **it's the pre-processed data it exposes and the modeling ideas behind it.**

Since our project is Python/Streamlit, we can't use the R package directly. However, most of the value is accessible through:
1. **hockeyR-data repo** — pre-built seasonal PBP CSV/Parquet files (no scraping needed)
2. **The NHL JSON API directly** — which hockeyR wraps and we already call
3. **hockey-reference.com** — which hockeyR scrapes and we could scrape ourselves with `httpx` + `BeautifulSoup`

---

## Key Gaps Identified in Our Current Project

Our models currently use aggregated season-level team stats only (goals/game, shots/game, PP%, PK%). The following are entirely absent:

- Shot-level event data (location, angle, distance)
- Any shot quality metric (xG per shot)
- On-ice stats (Corsi, Fenwick, zone entries)
- Player per-60 rate stats
- Goals Above Expected for players or goalies
- Historical data beyond current season (no backtesting with real shot data)

---

## High-Impact Opportunities

### 1. Shot-Level Play-by-Play Data (Biggest Opportunity)

**What hockeyR offers:** Pre-scraped PBP CSV files for every season back to 2010-11, available at the `hockeyR-data` GitHub repo. Each event row includes:

| Column | Value |
|--------|-------|
| `xg` | Expected goals probability for the shot (0–1) |
| `shot_distance` | Distance from goal in feet |
| `shot_angle` | Angle from the goal mouth in degrees |
| `x_fixed`, `y_fixed` | Coordinates, always oriented same direction |
| `event_type` | SHOT, MISSED_SHOT, GOAL, BLOCKED_SHOT, etc. |
| `strength_state` | 5v5, 5v4 (PP), 4v5 (SH), etc. |
| `event_player_1_name` | Shooter |
| `event_goalie_name` | Goalie facing the shot |
| Players on ice | 6 home + 6 away player columns |

**How to access in Python — zero R required:**
```python
# Pre-built CSVs are hosted directly on GitHub
import pandas as pd

season = "20252026"
url = f"https://raw.githubusercontent.com/danmorse314/hockeyR-data/main/data/{season}_pbp.csv.gz"
pbp = pd.read_csv(url, compression="gzip")
```

**What this unlocks for us:**
- Replace our aggregated-stat xG model with an actual shot-quality model
- Calculate rolling team xG for/against over last N games
- Calculate per-goalie expected goals against (for better goalie adjustment)
- Corsi% and Fenwick% at 5v5 as possession proxies

---

### 2. Improved xG Model Using Shot Features

**What hockeyR does:** Its xG model (described in the `hockeyR-models` repo) uses:
- Shot distance
- Shot angle
- Shot type (wrist, slap, tip, backhand, etc.)
- Whether it was a rush shot
- Whether it was a rebound
- Strength state (PP shots are weighted differently)

**Our current approach:** `xG = (home_offense + away_defense) / 2` — essentially just goals/shots per game averages.

**Suggested improvement:** Train a logistic regression or gradient boosting model on `hockeyR-data` historical PBP where the outcome is `1` (GOAL) or `0` (non-goal SHOT/MISSED_SHOT), with features: `shot_distance`, `shot_angle`, `shot_type`, `is_rebound`, `is_rush`, `strength_state`. This would produce a per-shot xG that is far more precise than what we have.

---

### 3. Goals Above Expected (GAX) / Goalie Saves Above Expected (GSAX)

**What hockeyR calculates:**
```r
GAX = actual_goals - sum(xg)         # skater
GSAX = sum(xg_against) - goals_against  # goalie
```

**Why it matters for betting:** A goalie with high GSAX is overperforming — they may regress. A team with consistently positive GAX (scoring above expected) likely has a shooting talent edge. These are regression signals that our current model completely ignores.

**Implementation idea:**
- Aggregate shot-level xG from `hockeyR-data` per goalie and per team
- Add GSAX column to our Goalies page (page 7)
- Flag goalies who are overperforming (likely regression = value on opponent)
- Add team GAX trend to Team Stats page

---

### 4. Hockey-Reference.com Data

**What hockeyR scrapes from hockey-reference.com that we don't have:**

| Metric | Use Case |
|--------|----------|
| Shots on goal per player | True shooting volume for props |
| Shooting % per player | Regression candidate detection |
| Per-60 rates (G/60, A/60, P/60) | Usage-adjusted player quality |
| Blocks, hits per player | Physical/defensive props |
| Faceoff win % | Zone starts and Corsi context |
| Even-strength vs power play splits | Line-adjust expected goals |
| Historical team records (back to 1918) | Deep backtesting data |

**Python scraping approach:** hockey-reference.com is accessible without an API key using `httpx` + `BeautifulSoup`. They have rate limiting but are publicly accessible. Alternatively, use their pre-built CSV exports.

**Suggested page additions:**
- Player Props page (page 5) could include shooting percentage regression flags
- Team Stats page (page 2) could show even-strength vs PP goal splits

---

### 5. Fenwick/Corsi from Play-by-Play

**What it is:**  
- **Corsi:** All shot attempts (goals + shots on goal + missed shots + blocked shots)  
- **Fenwick:** Unblocked shot attempts (goals + SOG + missed shots, excluding blocked)

Both are measured at 5v5 to isolate true possession quality.

**Current model gap:** Our model uses total shots/game, which is inflated by PP situations and doesn't reflect true 5v5 possession.

**Calculation from PBP data:**
```python
# From hockeyR-data PBP
fenwick_events = ["SHOT", "MISSED_SHOT", "GOAL"]
five_v_five = pbp[pbp["strength_state"] == "5v5"]
fenwick_for = five_v_five[five_v_five["event_team_abbr"] == team][
    five_v_five["event_type"].isin(fenwick_events)
].shape[0]
```

**Betting relevance:** Teams with higher 5v5 Fenwick% typically outperform over time — this is a cleaner signal than raw shot share.

---

### 6. Win Probability Model (In Progress in hockeyR)

**What hockeyR plans:** A real-time win probability model per play, inspired by `nflfastR`. Not yet shipped.

**Our current model:** Poisson distribution on seasonal xG averages — no in-game situational context.

**Opportunity:** Even without PBP, we could add a pre-game win probability calibration using:
- 5v5 Fenwick% (from PBP data)
- GSAX for starting goalie
- Recent form (rolling 10-game xG differential)
- Home/away splits

This would notably outperform our current Poisson-only approach.

---

### 7. Game Shift Data for Line Combinations

**What hockeyR exposes:** `get_game_shifts()` provides time-on-ice and line pairing data per game.

**Opportunity for Player Props page:** We don't currently model line context for player props (e.g., a center centering Auston Matthews is a vastly different prop than a fourth-line center). Shift data enables line combination detection.

---

## Data Source Summary

| Source | Access Method | What to Use |
|--------|--------------|-------------|
| `hockeyR-data` GitHub repo | Direct CSV download via `pandas.read_csv(url)` | Historical PBP, xG per shot (2010–present) |
| hockey-reference.com | `httpx` + `BeautifulSoup` | Skater/goalie advanced stats, per-60 rates, historical records |
| NHL JSON API (`api-web.nhle.com`) | Already implemented | Schedule, rosters, live scores |
| NHL Stats API (`api.nhle.com/stats/rest`) | Already implemented | Aggregated team/player stats |

---

## Suggested Implementation Priority

| Priority | Feature | Effort | Impact |
|----------|---------|--------|--------|
| 🔴 High | Download `hockeyR-data` PBP CSVs and build rolling team xGF/xGA | Medium | Very High |
| 🔴 High | Goalie GSAX from shot-level data (replace save% adjustment) | Medium | High |
| 🟡 Medium | Fenwick% at 5v5 to replace raw shots/game in model | Medium | High |
| 🟡 Medium | Scrape hockey-reference.com for per-60 skater stats (Player Props page) | Medium | Medium |
| 🟡 Medium | GAX per player for regression flags on Team Stats page | Medium | Medium |
| 🟢 Low | Shot map visualization using x_fixed/y_fixed coordinates | Low | Medium |
| 🟢 Low | Shooting % regression detection on Player Props | Low | Medium |
| 🟢 Low | Historical records from hockey-reference.com for deeper backtesting | High | Low |

---

## Quick Win: Rolling xGF/xGA from PBP CSV

The single easiest and highest-impact thing to adopt from hockeyR is replacing our season-average xG estimates with a **rolling 10-game xGF/xGA derived from actual shot data**. The pre-built CSVs already have `xg` per shot. We just need to:

1. Download current season PBP from `hockeyR-data` (one HTTP request)
2. Group by team and rolling 10-game window
3. Sum `xg` for and against at 5v5
4. Feed that into our existing Poisson model

This would make our predictions meaningfully more accurate with relatively low code change.

---

## Notes on hockeyR Models Repo

The [`hockeyR-models`](https://github.com/danmorse314/hockeyR-models) repo contains the full methodology for their xG model:
- Uses logistic regression
- Trained on ~10 seasons of shot data
- Features: shot distance, shot angle, shot type, rebound flag, rush flag
- Achieves AUC ~0.77 (typical for NHL xG models)

We could replicate this in Python using `scikit-learn` with the same feature set and training data from their CSV files — effectively porting their approach to our codebase.
