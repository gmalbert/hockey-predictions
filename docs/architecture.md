# Hockey Predictions — Architecture

## Overview
NHL analytics platform for sports betting insights. Multi-page Streamlit app using the unofficial NHL API for game data, xG models for predictions, and ESPN for odds.

## Data Flow
```
api-web.nhle.com (schedule, scores, rosters)
api.nhle.com/stats/rest (analytics: xGF, xGA, GSAA)
ESPN API (odds: moneyline, spread, total)
        ↓
src/api/nhl_client.py (httpx, 5-min cache)
        ↓
src/models/expected_goals.py
src/models/goalie_adjustment.py
        ↓
Streamlit pages → predictions.py (entry)
        ↓
data_files/best_bets_today.json (via scripts/export_best_bets.py)
```

## ML / Prediction Models
### Expected Goals (`src/models/expected_goals.py`)
Two paths:
- `calculate_expected_goals(home, away)` — legacy Poisson formula
- `calculate_expected_goals_with_analytics(home, away, analytics, weight=0.5)` — 50/50 blend with NHL `xGF`/`xGA`

### Goalie Adjustment (`src/models/goalie_adjustment.py`)
- `calculate_goalie_adjustment()` — legacy SV%
- `calculate_goalie_adjustment_with_analytics()` — GSAA (50%) + HD SV% (30%) + SV% (20%)

### NHLClient Analytics Methods
- `get_team_analytics(season)` → dict keyed by team abbr with `xgf`, `xga`, `xgf_pct`, `cf_pct`
- `get_goalie_analytics(season, limit)` → list with `gsaa`, `hd_save_pct`
- `get_skater_analytics(season, limit)` → per-60 rates (`g_per_60`, `a_per_60`, `toi_pg`)

## API Integrations
| Source | Purpose | Notes |
|--------|---------|-------|
| `api-web.nhle.com/v1` | Schedule, scores, teams | Public, unofficial |
| `api.nhle.com/stats/rest` | Analytics (xG, CF%, GSAA) | Intermittently 500s, always wrap in try/except |
| ESPN scoreboard | DraftKings odds | `NHLClient.get_espn_odds()` |

## Key Components
- `predictions.py` — entry, `st.set_page_config`, sidebar logo, `apply_custom_css()`
- `src/api/nhl_client.py` — all API calls with 5-min response cache
- `src/utils/styles.py` — `apply_custom_css()` (CSS only, no logo)
- `pages/` — 11 pages (Today, Team Stats, Standings, Value Finder, Player Props, Performance, Goalies, Injuries, Line Movement, Model Performance, Backtesting)
- `footer.py` — `add_betting_oracle_footer()`

## Pages Must NOT
- Call `st.set_page_config()` — only in `predictions.py`
- Call `apply_custom_css()` — only in `predictions.py`
- Render sidebar logo — only in `predictions.py`

## Storage
- `data_files/cache/` — API response cache
- `data_files/logo.png` — sidebar logo
- `data_files/best_bets_today.json` — Sports Picks Grid feed

## Per-60 Rates Defensive Pattern
Build records list first; check `if not records` before `pd.DataFrame(records).sort_values(...)` — empty DataFrame has no columns and raises `KeyError` on sort.
