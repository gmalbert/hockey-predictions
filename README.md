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
- **📊 Team Stats**: Detailed team performance, recent form, and season statistics
- **🏆 Standings**: League standings by division with rankings and key metrics
- **💰 Value Finder**: Identify betting opportunities with implied probabilities
- **🎯 Player Props**: Player performance tracking and prop betting analysis
- **📈 Performance**: Bet tracking and ROI analysis (framework ready)

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
