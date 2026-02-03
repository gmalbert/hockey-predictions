"""Oracle on Ice - NHL Predictions Platform."""
import streamlit as st
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Oracle on Ice",
    page_icon="🏒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load logo
logo_path = Path("data_files/logo.png")
if logo_path.exists():
    st.sidebar.image(str(logo_path), width=150)

st.sidebar.title("Oracle on Ice")
st.sidebar.markdown("NHL Betting Analytics")
st.sidebar.divider()

# Main content
st.title("🏒 Oracle on Ice")
st.markdown("### NHL Predictions & Betting Analytics")

st.markdown("""
Welcome to **Oracle on Ice** - your data-driven guide to NHL betting insights.

**Key Features:**
- 📊 Advanced prediction models using expected goals (xG)
- 💰 Moneyline and puck line analysis
- 📈 Live line movement tracking
- 🥅 Goalie performance adjustments
- 🏥 Injury impact calculations
- 📈 Model evaluation with MAE metrics

---

#### Getting Started
1. Navigate to **Today's Games** for current matchups
2. Check **Value Finder** for bets with positive expected value
3. Monitor **Line Movement** for sharp action signals
4. Review **Performance** to track model accuracy

---
""")

# Placeholder metrics
st.subheader("Today's Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Games Today", "—", help="Number of NHL games scheduled")
with col2:
    st.metric("Value Bets", "—", help="Bets with positive expected value")
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

# Footer
st.markdown("---")
st.markdown("*Built with Streamlit • Data from NHL APIs • For entertainment purposes only*")