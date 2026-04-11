# Hockey Predictions - Copilot Instructions

## Project Overview
A Streamlit-based NHL analytics platform for sports betting insights. Uses Python 3.13.7 with data from unofficial NHL APIs.

## Tech Stack
- **Framework**: Streamlit (≥1.51, uses `st.navigation` multi-page pattern)
- **Python**: 3.13.7 (venv in `venv/`)
- **Data Sources**: `api-web.nhle.com`, `api.nhle.com/stats/rest`

## Project Structure
```
hockey-predictions/
├── predictions.py              # Streamlit entry point (st.navigation)
├── pages/                      # One file per page (NOT src/pages/)
│   ├── 1_Todays_Games.py
│   ├── 2_Team_Stats.py
│   ├── 3_Standings.py
│   ├── 4_Value_Finder.py
│   ├── 5_Player_Props.py
│   ├── 6_Performance.py
│   ├── 7_Goalies.py
│   ├── 8_Injuries.py
│   ├── 9_Line_Movement.py
│   ├── 10_Model_Performance.py
│   └── 11_Backtesting.py
├── src/
│   ├── api/
│   │   └── nhl_client.py       # API wrapper with caching
│   ├── models/
│   │   ├── expected_goals.py   # xG models (legacy + analytics blend)
│   │   └── goalie_adjustment.py
│   └── utils/
│       └── styles.py           # apply_custom_css() — CSS only, no logo
├── footer.py                   # add_betting_oracle_footer()
├── data_files/
│   ├── logo.png                # Sidebar logo
│   └── cache/                  # API response cache
└── tests/                      # pytest test suite
```

## Key Patterns

### Streamlit Entry Point
`predictions.py` uses `st.navigation` and **runs on every page navigation**. All global setup lives there:
- `st.set_page_config()` — called once here only
- `apply_custom_css()` — CSS injected here
- Sidebar logo (`st.sidebar.image`) — rendered here only

**Individual page files must NOT call `st.set_page_config`, `apply_custom_css`, or render the sidebar logo.** Doing so causes duplication on every page.

### API Calls
- Use `httpx` for async HTTP requests
- Cache responses in `data_files/cache/` to avoid rate limits
- Handle API failures gracefully — NHL APIs are unofficial
- ESPN odds API provides betting data for upcoming games
- `api.nhle.com/stats/rest` analytics endpoints intermittently return HTTP 500; always wrap in try/except with fallback

```python
# Example pattern for API calls
async def fetch_schedule(date: str) -> dict:
    url = f"https://api-web.nhle.com/v1/schedule/{date}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

### ESPN Odds Integration
- Use `NHLClient.get_espn_odds()` for betting odds
- Returns moneyline, spread, and total (over/under) from DraftKings
- Cached for 5 minutes like other API calls

### Prediction Models

Two xG model paths in `src/models/expected_goals.py`:
- `calculate_expected_goals(home, away)` — legacy Poisson formula
- `calculate_expected_goals_with_analytics(home, away, home_analytics, away_analytics, analytics_weight=0.5)` — 50/50 blend with NHL xGF/xGA

`pages/4_Value_Finder.py` uses the analytics blend with graceful fallback to legacy. A "Model" column in the predictions table shows which path was used.

Goalie adjustment in `src/models/goalie_adjustment.py`:
- `calculate_goalie_adjustment()` — legacy SV%
- `calculate_goalie_adjustment_with_analytics()` — GSAA + HD SV% + SV% (weights: 50/30/20)

### NHLClient Analytics Methods
- `get_team_analytics(season)` → dict keyed by team abbreviation with `xgf`, `xga`, `xgf_pct`, `cf_pct`, `ff_pct`, `games_played`
- `get_goalie_analytics(season, limit)` → list with `gsaa`, `hd_save_pct`
- `get_skater_analytics(season, limit)` → list with `g_per_60`, `a_per_60`, `p_per_60`, `toi_pg`
  - Per-60 rates fall back to `timeOnIcePerGame × gamesPlayed` if season `timeOnIce` total is 0

### Per-60 Rates (Player Props page)
Build the records list first, check for empty before calling `.sort_values()` — an empty `pd.DataFrame([])` has no columns and will raise `KeyError` on sort.

### Data Flow
1. API client fetches raw JSON → 2. Transform to pandas DataFrame → 3. Display via Streamlit

## Commands
```powershell
.\venv\Scripts\Activate.ps1          # Activate venv
pip install -r requirements.txt       # Install deps
streamlit run predictions.py         # Run app
pytest tests/ -v                     # Run tests
```

## Conventions
- Type hints on all function signatures
- Use `pathlib.Path` for file paths
- Store betting-relevant metrics in separate utility module
- Document API endpoints in `docs/api/`

## Betting Focus
Primary bet types: **Moneyline** and **Puck Line** (-1.5/+1.5)

Key prediction targets:
- Win probability (Poisson-based)
- Expected goals (xG) per team — analytics-blended preferred
- Puck line coverage probability
- MAE for goal predictions (target: < 1.2)

## Documentation Reference
| Doc | Purpose |
|-----|---------|
| `docs/roadmap/01-data-gathering.md` | NHL API client implementation |
| `docs/roadmap/02-modeling.md` | xG and prediction models |
| `docs/roadmap/06-goalie-analysis.md` | Goalie impact adjustments |
| `docs/roadmap/07-injury-tracking.md` | Injury data and impact |
| `docs/roadmap/08-line-movement.md` | Odds tracking |
| `docs/roadmap/09-model-evaluation.md` | MAE, accuracy metrics |
| `docs/features/betting-metrics.md` | ML/puck line formulas |
| `docs/api/nhl-api-reference.md` | API endpoint reference |
