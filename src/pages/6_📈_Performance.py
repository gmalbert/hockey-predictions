"""Track betting performance and ROI."""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys
import random

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.api.nhl_client import NHLClient
from footer import add_betting_oracle_footer

st.set_page_config(page_title="Performance", page_icon="📈", layout="wide")
st.title("📈 Performance Tracker")

st.info("🚧 Performance tracking coming in Phase 3. This page shows placeholder data for UI demonstration.")

# Initialize client
@st.cache_resource
def get_client():
    return NHLClient()

client = get_client()

# Summary metrics
st.subheader("Betting Performance Summary")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Bets", "156", help="Total number of tracked bets")
with col2:
    st.metric("Win Rate", "54.5%", "+2.3%", help="Percentage of winning bets")
with col3:
    st.metric("Units Profit", "+12.4", "+3.2 this week", help="Total units won/lost")
with col4:
    st.metric("ROI", "+7.9%", "+1.1%", help="Return on investment")

# Performance chart
st.subheader("Cumulative Profit (Units)")

# Generate sample data
dates = [(datetime.now() - timedelta(days=x)) for x in range(30, 0, -1)]
cumulative_profit = []
profit = 0
for i in range(30):
    profit += random.uniform(-0.5, 1.0)
    cumulative_profit.append(profit)

chart_df = pd.DataFrame({
    "Date": dates,
    "Units": cumulative_profit
})

st.line_chart(chart_df.set_index("Date"))

# Breakdown by bet type
st.divider()
st.subheader("Performance by Bet Type")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Moneyline**")
    st.metric("Bets", "82")
    st.metric("Win Rate", "56.1%")
    st.metric("ROI", "+9.2%")

with col2:
    st.markdown("**Puck Line**")
    st.metric("Bets", "54")
    st.metric("Win Rate", "51.9%")
    st.metric("ROI", "+4.3%")

with col3:
    st.markdown("**Totals**")
    st.metric("Bets", "20")
    st.metric("Win Rate", "55.0%")
    st.metric("ROI", "+11.5%")

# Bet history
st.divider()
st.subheader("Recent Bets")

# Generate sample bet history
history = pd.DataFrame({
    "Rank": range(1, 11),
    "Date": [
        "2026-02-04",
        "2026-02-03",
        "2026-02-03",
        "2026-02-02",
        "2026-02-02",
        "2026-02-01",
        "2026-02-01",
        "2026-01-31",
        "2026-01-31",
        "2026-01-30"
    ],
    "Game": [
        f"{client.TEAM_NAMES.get('TOR', 'TOR')} @ {client.TEAM_NAMES.get('MTL', 'MTL')}",
        f"{client.TEAM_NAMES.get('BOS', 'BOS')} @ {client.TEAM_NAMES.get('NYR', 'NYR')}",
        f"{client.TEAM_NAMES.get('COL', 'COL')} vs {client.TEAM_NAMES.get('VGK', 'VGK')}",
        f"{client.TEAM_NAMES.get('EDM', 'EDM')} @ {client.TEAM_NAMES.get('CGY', 'CGY')}",
        f"{client.TEAM_NAMES.get('FLA', 'FLA')} vs {client.TEAM_NAMES.get('TBL', 'TBL')}",
        f"{client.TEAM_NAMES.get('CHI', 'CHI')} @ {client.TEAM_NAMES.get('DET', 'DET')}",
        f"{client.TEAM_NAMES.get('SEA', 'SEA')} vs {client.TEAM_NAMES.get('LAK', 'LAK')}",
        f"{client.TEAM_NAMES.get('PIT', 'PIT')} @ {client.TEAM_NAMES.get('WSH', 'WSH')}",
        f"{client.TEAM_NAMES.get('NJD', 'NJD')} vs {client.TEAM_NAMES.get('PHI', 'PHI')}",
        f"{client.TEAM_NAMES.get('DAL', 'DAL')} @ {client.TEAM_NAMES.get('MIN', 'MIN')}"
    ],
    "Bet": [
        "TOR ML",
        "Under 6.0",
        "COL -1.5",
        "EDM ML",
        "Over 6.5",
        "DET ML",
        "Under 5.5",
        "WSH -1.5",
        "PHI ML",
        "Over 6.0"
    ],
    "Odds": [
        "-150",
        "-110",
        "+145",
        "+120",
        "-105",
        "-135",
        "+100",
        "+160",
        "-125",
        "-115"
    ],
    "Stake": [
        "1.0u",
        "1.0u",
        "0.5u",
        "1.0u",
        "1.0u",
        "1.5u",
        "1.0u",
        "0.5u",
        "1.0u",
        "1.0u"
    ],
    "Result": [
        "⏳ Pending",
        "✅ Won",
        "❌ Lost",
        "✅ Won",
        "✅ Won",
        "❌ Lost",
        "✅ Won",
        "❌ Lost",
        "✅ Won",
        "❌ Lost"
    ],
    "Profit": [
        "—",
        "+0.91u",
        "-0.50u",
        "+1.20u",
        "+0.95u",
        "-1.50u",
        "+1.00u",
        "-0.50u",
        "+0.80u",
        "-1.00u"
    ]
})

st.dataframe(
    history,
    width='stretch',
    hide_index=True,
    column_config={
        "Rank": st.column_config.NumberColumn("#", width="small"),
        "Date": st.column_config.TextColumn("Date", width="small"),
        "Game": st.column_config.TextColumn("Matchup", width="large"),
        "Bet": st.column_config.TextColumn("Bet Type", width="small"),
        "Odds": st.column_config.TextColumn("Odds", width="small"),
        "Stake": st.column_config.TextColumn("Stake (Units)", width="small"),
        "Result": st.column_config.TextColumn("Result", width="small"),
        "Profit": st.column_config.TextColumn("Profit/Loss", width="small"),
    }
)

# Monthly breakdown
st.divider()
st.subheader("Monthly Performance")

monthly = pd.DataFrame({
    "Month": ["February 2026", "January 2026", "December 2025", "November 2025"],
    "Bets": [15, 68, 52, 21],
    "Win Rate": ["53.3%", "55.9%", "53.8%", "52.4%"],
    "Units": ["+2.4", "+5.1", "+3.8", "+1.1"],
    "ROI": ["+8.1%", "+7.5%", "+7.3%", "+5.2%"]
})

st.dataframe(monthly, width='stretch', hide_index=True)

# Implementation notes
st.divider()
st.info("""
**Coming in Phase 3:**
- Manual bet entry form
- Automatic result tracking via API
- Advanced analytics (by team, league, bet type)
- Bankroll management tools
- Export to CSV/Excel
- Custom date range filtering
""")

# Add footer
add_betting_oracle_footer()
