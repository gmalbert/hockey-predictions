# UI Layout Roadmap

## Overview
Streamlit application structure and component design for the betting analytics platform.

---

## App Structure

### Main Entry Point
**File**: `src/app.py`

```python
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

# Main content
st.title("🏒 Today's Games")
st.markdown("Welcome to Hockey Predictions. Select a page from the sidebar to get started.")

# Quick stats placeholder
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Games Today", "0", help="Number of NHL games scheduled")
with col2:
    st.metric("Value Bets", "0", help="Bets with positive expected value")
with col3:
    st.metric("Model Accuracy", "0%", help="Last 30 days")
with col4:
    st.metric("ROI", "0%", help="Hypothetical returns")
```

---

## Phase 1: Core Pages

### Task 1.1: Daily Games Dashboard
**File**: `src/pages/1_📅_Todays_Games.py`

```python
"""Today's games with predictions and betting value."""
import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Today's Games", page_icon="📅", layout="wide")
st.title("📅 Today's Games")

# Date selector
selected_date = st.date_input("Select Date", value=date.today())

# Placeholder for games data
# TODO: Replace with actual API call
games_data = [
    {
        "Time": "7:00 PM",
        "Away": "TOR",
        "Home": "MTL",
        "Away xG": 2.8,
        "Home xG": 3.1,
        "Home Win %": "54%",
        "Total": 5.9,
        "Value": "✅ Home ML"
    },
]

if games_data:
    df = pd.DataFrame(games_data)
    
    # Styled dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Value": st.column_config.TextColumn(
                "Value Bet",
                help="Identified betting value"
            )
        }
    )
else:
    st.info("No games scheduled for this date.")

# Expandable game details
st.subheader("Game Details")
with st.expander("TOR @ MTL - 7:00 PM", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Toronto Maple Leafs")
        st.write("**Record:** 30-15-5")
        st.write("**Last 10:** 7-2-1")
        st.write("**Goals/Game:** 3.4")
        st.write("**Goals Against:** 2.8")
    
    with col2:
        st.markdown("### Montreal Canadiens")
        st.write("**Record:** 22-25-3")
        st.write("**Last 10:** 4-5-1")
        st.write("**Goals/Game:** 2.9")
        st.write("**Goals Against:** 3.3")
```

### Task 1.2: Team Analysis Page
**File**: `src/pages/2_📊_Team_Stats.py`

```python
"""Team statistics and trends."""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Team Stats", page_icon="📊", layout="wide")
st.title("📊 Team Statistics")

# Team selector
teams = ["ANA", "ARI", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL", "DAL",
         "DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NJD", "NSH", "NYI", "NYR",
         "OTT", "PHI", "PIT", "SEA", "SJS", "STL", "TBL", "TOR", "VAN", "VGK",
         "WPG", "WSH"]

selected_team = st.selectbox("Select Team", teams, index=teams.index("TOR"))

# Tabs for different stat views
tab1, tab2, tab3 = st.tabs(["Overview", "Trends", "Situational"])

with tab1:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Record", "30-15-5", "+5 vs last season")
    with col2:
        st.metric("Goals/Game", "3.4", "+0.3")
    with col3:
        st.metric("xG Differential", "+0.6", "League rank: 5th")

with tab2:
    st.subheader("Last 10 Games")
    # Placeholder chart
    st.line_chart({"Goals For": [3, 2, 4, 5, 2, 3, 4, 2, 3, 4],
                   "Goals Against": [2, 3, 2, 1, 4, 2, 3, 3, 2, 2]})

with tab3:
    st.subheader("Situational Stats")
    situational = pd.DataFrame({
        "Situation": ["Home", "Away", "Favorite", "Underdog", "Back-to-Back"],
        "Record": ["18-6-2", "12-9-3", "25-10-3", "5-5-2", "4-3-1"],
        "GF/G": [3.6, 3.1, 3.5, 2.9, 2.8],
        "GA/G": [2.5, 3.1, 2.7, 3.0, 3.4]
    })
    st.dataframe(situational, use_container_width=True, hide_index=True)
```

### Task 1.3: Standings Page
**File**: `src/pages/3_🏆_Standings.py`

```python
"""League standings with betting context."""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Standings", page_icon="🏆", layout="wide")
st.title("🏆 NHL Standings")

# Division tabs
tab1, tab2, tab3, tab4 = st.tabs(["Atlantic", "Metropolitan", "Central", "Pacific"])

# Placeholder standings
standings_columns = ["Team", "GP", "W", "L", "OTL", "PTS", "GF", "GA", "DIFF", "L10"]

with tab1:
    atlantic = pd.DataFrame({
        "Team": ["TOR", "FLA", "BOS", "TBL", "DET", "BUF", "OTT", "MTL"],
        "GP": [50] * 8,
        "W": [30, 29, 27, 25, 22, 20, 18, 15],
        "L": [15, 16, 18, 20, 23, 25, 27, 30],
        "OTL": [5, 5, 5, 5, 5, 5, 5, 5],
        "PTS": [65, 63, 59, 55, 49, 45, 41, 35],
        "GF": [170, 165, 155, 150, 140, 135, 130, 120],
        "GA": [140, 145, 145, 155, 160, 165, 175, 185],
        "DIFF": [30, 20, 10, -5, -20, -30, -45, -65],
        "L10": ["7-2-1", "6-3-1", "5-4-1", "6-3-1", "4-5-1", "3-6-1", "3-6-1", "2-7-1"]
    })
    st.dataframe(atlantic, use_container_width=True, hide_index=True)
```

---

## Phase 2: Betting-Specific Pages

### Task 2.1: Value Finder
**File**: `src/pages/4_💰_Value_Finder.py`

```python
"""Identify bets with positive expected value."""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Value Finder", page_icon="💰", layout="wide")
st.title("💰 Value Finder")

st.markdown("""
Find bets where the model's probability exceeds the implied odds.
A **positive edge** suggests potential value.
""")

# Filters
col1, col2, col3 = st.columns(3)
with col1:
    min_edge = st.slider("Minimum Edge %", 0, 20, 3)
with col2:
    bet_types = st.multiselect("Bet Types", ["Moneyline", "Puck Line", "Totals"], default=["Moneyline"])
with col3:
    confidence = st.selectbox("Model Confidence", ["All", "High", "Medium", "Low"])

# Value bets table
st.subheader("Today's Value Bets")

value_bets = pd.DataFrame({
    "Game": ["TOR @ MTL", "BOS @ NYR", "COL @ VGK"],
    "Bet": ["MTL ML", "Under 6.0", "COL -1.5"],
    "Odds": ["+125", "-110", "+145"],
    "Model Prob": ["48%", "58%", "42%"],
    "Implied": ["44%", "52%", "41%"],
    "Edge": ["+4.0%", "+6.0%", "+1.0%"],
    "Kelly": ["2.1%", "3.2%", "0.5%"]
})

# Highlight positive edges
st.dataframe(
    value_bets,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Edge": st.column_config.TextColumn("Edge", help="Model probability minus implied probability")
    }
)
```

### Task 2.2: Props Analysis (Future)
**File**: `src/pages/5_🎯_Player_Props.py`

```python
"""Player prop betting analysis."""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Player Props", page_icon="🎯", layout="wide")
st.title("🎯 Player Props Analysis")

# Player search
player_search = st.text_input("Search Player", placeholder="Enter player name...")

# Prop type selector
prop_type = st.selectbox("Prop Type", ["Goals", "Assists", "Points", "Shots on Goal", "Saves"])

st.subheader(f"Top {prop_type} Props for Today")

# Placeholder data
props_data = pd.DataFrame({
    "Player": ["A. Matthews", "C. McDavid", "N. Kucherov"],
    "Team": ["TOR", "EDM", "TBL"],
    "Matchup": ["@ MTL", "vs CGY", "@ FLA"],
    "Line": [0.5, 0.5, 1.5],
    "Over Odds": ["-140", "-130", "+120"],
    "Model O%": ["62%", "58%", "48%"],
    "Edge": ["+5%", "+3%", "-2%"]
})

st.dataframe(props_data, use_container_width=True, hide_index=True)
```

---

## Phase 3: Tracking & Performance

### Task 3.1: Bet Tracker
**File**: `src/pages/6_📈_Performance.py`

```python
"""Track betting performance and ROI."""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Performance", page_icon="📈", layout="wide")
st.title("📈 Performance Tracker")

# Summary metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Bets", "156")
with col2:
    st.metric("Win Rate", "54.5%", "+2.3%")
with col3:
    st.metric("Units Profit", "+12.4", "+3.2 this week")
with col4:
    st.metric("ROI", "+7.9%", "+1.1%")

# Performance chart
st.subheader("Cumulative Profit")
st.line_chart({"Units": [0, 1, -0.5, 2, 1.5, 3, 4, 3.5, 5, 6, 5.5, 7, 8, 9, 10, 12, 12.4]})

# Bet history
st.subheader("Recent Bets")
history = pd.DataFrame({
    "Date": ["2026-02-01", "2026-02-01", "2026-01-31"],
    "Game": ["TOR @ MTL", "BOS @ NYR", "COL vs VGK"],
    "Bet": ["TOR ML", "Under 6.0", "COL -1.5"],
    "Odds": ["-150", "-110", "+145"],
    "Stake": ["1u", "1u", "0.5u"],
    "Result": ["✅ Won", "❌ Lost", "✅ Won"],
    "Profit": ["+0.67u", "-1.0u", "+0.73u"]
})
st.dataframe(history, use_container_width=True, hide_index=True)
```

---

## Styling & Components

### Custom CSS
**File**: `src/utils/styles.py`

```python
"""Custom Streamlit styling."""
import streamlit as st

def apply_custom_css():
    """Apply custom CSS styles."""
    st.markdown("""
        <style>
        /* Value bet highlighting */
        .positive-edge {
            background-color: #d4edda;
            border-left: 4px solid #28a745;
            padding: 10px;
            margin: 5px 0;
        }
        
        /* Metric cards */
        div[data-testid="metric-container"] {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
        }
        
        /* Team colors (example) */
        .team-tor { color: #00205B; }
        .team-mtl { color: #AF1E2D; }
        </style>
    """, unsafe_allow_html=True)
```

---

## Next Steps
- See [04-short-term.md](04-short-term.md) for MVP priorities
- See [05-long-term.md](05-long-term.md) for future features
