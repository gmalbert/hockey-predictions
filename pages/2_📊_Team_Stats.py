"""Team statistics and trends."""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.api.nhl_client import NHLClient
from footer import add_betting_oracle_footer

st.set_page_config(page_title="Oracle on Ice - Hockey Predictions", page_icon="📊", layout="wide")
st.title("📊 Team Statistics")

# Initialize client
@st.cache_resource
def get_client():
    return NHLClient()

client = get_client()

# Load logo
logo_path = Path("data_files/logo.png")
if logo_path.exists():
    st.sidebar.image(str(logo_path), width=150)

# Team selector - create list of (full name, abbreviation) tuples
team_options = [(client.TEAM_NAMES.get(abbr, abbr), abbr) for abbr in sorted(client.TEAM_NAMES.keys())]
team_names = [name for name, _ in team_options]
team_abbrevs = [abbr for _, abbr in team_options]

default_idx = team_abbrevs.index("TOR") if "TOR" in team_abbrevs else 0
selected_team_name = st.selectbox("Select Team", team_names, index=default_idx)
selected_team = team_abbrevs[team_names.index(selected_team_name)]

# Get team stats
try:
    team_stats = client.get_team_summary(selected_team)
    
    if team_stats:
        # Tabs for different stat views
        tab1, tab2, tab3 = st.tabs(["Overview", "Season Stats", "Recent Games"])
        
        with tab1:
            st.subheader(f"{team_stats.get('team_full_name', selected_team)} - Season Overview")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                record = f"{team_stats['wins']}-{team_stats['losses']}-{team_stats['ot_losses']}"
                st.metric("Record", record)
            with col2:
                st.metric("Points", team_stats['points'])
            with col3:
                st.metric("Goals For", team_stats['goals_for'])
            with col4:
                st.metric("Goals Against", team_stats['goals_against'])
            
            # Advanced stats
            st.divider()
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Goals/Game", f"{team_stats['goals_for_pg']:.2f}")
            with col2:
                st.metric("Goals Against/Game", f"{team_stats['goals_against_pg']:.2f}")
            with col3:
                st.metric("Power Play %", f"{team_stats['pp_pct']:.1%}")
            with col4:
                st.metric("Penalty Kill %", f"{team_stats['pk_pct']:.1%}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Shots For/Game", f"{team_stats['shots_for_pg']:.2f}")
            with col2:
                st.metric("Shots Against/Game", f"{team_stats['shots_against_pg']:.2f}")
        
        with tab2:
            st.subheader("Detailed Statistics")
            
            # Create stats dataframe
            stats_df = pd.DataFrame({
                "Category": [
                    "Games Played",
                    "Wins",
                    "Losses",
                    "OT Losses",
                    "Points",
                    "Goals For",
                    "Goals Against",
                    "Goal Differential",
                    "GF/Game",
                    "GA/Game",
                    "Power Play %",
                    "Penalty Kill %",
                    "Shots For/Game",
                    "Shots Against/Game"
                ],
                "Value": [
                    str(team_stats['games_played']),
                    str(team_stats['wins']),
                    str(team_stats['losses']),
                    str(team_stats['ot_losses']),
                    str(team_stats['points']),
                    str(team_stats['goals_for']),
                    str(team_stats['goals_against']),
                    str(team_stats['goals_for'] - team_stats['goals_against']),
                    f"{team_stats['goals_for_pg']:.2f}",
                    f"{team_stats['goals_against_pg']:.2f}",
                    f"{team_stats['pp_pct']:.1%}",
                    f"{team_stats['pk_pct']:.1%}",
                    f"{team_stats['shots_for_pg']:.2f}",
                    f"{team_stats['shots_against_pg']:.2f}"
                ]
            })
            
            st.dataframe(stats_df, width='stretch', hide_index=True)
        
        with tab3:
            st.subheader("Recent Games")
            
            # Get season games
            try:
                games = client.get_season_games(selected_team)
                
                if games:
                    # Take last 10 games
                    recent_games = games[-10:]
                    
                    games_df = pd.DataFrame([
                        {
                            "Date": g["date"][:10] if g.get("date") else "",
                            "Opponent": client.TEAM_NAMES.get(g["opponent"], g["opponent"]),
                            "Location": "Home" if g["home_away"] == "home" else "Away",
                            "Result": g["result"],
                            "Score": f"{g['team_score']}-{g['opponent_score']}"
                        }
                        for g in reversed(recent_games)
                    ])
                    
                    st.dataframe(games_df, width='stretch', hide_index=True)
                    
                    # Calculate recent record
                    wins = sum(1 for g in recent_games if g["result"] == "W")
                    losses = len(recent_games) - wins
                    st.info(f"Last {len(recent_games)} games: {wins}-{losses}")
                else:
                    st.info("No recent games data available.")
            except Exception as e:
                st.warning(f"Unable to load recent games: {e}")
    else:
        st.error(f"No stats available for {selected_team}")
        
except Exception as e:
    st.error(f"Error loading team stats: {e}")

# Add footer
add_betting_oracle_footer()
