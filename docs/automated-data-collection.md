# Automated Data Collection

This document describes the automated data collection workflows that keep the app's data fresh without relying on on-demand user requests.

## Overview

The app uses GitHub Actions to automatically fetch and cache data on scheduled intervals:

1. **Daily Game Schedule Fetch** - Runs once per day (2 AM ET)
2. **4-Hour Odds Capture** - Runs 6 times per day to track line movement
3. **Weekly Model Retraining** - Runs weekly on Sundays (3 AM ET)
4. **Keep-Alive Ping** - Runs twice daily to prevent Streamlit app from sleeping

## Why Automated Collection?

**Problem**: When users access the app, game data is fetched on-demand. With multiple concurrent users, this causes:
- Duplicate API calls for the same data
- Rapid rate limit exhaustion
- Slower load times
- Potential service interruptions

**Solution**: Pre-fetch and cache game schedules nightly, so all users read from the same cached data.

## Daily Game Schedule Fetch

### Workflow: `.github/workflows/daily-game-fetch.yml`

**Schedule**: Daily at 7:00 AM UTC (2:00 AM ET)

**What it does**:
1. Fetches game schedules for the next 10 days
2. Caches them in `data_files/cache/`
3. Commits any changes to the repo

**Script**: `auto_fetch_games.py`

**Cache Duration**: 24 hours (schedules don't change frequently)

### Manual Trigger

You can manually trigger the workflow from GitHub Actions:
```bash
gh workflow run daily-game-fetch.yml
```

Or run locally:
```bash
python auto_fetch_games.py --days 10
```

## 4-Hour Odds Capture

### Workflow: `.github/workflows/capture-odds.yml`

**Schedule**: Every 4 hours at 1:00, 5:00, 9:00, 13:00, 17:00, 21:00 UTC

**What it does**:
1. Fetches current betting odds for the next 3 days
2. Saves snapshots to `data_files/odds/`
3. Tracks line movement over time
4. Commits changes to the repo

**Script**: `auto_capture_odds.py`

**Cache Duration**: 5 minutes (odds change frequently)

### Manual Trigger

```bash
python auto_capture_odds.py
```

## Weekly Model Retraining

### Workflow: `.github/workflows/weekly-model-retraining.yml`

**Schedule**: Weekly on Sundays at 8:00 AM UTC (3:00 AM ET)

**What it does**:
1. Fetches latest historical game data
2. Retrains the ML prediction models
3. Saves updated models to `data_files/models/`
4. Commits the new models to the repo

**Script**: `retrain_model.py`

## Keep-Alive Ping

### Workflow: `.github/workflows/keep-alive.yml`

**Schedule**: Twice daily at 9:00 AM and 9:00 PM UTC (4:00 AM and 4:00 PM ET)

**What it does**:
1. Sends HTTP request to Streamlit app URL
2. Prevents app from going to sleep on Streamlit Community Cloud
3. Logs response status

**Why**: Streamlit Community Cloud puts inactive apps to sleep after extended periods. Regular pings keep the app responsive.

### Configuration

Update the `STREAMLIT_APP_URL` in the workflow file:

```yaml
env:
  STREAMLIT_APP_URL: 'https://your-app-name.streamlit.app'
```

### Manual Trigger

Test the keep-alive ping:
```bash
curl https://your-app-name.streamlit.app
```

### Reusability

This workflow is designed to be easily copied to other Streamlit projects:
1. Copy `.github/workflows/keep-alive.yml` to your repository
2. Update the `STREAMLIT_APP_URL` environment variable
3. Adjust the schedule if needed (default: twice daily)

## Cache Strategy

### Schedule Data (24-hour TTL)
- **Purpose**: Game schedules for upcoming days
- **Cache Duration**: 24 hours
- **Update Frequency**: Daily at 2 AM ET
- **Why**: Schedules rarely change once published

### Odds Data (5-minute TTL)
- **Purpose**: Current betting lines
- **Cache Duration**: 5 minutes
- **Update Frequency**: Every 4 hours (snapshot storage)
- **Why**: Odds change frequently based on betting action

### Stats Data (5-minute TTL)
- **Purpose**: Team and player statistics
- **Cache Duration**: 5 minutes
- **Update Frequency**: On-demand
- **Why**: Stats update after each game

## NHLClient Implementation

The `NHLClient` class (`src/api/nhl_client.py`) handles caching with different TTLs:

```python
def __init__(self, cache_ttl_minutes: int = 5):
    self.cache_ttl = timedelta(minutes=cache_ttl_minutes)  # Stats, odds
    self.schedule_cache_ttl = timedelta(hours=24)  # Schedules
```

Schedule methods use the longer TTL:
```python
def get_schedule(self, game_date: str) -> dict:
    url = f"{self.BASE_WEB_API}/schedule/{game_date}"
    return self._fetch_sync(url, ttl=self.schedule_cache_ttl)
```

## Benefits

1. **Rate Limit Protection**: Pre-cached schedules prevent API overload
2. **Faster Load Times**: Users read from local cache instead of waiting for API calls
3. **Reliability**: App works even if external APIs are temporarily unavailable
4. **Line Movement Tracking**: 4-hour snapshots capture odds changes throughout the day
5. **Fresh Models**: Weekly retraining keeps predictions accurate
6. **Always Available**: Keep-alive pings ensure the app stays responsive 24/7

## Monitoring

Check GitHub Actions workflow runs:
- [Daily Game Fetch](../../actions/workflows/daily-game-fetch.yml)
- [Odds Capture](../../actions/workflows/capture-odds.yml)
- [Model Retraining](../../actions/workflows/weekly-model-retraining.yml)
- [Keep-Alive Ping](../../actions/workflows/keep-alive.yml)

## Troubleshooting

### Workflow Fails

If a workflow fails:
1. Check the Actions tab in GitHub
2. Review the error logs
3. Common issues:
   - API rate limits (wait and retry)
   - Network timeouts (transient, will retry next run)
   - Authentication issues (check GITHUB_TOKEN permissions)

### Stale Data

If data seems outdated:
1. Check the last workflow run time
2. Manually trigger the workflow
3. Verify cache file timestamps in `data_files/cache/`

### Cache Issues

Clear the cache if needed:
```bash
# Clear all cache
Remove-Item data_files/cache/*.json

# Clear only schedules
Remove-Item data_files/cache/api-web.nhle.com_v1_schedule_*.json
```

Then manually run the fetch script:
```bash
python auto_fetch_games.py --days 10
```
