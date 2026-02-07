# Automated Odds Tracking

## Overview
This project uses GitHub Actions to automatically capture NHL betting odds every 4 hours, enabling line movement analysis without manual tracking.

## How It Works

### GitHub Action Workflow
**File**: `.github/workflows/capture-odds.yml`

- **Schedule**: Runs every 4 hours (1 AM, 5 AM, 9 AM, 1 PM, 5 PM, 9 PM UTC)
- **Manual Trigger**: Can be triggered manually via GitHub Actions tab
- **Process**:
  1. Fetches current odds from ESPN API (via DraftKings)
  2. Stores snapshots in `data_files/odds/` directory
  3. Commits and pushes changes automatically

### Odds Capture Script
**File**: `auto_capture_odds.py`

Captures odds for games scheduled within the next 3 days:
- **Moneyline**: Home/Away ML odds
- **Puck Line**: Home/Away spread odds (typically -1.5/+1.5)
- **Total**: Over/Under line and odds

### Data Storage Format
Odds are stored in JSON files:
```
data_files/odds/{game_id}.json
```

Each file contains:
- Game metadata (teams, game_id)
- Array of snapshots with timestamps
- Historical odds progression

Example:
```json
{
  "game_id": "401559123",
  "home_team": "TOR",
  "away_team": "BOS",
  "snapshots": [
    {
      "timestamp": "2026-02-06T15:00:00",
      "home_ml": -150,
      "away_ml": +130,
      "total": 6.5,
      "over_odds": -110,
      "under_odds": -110,
      "home_pl_odds": -110,
      "away_pl_odds": -110
    },
    {
      "timestamp": "2026-02-06T19:00:00",
      "home_ml": -145,
      "away_ml": +125,
      ...
    }
  ]
}
```

## Line Movement Analysis

The **📉 Line Movement** page uses this historical data to:
- Compare opening lines to current lines
- Identify sharp money indicators
- Detect reverse line movement
- Flag steam moves and significant shifts

## Benefits

✅ **No Manual Entry**: Odds automatically captured every 4 hours
✅ **Historical Tracking**: Build a database of line movements over time
✅ **Sharp Action Detection**: Identify when professional bettors are moving lines
✅ **Git History**: Full audit trail of all odds changes

## Setup

The GitHub Action is already configured and will run automatically. No additional setup required!

### Manual Trigger
1. Go to **Actions** tab in GitHub
2. Select **Capture NHL Odds** workflow
3. Click **Run workflow**

## Monitoring

Check the Actions tab to see:
- Latest run status
- Number of games captured
- Any errors or warnings

The workflow will show:
- ✅ Captured games with odds
- ⚠️  Skipped games (missing odds data)
- ℹ️  Info messages when no games are scheduled
