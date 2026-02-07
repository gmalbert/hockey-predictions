"""Hockey Predictions - Streamlit Entry Point."""
import streamlit as st
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from src.api.nhl_client import NHLClient
from src.utils.styles import apply_custom_css
from footer import add_betting_oracle_footer

# Page configuration
st.set_page_config(
    page_title="Oracle on Ice - Hockey Predictions",
    page_icon="🏒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styling
apply_custom_css()

# Initialize client
@st.cache_resource
def get_client():
    return NHLClient()

client = get_client()

# Load logo
logo_path = Path("data_files/logo.png")
if logo_path.exists():
    st.sidebar.image(str(logo_path), width=150)

st.sidebar.title("Oracle on Ice - Hockey Predictions")
st.sidebar.markdown("NHL Betting Analytics")
st.sidebar.divider()

# Main content - Landing Page
st.title("🏒 Oracle on Ice - Hockey Predictions")
st.markdown("### Your Data-Driven Guide to NHL Betting")


# Hero section with key stats
st.divider()

try:
    # Get today's games for quick overview
    all_games = client.get_todays_games()
    # Filter for NHL regular season games only (game_type == 2)
    games = [game for game in all_games if game.get("game_type") == 2]
    games_count = len(games)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Games Today", games_count)
        if games_count > 0:
            st.caption("NHL matchups scheduled")

    with col2:
        st.metric("Live Data", "Active")
        st.caption("Real-time NHL stats")

    with col3:
        st.metric("Teams", "32")
        st.caption("NHL franchises")

except Exception as e:
    st.warning("Unable to load live data - check your connection")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Games Today", "—")
    with col2:
        st.metric("Live Data", "—")
    with col3:
        st.metric("Teams", "32")

st.divider()

# Feature cards
st.subheader("🎯 What We Offer")

# First row of features
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📅 Today's Games")
    st.markdown("""
    Complete schedule with live scores,
    betting odds, and game analysis.
    """)
    if st.button("View Games", key="games_btn"):
        st.switch_page("pages/1_📅_Todays_Games.py")

with col2:
    st.markdown("### 📊 Team Analytics")
    st.markdown("""
    Deep dive into team performance,
    recent form, and head-to-head matchups.
    """)
    if st.button("Explore Teams", key="teams_btn"):
        st.switch_page("pages/2_📊_Team_Stats.py")

with col3:
    st.markdown("### 🏆 League Standings")
    st.markdown("""
    Current NHL standings by division
    with key performance metrics.
    """)
    if st.button("View Standings", key="standings_btn"):
        st.switch_page("pages/3_🏆_Standings.py")

# Second row of features
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 💰 Value Finder")
    st.markdown("""
    Identify betting opportunities with
    statistical edge analysis.
    """)
    if st.button("Find Value", key="value_btn"):
        st.switch_page("pages/4_💰_Value_Finder.py")

with col2:
    st.markdown("### 🎯 Player Props")
    st.markdown("""
    Player performance tracking and
    prop betting insights.
    """)
    if st.button("Player Stats", key="props_btn"):
        st.switch_page("pages/5_🎯_Player_Props.py")

with col3:
    st.markdown("### 📈 Performance")
    st.markdown("""
    Track your betting results and
    monitor ROI over time.
    """)
    if st.button("View Performance", key="perf_btn"):
        st.switch_page("pages/6_📈_Performance.py")

# Third row of features
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🥅 Goalies")
    st.markdown("""
    Goalie performance analysis and
    matchup insights for betting.
    """)
    if st.button("Goalie Stats", key="goalies_btn"):
        st.switch_page("pages/7_🥅_Goalies.py")

with col2:
    st.markdown("### 🏥 Injuries")
    st.markdown("""
    Track player injuries and their
    impact on team performance.
    """)
    if st.button("Injury Report", key="injuries_btn"):
        st.switch_page("pages/8_🏥_Injuries.py")

with col3:
    st.markdown("### 📉 Line Movement")
    st.markdown("""
    Monitor odds changes and line
    movement throughout the day.
    """)
    if st.button("Line Movement", key="line_movement_btn"):
        st.switch_page("pages/9_📉_Line_Movement.py")

# Fourth row of features
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 Model Performance")
    st.markdown("""
    Detailed analysis of prediction
    model accuracy and metrics.
    """)
    if st.button("Model Stats", key="model_perf_btn"):
        st.switch_page("pages/10_📊_Model_Performance.py")

with col2:
    st.markdown("### 🔬 Backtesting")
    st.markdown("""
    Historical backtesting of betting
    strategies and performance.
    """)
    if st.button("Backtest", key="backtesting_btn"):
        st.switch_page("pages/11_🔬_Backtesting.py")



# Today's featured games (if available)
if 'games' in locals() and games:
    st.divider()
    st.subheader("🔥 Today's Matchups")

    # Show first 3 games as preview
    for i, game in enumerate(games[:3]):
        try:
            away_team = client.TEAM_NAMES.get(game.get("away_team", ""), game.get("away_team", ""))
            home_team = client.TEAM_NAMES.get(game.get("home_team", ""), game.get("home_team", ""))

            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{away_team} @ {home_team}**")
                if game.get("venue"):
                    st.caption(f"📍 {game.get('venue', '')}")

            with col2:
                game_state = game.get("game_state", "")
                if game_state == "LIVE":
                    st.markdown("🔴 **LIVE**")
                elif game_state == "FINAL":
                    home_score = game.get("home_score", 0)
                    away_score = game.get("away_score", 0)
                    st.markdown(f"**{away_score}-{home_score}**")
                else:
                    st.caption("Scheduled")

        except Exception as e:
            st.caption(f"Error loading game {i+1}")

    if len(games) > 3:
        st.caption(f"Plus {len(games) - 3} more games today")

    if st.button("See All Today's Games", key="all_games_btn"):
        st.switch_page("pages/1_📅_Todays_Games.py")

# Add footer to all pages
add_betting_oracle_footer()