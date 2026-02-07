"""League standings with betting context."""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.api.nhl_client import NHLClient
from footer import add_betting_oracle_footer

st.set_page_config(page_title="Oracle on Ice - Hockey Predictions", page_icon="🏆", layout="wide")
st.title("🏆 NHL Standings")

# Initialize client
@st.cache_resource
def get_client():
    return NHLClient()

client = get_client()

# Load logo
logo_path = Path("data_files/logo.png")
if logo_path.exists():
    st.sidebar.image(str(logo_path), width=150)

# Get standings
try:
    standings_data = client.get_standings()
    teams = standings_data.get("standings", [])
    
    if teams:
        # Group teams by division
        divisions = {}
        for team in teams:
            div_name = team.get("divisionName", "Unknown")
            if div_name not in divisions:
                divisions[div_name] = []
            divisions[div_name].append(team)
        
        # Sort each division by points
        for div in divisions:
            divisions[div].sort(key=lambda x: x.get("points", 0), reverse=True)
        
        # Create tabs for each division
        div_names = list(divisions.keys())
        if len(div_names) == 4:
            tab1, tab2, tab3, tab4 = st.tabs(div_names)
            tabs = [tab1, tab2, tab3, tab4]
        else:
            tabs = st.tabs(div_names)
        
        # Display each division
        for i, div_name in enumerate(div_names):
            with tabs[i]:
                div_teams = divisions[div_name]
                
                standings_df = pd.DataFrame([
                    {
                        "Rank": idx + 1,
                        "Team": client.TEAM_NAMES.get(team.get("teamAbbrev", {}).get("default", ""), team.get("teamAbbrev", {}).get("default", "")),
                        "GP": team.get("gamesPlayed", 0),
                        "W": team.get("wins", 0),
                        "L": team.get("losses", 0),
                        "OTL": team.get("otLosses", 0),
                        "PTS": team.get("points", 0),
                        "GF": team.get("goalFor", 0),
                        "GA": team.get("goalAgainst", 0),
                        "DIFF": team.get("goalDifferential", 0),
                        "P%": f"{team.get('pointPctg', 0):.3f}"
                    }
                    for idx, team in enumerate(div_teams)
                ])
                
                st.dataframe(
                    standings_df,
                    width='stretch',
                    hide_index=True,
                    column_config={
                        "Rank": st.column_config.NumberColumn("Rank", width="small"),
                        "Team": st.column_config.TextColumn("Team", width="medium"),
                        "GP": st.column_config.NumberColumn("Games Played", width="small"),
                        "W": st.column_config.NumberColumn("Wins", width="small"),
                        "L": st.column_config.NumberColumn("Losses", width="small"),
                        "OTL": st.column_config.NumberColumn("OT Losses", width="small"),
                        "PTS": st.column_config.NumberColumn("Points", width="small"),
                        "GF": st.column_config.NumberColumn("Goals For", width="small"),
                        "GA": st.column_config.NumberColumn("Goals Against", width="small"),
                        "DIFF": st.column_config.NumberColumn("Goal Diff", width="small"),
                        "P%": st.column_config.TextColumn("Point %", width="small"),
                    }
                )
        
        # League-wide summary
        st.divider()
        st.subheader("League Leaders")
        
        # Sort by points for top teams
        all_teams_sorted = sorted(teams, key=lambda x: x.get("points", 0), reverse=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Most Points**")
            for i, team in enumerate(all_teams_sorted[:5]):
                abbrev = team.get('teamAbbrev', {}).get('default', '')
                team_name = client.TEAM_NAMES.get(abbrev, abbrev)
                st.write(f"{i+1}. {team_name} - {team.get('points', 0)} pts")
        
        with col2:
            st.markdown("**Most Goals For**")
            top_gf = sorted(teams, key=lambda x: x.get("goalFor", 0), reverse=True)[:5]
            for i, team in enumerate(top_gf):
                abbrev = team.get('teamAbbrev', {}).get('default', '')
                team_name = client.TEAM_NAMES.get(abbrev, abbrev)
                st.write(f"{i+1}. {team_name} - {team.get('goalFor', 0)} GF")
        
        with col3:
            st.markdown("**Best Goal Differential**")
            top_diff = sorted(teams, key=lambda x: x.get("goalDifferential", 0), reverse=True)[:5]
            for i, team in enumerate(top_diff):
                abbrev = team.get('teamAbbrev', {}).get('default', '')
                team_name = client.TEAM_NAMES.get(abbrev, abbrev)
                st.write(f"{i+1}. {team_name} - {team.get('goalDifferential', 0):+d}")
    else:
        st.error("No standings data available")
        
except Exception as e:
    st.error(f"Error loading standings: {e}")
    st.exception(e)

# Add footer
add_betting_oracle_footer()
