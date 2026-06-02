> **AI Onboarding Guide** — See also `.github/copilot-instructions.md` for full coding conventions.

# NHL Hockey Predictions — Site Summary

## What This App Does

Streamlit analytics platform for NHL sports betting. Predicts game outcomes (win probability, puck line, totals) using a blended xG model combining legacy Poisson and NHL analytics data. Features 11 pages covering today's games, team stats, standings, value finding, player props, goalie analysis, injuries, and backtesting.

## Quick Start

```bash
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1        # Windows
source .venv/bin/activate           # macOS/Linux

# 2. Run the app
streamlit run predictions.py
```

No manual data generation step needed — `NHLClient` fetches and caches data at startup.

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit ≥1.51 (`st.navigation` multi-page) |
| ML | xG models: legacy Poisson + analytics blend (50/50) |
| HTTP | `httpx` (async) |
| Data | pandas, NumPy, Parquet |
| Visualization | Plotly |
| Python | 3.13.7 |

## Key Files

| File | Purpose |
|---|---|
| `predictions.py` | Entry point — `st.set_page_config`, `apply_custom_css()`, sidebar logo, `st.navigation` |
| `pages/` | 11 pages (1_Todays_Games through 11_Backtesting) — **never** call `st.set_page_config` here |
| `src/api/nhl_client.py` | All NHL API calls with 5-min caching; includes `get_team_analytics()`, `get_goalie_analytics()` |
| `src/models/expected_goals.py` | Two xG paths: legacy Poisson and analytics-blended (XGBoost+NHL data) |
| `src/models/goalie_adjustment.py` | Goalie adjustment: GSAA + HD SV% + SV% (weights: 50/30/20) |
| `src/utils/styles.py` | `apply_custom_css()` — CSS only, no logo |
| `footer.py` | `add_betting_oracle_footer()` |
| `data_files/logo.png` | Sidebar logo |

## Data Flow

1. **Schedule**: `api-web.nhle.com/v1/schedule/{date}` → today's games
2. **Team analytics**: `api.nhle.com/stats/rest` → xGF, xGA, CF%, FF%, games played → cached per season
3. **Goalie analytics**: same endpoint → GSAA, HD save% → goalie adjustment
4. **xG prediction**: `calculate_expected_goals_with_analytics(home, away, home_analytics, away_analytics, analytics_weight=0.5)`
5. **Betting odds**: `NHLClient.get_espn_odds()` → DraftKings moneyline, spread, total (cached 5 min)
6. **Value finding**: model win% vs DK implied probability → edge per game

## xG Model Paths

```
Legacy path:    calculate_expected_goals(home, away)            → Poisson baseline
Analytics path: calculate_expected_goals_with_analytics(...)   → 50/50 blend with NHL xGF/xGA
```

`pages/4_Value_Finder.py` uses the analytics blend with graceful fallback to legacy.

## Environment Variables

No API keys required — NHL APIs are unofficial and public. ESPN odds endpoint is also public.

## External APIs & Rate Limits

| API | Notes |
|---|---|
| `api-web.nhle.com` | Unofficial NHL API; no key needed; can return HTTP 500 intermittently |
| `api.nhle.com/stats/rest` | NHL analytics; unofficial; intermittently returns HTTP 500 — always wrap in try/except |
| ESPN scores API | Public; used for betting odds via `NHLClient.get_espn_odds()` |

## Critical Conventions

- `st.set_page_config()` is called **only once** in `predictions.py` — never in page files
- `apply_custom_css()` and sidebar logo are rendered in `predictions.py` — never in page files
- `api.nhle.com/stats/rest` analytics endpoints **intermittently return HTTP 500** — always wrap in try/except with fallback
- Use `width='stretch'` for charts/dataframes — `use_container_width` is deprecated and removed
- Per-60 rates fall back to `timeOnIcePerGame × gamesPlayed` if season `timeOnIce` total is 0
- Build records list before calling `.sort_values()` — empty DataFrame has no columns → KeyError on sort

## Common Gotchas

- NHL APIs are unofficial — they may change without notice; check `nhl_client.py` if endpoints break
- `pages/11_Backtesting.py` exists but may be incomplete; verify before referencing
- The "Model" column in the Value Finder table shows `Legacy` or `Analytics` path used per prediction
