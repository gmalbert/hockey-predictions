"""Hockey Predictions - Streamlit Entry Point."""
import streamlit as st
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Hockey Predictions",
    page_icon="🏒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load logo
logo_path = Path("data_files/logo.png")
if logo_path.exists():
    st.sidebar.image(str(logo_path), width=150)

st.sidebar.title("Hockey Predictions")
st.sidebar.markdown("NHL Betting Analytics")
st.sidebar.divider()
st.sidebar.markdown("""
**Navigation**
- 📅 Today's Games
- 🏆 Standings
- 📊 Team Stats
- 💰 Value Finder
- 🥅 Goalies
- 🏥 Injuries
- 📉 Line Movement
- 📈 Performance
""")

# Main content
st.title("🏒 Hockey Predictions")
st.markdown("### NHL Betting Analytics Platform")

st.markdown("""
Welcome to Hockey Predictions! This platform provides data-driven insights 
for NHL sports betting, focusing on **moneyline** and **puck line** analysis.

---

#### Quick Start
1. Check **Today's Games** for current matchups and predictions
2. Review **Value Finder** for bets with positive expected value
3. Monitor **Line Movement** for sharp action signals
4. Track **Performance** to validate model accuracy

---
""")

# Quick stats placeholder
st.subheader("Today's Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Games Today", "0", help="Number of NHL games scheduled")
with col2:
    st.metric("Value Bets", "0", help="Bets with positive expected value")
with col3:
    st.metric("Model Accuracy", "—", help="Last 30 days")
with col4:
    st.metric("MAE (Goals)", "—", help="Mean Absolute Error")

st.divider()

# System status
st.subheader("System Status")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Data Sources**")
    st.markdown("- 🟢 NHL Web API")
    st.markdown("- 🟢 NHL Stats API")

with col2:
    st.markdown("**Last Updated**")
    st.markdown("- Schedule: —")
    st.markdown("- Standings: —")
    st.markdown("- Odds: —")
