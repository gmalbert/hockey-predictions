<p align="center">
  <img src="data_files/logo.png" width="200" alt="Oracle on Ice Logo">
</p>

# Hockey Predictions

A Streamlit-powered analytics platform designed to provide data-driven insights for NHL sports betting. This application aggregates real-time and historical NHL data to help bettors make informed decisions.

## 🎯 Purpose

This application aims to:

- **Aggregate NHL Data**: Pull comprehensive statistics from the NHL API including team records, player performance, and game outcomes
- **Identify Betting Value**: Surface statistical edges and trends that bookmakers may undervalue
- **Visualize Patterns**: Display historical performance, head-to-head matchups, and situational trends
- **Track Performance**: Monitor prediction accuracy and betting ROI over time

## 🏒 Data Sources

| Source | Description |
|--------|-------------|
| `api-web.nhle.com` | Game schedules, scores, player stats |
| `api.nhle.com/stats/rest` | Advanced team and player statistics |
| `site.api.espn.com` | Live betting odds and lines |

## 📊 Key Features

- **📅 Today's Games**: Daily NHL matchups with real-time odds and betting insights
- **📊 Team Stats**: Detailed team performance, recent form, and season statistics with advanced analytics (xGF%, CF%, FF%)
- **🏆 Standings**: League standings by division with rankings and key metrics
- **💰 Value Finder**: Identifies betting opportunities using an analytics-blended xG model (falls back to legacy on API failure)
- **🎯 Player Props**: Per-60 rate leaders, shooting% regression watch, player performance tracking
- **📈 Performance**: Bet tracking and ROI analysis (framework ready)
- **🥅 Goalies**: Goalie matchup comparison with GSAA, HD SV%, and xG adjustments
- **🏥 Injuries**: Injury report with positional impact scoring
- **📉 Line Movement**: Moneyline and total movement tracking with sharp-action signals
- **📊 Model Performance**: Prediction accuracy metrics and model diagnostics
- **🔬 Backtesting**: Historical model validation simulator

## 🧠 Prediction Models

### Expected Goals (xG)
Two model paths with automatic fallback:
- **Analytics blend** (`calculate_expected_goals_with_analytics`): 50/50 blend of raw goals-per-game and NHL xGF/xGA data from `api.nhle.com/stats/rest`
- **Legacy** (`calculate_expected_goals`): Poisson-based goals-per-game formula

The Value Finder page displays which model path was used for each game prediction.

### Goalie Adjustment
- Legacy: Season SV% adjustment
- Analytics-enhanced: GSAA + HD SV% + SV% weighted blend (50/30/20)

### Per-60 Rates
Player production normalised by ice time. Falls back to `timeOnIcePerGame × gamesPlayed` when season totals are unavailable from the API.

## 🏗️ Architecture

`predictions.py` is the single Streamlit entry point using `st.navigation`. It runs on every page navigation, so global setup (CSS, sidebar logo) lives there — **individual page files must not duplicate these calls**.

## 🚀 Quick Start

### Local Development

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows
# or
source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run predictions.py
```

### Deployment

For Streamlit Cloud or other remote deployments, set the main file to:
```
predictions.py
```

## 📖 Documentation

See the [docs/roadmap/](docs/roadmap/) folder for detailed development plans and implementation status.

---

*Built with Python 3.13 and Streamlit*
