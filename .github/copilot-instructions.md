# Hockey Predictions - Copilot Instructions

## Project Overview
A Streamlit-based NHL analytics platform for sports betting insights. Uses Python 3.13.7 with data from unofficial NHL APIs.

## Tech Stack
- **Framework**: Streamlit
- **Python**: 3.13.7 (venv in `venv/`)
- **Data Sources**: `api-web.nhle.com`, `api.nhle.com/stats/rest`

## Project Structure
```
hockey-predictions/
├── src/
│   ├── app.py              # Streamlit entry point
│   ├── api/                # NHL API client modules
│   │   └── nhl_client.py   # API wrapper with caching
│   ├── models/             # Prediction/ML models
│   └── utils/              # Helpers (dates, formatting)
├── data_files/             # Static assets, cached data
├── docs/                   # Roadmaps and documentation
└── tests/                  # pytest test suite
```

## Key Patterns

### API Calls
- Use `httpx` for async HTTP requests
- Cache responses in `data_files/cache/` to avoid rate limits
- Handle API failures gracefully - NHL APIs are unofficial

```python
# Example pattern for API calls
async def fetch_schedule(date: str) -> dict:
    url = f"https://api-web.nhle.com/v1/schedule/{date}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

### Streamlit Components
- One page per file in `src/pages/`
- Use `st.cache_data` for API responses (TTL: 5 min for live data)
- Use `st.cache_resource` for model loading

### Data Flow
1. API client fetches raw JSON → 2. Transform to pandas DataFrame → 3. Display via Streamlit

## Commands
```powershell
.\venv\Scripts\Activate.ps1          # Activate venv
pip install -r requirements.txt       # Install deps
streamlit run src/app.py              # Run app
pytest tests/ -v                      # Run tests
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
- Expected goals (xG) per team
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
