"""Injury tracking dashboard."""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from src.utils.injury_data import load_injuries, load_team_injuries
from src.models.injury_impact import calculate_injury_impact, POSITION_IMPACTS
from src.utils.styles import apply_custom_css
from src.utils.injury_scraper import scrape_cbs_injuries, save_injuries_to_file
from footer import add_betting_oracle_footer

# Position mapping for display
POSITION_NAMES = {
    "G": "Goalie",
    "C": "Center",
    "W": "Winger", 
    "D": "Defenseman"
}

st.set_page_config(page_title="Oracle on Ice - Hockey Predictions", page_icon="🏥", layout="wide")
apply_custom_css()

# Load logo
logo_path = Path("data_files/logo.png")
if logo_path.exists():
    st.sidebar.image(str(logo_path), width=150)

st.title("🏥 Injury Report")
st.markdown("Track injuries and their impact on betting predictions.")

# CBS Sports scraper button
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Refresh from CBS Sports", width='stretch'):
        with st.spinner("Scraping CBS Sports for latest injuries..."):
            injuries = scrape_cbs_injuries()
            if injuries:
                save_injuries_to_file(injuries)
                st.success(f"✅ Updated! Found {sum(len(v) for v in injuries.values())} injuries across {len(injuries)} teams")
                st.rerun()
            else:
                st.error("❌ Failed to fetch injuries from CBS Sports")

# Info box
st.info("""
📰 **Auto-Updated from CBS Sports** - Click "Refresh from CBS Sports" to fetch the latest injury data.
""")

st.markdown("---")

# Team selector
NHL_TEAMS = {
    "ANA": "Anaheim Ducks",
    "BOS": "Boston Bruins", 
    "BUF": "Buffalo Sabres",
    "CAR": "Carolina Hurricanes",
    "CBJ": "Columbus Blue Jackets",
    "CGY": "Calgary Flames",
    "CHI": "Chicago Blackhawks",
    "COL": "Colorado Avalanche",
    "DAL": "Dallas Stars",
    "DET": "Detroit Red Wings",
    "EDM": "Edmonton Oilers",
    "FLA": "Florida Panthers",
    "LAK": "Los Angeles Kings",
    "MIN": "Minnesota Wild",
    "MTL": "Montreal Canadiens",
    "NJD": "New Jersey Devils",
    "NSH": "Nashville Predators",
    "NYI": "New York Islanders",
    "NYR": "New York Rangers",
    "OTT": "Ottawa Senators",
    "PHI": "Philadelphia Flyers",
    "PIT": "Pittsburgh Penguins",
    "SEA": "Seattle Kraken",
    "SJS": "San Jose Sharks",
    "STL": "St. Louis Blues",
    "TBL": "Tampa Bay Lightning",
    "TOR": "Toronto Maple Leafs",
    "UTA": "Utah Hockey Club",
    "VAN": "Vancouver Canucks",
    "VGK": "Vegas Golden Knights",
    "WPG": "Winnipeg Jets",
    "WSH": "Washington Capitals"
}

selected_team_name = st.selectbox("Select Team", list(NHL_TEAMS.values()))

# Get abbreviation from selected full name
selected_team = [abbr for abbr, name in NHL_TEAMS.items() if name == selected_team_name][0]

# Load team injuries
team_injuries = load_team_injuries(selected_team)

# Current injuries table
st.subheader(f"{selected_team_name} Current Injuries")

if team_injuries:
    # Calculate impact
    impact = calculate_injury_impact(team_injuries)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Injuries", len(team_injuries))
    with col2:
        st.metric("Offensive Impact", f"{impact.offensive_impact:.2f} GF/G", 
                  delta=None if impact.offensive_impact == 0 else f"-{impact.offensive_impact:.2f}",
                  delta_color="inverse")
    with col3:
        st.metric("Defensive Impact", f"{impact.defensive_impact:.2f} GA/G",
                  delta=None if impact.defensive_impact == 0 else f"+{impact.defensive_impact:.2f}",
                  delta_color="inverse")
    with col4:
        st.metric("Net Impact", f"{impact.net_impact:.2f} goals",
                  delta=None if impact.net_impact == 0 else f"{impact.net_impact:+.2f}",
                  delta_color="normal")
    
    # Build injury table
    injury_rows = []
    for inj in team_injuries:
        position = inj.get("position", "W")[0]
        tier = inj.get("player_tier", "medium")
        
        # Calculate individual impact
        pos_impact = POSITION_IMPACTS.get(position, {}).get(tier, 0.05)
        
        injury_rows.append({
            "Player": inj["player_name"],
            "Position": POSITION_NAMES.get(inj.get("position", "Unknown"), inj.get("position", "Unknown")),
            "Status": inj["status"].upper(),
            "Injury": inj["injury_type"],
            "Tier": inj.get("player_tier", "medium").capitalize(),
            "Impact": f"-{pos_impact:.2f} goals/game",
            "Updated": inj.get("updated", "Unknown")[:10]  # Date only
        })
    
    injuries_df = pd.DataFrame(injury_rows)
    st.dataframe(injuries_df, width='stretch', hide_index=True)

else:
    st.info(f"No injuries currently tracked for {selected_team_name}")

# All injuries overview
st.subheader("All Teams Injury Summary")

# Impact Reference
with st.expander("📊 Impact Reference Guide"):
    st.markdown("""
    ### Player Tier Guidelines
    
    **Critical** (0.30-0.50 goals/game impact)
    - Starting goalie
    - #1 center or top-line winger
    - #1 defenseman
    
    **High** (0.15-0.30 goals/game impact)
    - Backup goalie (when starter plays)
    - Top-6 forward
    - Top-4 defenseman
    
    **Medium** (0.05-0.15 goals/game impact)
    - Third-line forward
    - 5th/6th defenseman
    
    **Low** (< 0.05 goals/game impact)
    - Fourth-line forward
    - 7th defenseman
    
    ### Status Definitions
    - **Healthy**: Available to play
    - **Day-to-Day**: Minor injury, may miss 1-3 games
    - **Week-to-Week**: Expected to miss 1-3 weeks
    - **IR**: Injured Reserve (minimum 7 days)
    - **LTIR**: Long-term IR (extended absence)
    - **Out**: Confirmed out for next game
    - **Questionable**: 50/50 chance to play
    - **Probable**: Likely to play
    """)

# All injuries overview
st.subheader("All Teams Injury Summary")

all_injuries = load_injuries()
if all_injuries:
    summary_rows = []
    for team, injuries in all_injuries.items():
        if injuries:
            impact = calculate_injury_impact(injuries)
            summary_rows.append({
                "Team": NHL_TEAMS.get(team, team),  # Use full name if available
                "Total Injuries": len(injuries),
                "Key Players Out": ", ".join(impact.key_injuries) if impact.key_injuries else "None",
                "Net Impact": f"{impact.net_impact:+.2f}"
            })
    
    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
        summary_df = summary_df.sort_values("Net Impact")
        st.dataframe(summary_df, width='stretch', hide_index=True)
else:
    st.info("No injuries tracked yet. Click 'Refresh from CBS Sports' above to load the latest injury data.")

add_betting_oracle_footer()
