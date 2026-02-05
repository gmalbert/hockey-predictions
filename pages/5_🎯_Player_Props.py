"""Player prop betting analysis."""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.api.nhl_client import NHLClient
from footer import add_betting_oracle_footer

st.set_page_config(page_title="Player Props", page_icon="🎯", layout="wide")
st.title("🎯 Player Props Analysis")

st.info("🚧 Player props analysis coming in Phase 2. This page shows current player statistics for reference.")

# Initialize client
@st.cache_resource
def get_client():
    return NHLClient()

client = get_client()

# Prop type selector
prop_type = st.selectbox("Stat Type", ["Points", "Goals", "Assists", "Shots", "Saves (Goalies)"])

# Get player stats based on type
st.subheader(f"Top Players by {prop_type}")

try:
    if prop_type == "Saves (Goalies)":
        # Get goalie stats
        players = client.get_goalie_stats(limit=20)
        
        if players:
            player_df = pd.DataFrame([
                {
                    "Rank": idx + 1,
                    "Player": p["name"],
                    "Team": client.TEAM_NAMES.get(p["team"], p["team"]),
                    "GP": p["games_played"],
                    "Wins": p["wins"],
                    "Losses": p["losses"],
                    "OTL": p["ot_losses"],
                    "Save %": f"{p['save_pct']:.3f}",
                    "GAA": f"{p['gaa']:.2f}",
                    "Shutouts": p["shutouts"],
                    "Saves": p["saves"]
                }
                for idx, p in enumerate(players)
            ])
            
            st.dataframe(
                player_df,
                width='stretch',
                hide_index=True,
                column_config={
                    "Rank": st.column_config.NumberColumn("Rank", width="small"),
                    "Player": st.column_config.TextColumn("Player", width="medium"),
                    "Team": st.column_config.TextColumn("Team", width="medium"),
                    "GP": st.column_config.NumberColumn("Games Played", width="small"),
                    "Wins": st.column_config.NumberColumn("Wins", width="small"),
                    "Losses": st.column_config.NumberColumn("Losses", width="small"),
                    "OTL": st.column_config.NumberColumn("OT Losses", width="small"),
                    "Save %": st.column_config.TextColumn("Save %", width="small"),
                    "GAA": st.column_config.TextColumn("Goals Against Avg", width="small"),
                    "Shutouts": st.column_config.NumberColumn("Shutouts", width="small"),
                    "Saves": st.column_config.NumberColumn("Saves", width="small"),
                }
            )
        else:
            st.info("No goalie stats available.")
    else:
        # Get skater stats
        players = client.get_skater_stats(limit=50)
        
        if players:
            player_df = pd.DataFrame([
                {
                    "Rank": idx + 1,
                    "Player": p["name"],
                    "Team": client.TEAM_NAMES.get(p["team"], p["team"]),
                    "Position": p.get("position", ""),
                    "GP": p["games"],
                    "Goals": p["goals"],
                    "Assists": p["assists"],
                    "Points": p["points"],
                    "Shots": p["shots"],
                    "S%": f"{p['shooting_pct']:.1f}%" if p.get("shooting_pct") else "0%",
                    "TOI/G": f"{p['toi_pg']:.1f}" if p.get("toi_pg") else "0"
                }
                for idx, p in enumerate(players)
            ])
            
            # Sort by selected stat type
            if prop_type == "Points":
                player_df = player_df.sort_values("Points", ascending=False)
            elif prop_type == "Goals":
                player_df = player_df.sort_values("Goals", ascending=False)
            elif prop_type == "Assists":
                player_df = player_df.sort_values("Assists", ascending=False)
            elif prop_type == "Shots":
                player_df = player_df.sort_values("Shots", ascending=False)
            
            # Reset rank after sorting
            player_df["Rank"] = range(1, len(player_df) + 1)
            
            st.dataframe(
                player_df,
                width='stretch',
                hide_index=True,
                column_config={
                    "Rank": st.column_config.NumberColumn("Rank", width="small"),
                    "Player": st.column_config.TextColumn("Player", width="medium"),
                    "Team": st.column_config.TextColumn("Team", width="medium"),
                    "Position": st.column_config.TextColumn("Pos", width="small"),
                    "GP": st.column_config.NumberColumn("Games Played", width="small"),
                    "Goals": st.column_config.NumberColumn("Goals", width="small"),
                    "Assists": st.column_config.NumberColumn("Assists", width="small"),
                    "Points": st.column_config.NumberColumn("Points", width="small"),
                    "Shots": st.column_config.NumberColumn("Shots", width="small"),
                    "S%": st.column_config.TextColumn("Shooting %", width="small"),
                    "TOI/G": st.column_config.TextColumn("TOI/Game", width="small"),
                }
            )
        else:
            st.info("No player stats available.")
    
    # Player search
    st.divider()
    st.subheader("Player Search")
    player_search = st.text_input("Search by name", placeholder="Enter player name...")
    
    if player_search:
        # Filter players
        if prop_type == "Saves (Goalies)":
            players = client.get_goalie_stats(limit=100)
        else:
            players = client.get_skater_stats(limit=200)
        
        matching = [p for p in players if player_search.lower() in p["name"].lower()]
        
        if matching:
            st.success(f"Found {len(matching)} matching player(s)")
            
            for p in matching[:5]:  # Show first 5 matches
                team_name = client.TEAM_NAMES.get(p['team'], p['team'])
                with st.expander(f"{p['name']} ({team_name})"):
                    if prop_type == "Saves (Goalies)":
                        st.write(f"**Games Played:** {p['games_played']}")
                        st.write(f"**Record:** {p['wins']}-{p['losses']}-{p['ot_losses']}")
                        st.write(f"**Save %:** {p['save_pct']:.3f}")
                        st.write(f"**GAA:** {p['gaa']:.2f}")
                        st.write(f"**Shutouts:** {p['shutouts']}")
                        st.write(f"**Saves:** {p['saves']}")
                    else:
                        st.write(f"**Position:** {p.get('position', 'N/A')}")
                        st.write(f"**Games:** {p['games']}")
                        st.write(f"**Goals:** {p['goals']}")
                        st.write(f"**Assists:** {p['assists']}")
                        st.write(f"**Points:** {p['points']}")
                        st.write(f"**Shots:** {p['shots']}")
                        st.write(f"**+/-:** {p.get('plus_minus', 0)}")
        else:
            st.warning("No players found matching that name.")
            
except Exception as e:
    st.error(f"Error loading player stats: {e}")

# Sample props format
st.divider()
st.subheader("Coming Soon: Player Props")
st.markdown("""
**Player props analysis will include:**
- Over/Under lines for goals, assists, points, shots
- Historical performance vs opponent
- Recent form and trends
- Injury and lineup status
- Model-based edge calculations

**Example prop format:**
""")

sample_props = pd.DataFrame({
    "Player": ["A. Matthews", "C. McDavid", "N. Kucherov"],
    "Team": ["TOR", "EDM", "TBL"],
    "Matchup": ["@ MTL", "vs CGY", "@ FLA"],
    "Prop": ["Goals O/U", "Points O/U", "Shots O/U"],
    "Line": [0.5, 1.5, 3.5],
    "Over": ["-140", "+120", "-110"],
    "Model O%": ["65%", "52%", "55%"],
    "Edge": ["+5%", "-3%", "+2%"]
})

st.dataframe(sample_props, width='stretch', hide_index=True)

# Add footer
add_betting_oracle_footer()
