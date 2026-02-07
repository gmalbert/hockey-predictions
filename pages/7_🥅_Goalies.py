"""Goalie analysis and matchup comparison page."""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from src.api.nhl_client import NHLClient
from src.models.goalie_adjustment import calculate_goalie_adjustment, adjusted_xg_for_matchup, LEAGUE_AVG_SAVE_PCT
from src.models.goalie_matchup import compare_goalie_matchup, goalie_recent_form
from src.utils.styles import apply_custom_css
from footer import add_betting_oracle_footer

st.set_page_config(page_title="Oracle on Ice - Hockey Predictions", page_icon="🥅", layout="wide")
apply_custom_css()

st.title("🥅 Goalie Analysis")
st.markdown("Analyze goalie matchups and their impact on betting value.")

# Initialize client for team names
client = NHLClient()

# Fetch goalie stats first
try:
    import httpx
    url = "https://api.nhle.com/stats/rest/en/goalie/summary"
    params = {
        "cayenneExp": "seasonId=20252026",
        "sort": "savePct",
        "direction": "DESC",
        "limit": 100
    }
    
    with httpx.Client(timeout=10.0) as http_client:
        response = http_client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    
    # Build goalie dictionary
    goalie_stats = {}
    goalie_names = []
    for g in data.get("data", []):
        if g.get("gamesPlayed", 0) >= 5:  # Minimum 5 games
            name = g.get("goalieFullName", "Unknown")
            team = g.get("teamAbbrevs", "")
            display_name = f"{name} ({team})"
            goalie_names.append(display_name)
            goalie_stats[display_name] = {
                "name": name,
                "team": team,
                "sv_pct": g.get("savePct", 0.900),
                "games": g.get("gamesPlayed", 0),
                "wins": g.get("wins", 0),
                "gaa": g.get("goalsAgainstAverage", 0),
                "shutouts": g.get("shutouts", 0)
            }
    
    if not goalie_names:
        st.error("No goalie data available")
        st.stop()
        
except Exception as e:
    st.error(f"Could not load goalie data: {e}")
    st.stop()

# Quick Goalie Comparison
st.subheader("Goalie Matchup Comparison")

st.info("""
💡 **Tip**: Select two goalies below to compare their stats and see the betting edge.
""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🏠 Home Goalie")
    goalie_1_select = st.selectbox(
        "Select Goalie",
        options=goalie_names,
        key="goalie_1",
        index=0
    )
    
    goalie_1 = goalie_stats[goalie_1_select]
    
    # Calculate adjustment
    goalie_1_adj = calculate_goalie_adjustment(goalie_1["sv_pct"], goalie_1["games"])
    
    # Display stats
    st.markdown(f"**{goalie_1['team']}** - {goalie_1['games']} GP")
    
    col1a, col1b, col1c = st.columns(3)
    with col1a:
        st.metric("SV%", f"{goalie_1['sv_pct']:.3f}")
    with col1b:
        st.metric("GAA", f"{goalie_1['gaa']:.2f}")
    with col1c:
        st.metric("W-SO", f"{goalie_1['wins']}-{goalie_1['shutouts']}")
    
    col1d, col1e = st.columns(2)
    with col1d:
        st.metric("vs League Avg", f"{(goalie_1['sv_pct'] - LEAGUE_AVG_SAVE_PCT)*100:+.1f}%")
    with col1e:
        st.metric("Goals Saved/Game", f"{goalie_1_adj.adjustment:+.2f}")
    
    # Confidence indicator
    confidence_color = {
        "high": "🟢",
        "medium": "🟡",
        "low": "🔴"
    }
    st.caption(f"{confidence_color.get(goalie_1_adj.confidence, '⚪')} Confidence: {goalie_1_adj.confidence.title()}")

with col2:
    st.markdown("### ✈️ Away Goalie")
    goalie_2_select = st.selectbox(
        "Select Goalie",
        options=goalie_names,
        key="goalie_2",
        index=min(1, len(goalie_names)-1)
    )
    
    goalie_2 = goalie_stats[goalie_2_select]
    
    # Calculate adjustment
    goalie_2_adj = calculate_goalie_adjustment(goalie_2["sv_pct"], goalie_2["games"])
    
    # Display stats
    st.markdown(f"**{goalie_2['team']}** - {goalie_2['games']} GP")
    
    col2a, col2b, col2c = st.columns(3)
    with col2a:
        st.metric("SV%", f"{goalie_2['sv_pct']:.3f}")
    with col2b:
        st.metric("GAA", f"{goalie_2['gaa']:.2f}")
    with col2c:
        st.metric("W-SO", f"{goalie_2['wins']}-{goalie_2['shutouts']}")
    
    col2d, col2e = st.columns(2)
    with col2d:
        st.metric("vs League Avg", f"{(goalie_2['sv_pct'] - LEAGUE_AVG_SAVE_PCT)*100:+.1f}%")
    with col2e:
        st.metric("Goals Saved/Game", f"{goalie_2_adj.adjustment:+.2f}")
    
    # Confidence indicator
    st.caption(f"{confidence_color.get(goalie_2_adj.confidence, '⚪')} Confidence: {goalie_2_adj.confidence.title()}")

# Matchup Analysis
st.markdown("---")
st.subheader("Matchup Edge Analysis")

matchup = compare_goalie_matchup(
    home_goalie_sv_pct=goalie_1["sv_pct"],
    away_goalie_sv_pct=goalie_2["sv_pct"],
    home_goalie_name=goalie_1["name"],
    away_goalie_name=goalie_2["name"]
)

# Display edge
edge_col1, edge_col2, edge_col3 = st.columns([1, 2, 1])

with edge_col2:
    if matchup.edge_team == "Even":
        st.info(f"**⚖️ Matchup is Even**\n\nNo significant goalie advantage ({matchup.edge_magnitude:.2f} goals)")
    elif matchup.edge_team == "Home":
        st.success(f"**🏠 {goalie_1['name']} Advantage**\n\n{matchup.edge_magnitude:.2f} expected goals difference")
    else:
        st.warning(f"**✈️ {goalie_2['name']} Advantage**\n\n{matchup.edge_magnitude:.2f} expected goals difference")

# Expected Goals Adjustment Example
st.markdown("---")
st.subheader("Expected Goals Adjustment")

st.markdown("""
See how goalie quality affects team expected goals (xG):
""")

col3, col4 = st.columns(2)

with col3:
    st.markdown(f"#### {goalie_1['team']} Attack (vs {goalie_2['name']})")
    goalie_1_team_xg = st.slider("Base xG (before goalie adj)", 2.0, 4.5, 3.0, 0.1, key="goalie_1_xg")
    
    # Adjust for opposing goalie
    adjusted_goalie_1_xg = adjusted_xg_for_matchup(goalie_1_team_xg, goalie_2["sv_pct"], goalie_2["games"])
    
    st.metric(
        "Adjusted xG",
        f"{adjusted_goalie_1_xg:.2f}",
        delta=f"{adjusted_goalie_1_xg - goalie_1_team_xg:+.2f} goals",
        delta_color="normal"
    )

with col4:
    st.markdown(f"#### {goalie_2['team']} Attack (vs {goalie_1['name']})")
    goalie_2_team_xg = st.slider("Base xG (before goalie adj)", 2.0, 4.5, 3.0, 0.1, key="goalie_2_xg")
    
    # Adjust for opposing goalie
    adjusted_goalie_2_xg = adjusted_xg_for_matchup(goalie_2_team_xg, goalie_1["sv_pct"], goalie_1["games"])
    
    st.metric(
        "Adjusted xG",
        f"{adjusted_goalie_2_xg:.2f}",
        delta=f"{adjusted_goalie_2_xg - goalie_2_team_xg:+.2f} goals",
        delta_color="normal"
    )

# League Goalie Rankings
st.markdown("---")
st.subheader("League Goalie Leaders")

# Convert goalie_stats dict to DataFrame for display
display_goalies = []
for name, stats in goalie_stats.items():
    display_goalies.append({
        "Goalie": stats["name"],
        "Team": client.TEAM_NAMES.get(stats["team"], stats["team"]),  # Full team name
        "Games": stats["games"],
        "Wins": stats["wins"],
        "Save %": f"{stats['sv_pct']:.3f}",
        "GAA": f"{stats['gaa']:.2f}",
        "Shutouts": stats["shutouts"],
        "Quality Starts": f"{int((stats['sv_pct'] - 0.880) / 0.040 * 100)}%"  # Rough estimate
    })

df = pd.DataFrame(display_goalies[:30])  # Top 30
st.dataframe(df, hide_index=True, use_container_width=True)

# Interpretation Guide
with st.expander("📚 Goalie Analysis Guide"):
    st.markdown("""
    ### Understanding Goalie Impact
    
    **Save Percentage Benchmarks**
    - **Elite (> 0.920)**: Top-tier goalie, significant betting factor
    - **Above Average (0.910-0.920)**: Solid starter, positive impact
    - **League Average (0.900-0.910)**: Typical NHL starter
    - **Below Average (< 0.900)**: Weakness to exploit
    
    **Expected Goals Adjustment**
    - Each 1% in SV% above league average ≈ **0.3 goals saved per game**
    - Example: 0.920 SV% goalie vs 0.900 SV% goalie = **0.6 goal swing**
    
    **When Goalies Matter Most**
    1. **High-shot games**: Team facing 35+ shots benefits from elite goalie
    2. **Playoff races**: Hot goalie can carry team through stretch
    3. **Back-to-backs**: Backup quality crucial in second game
    4. **Injury returns**: Goalie returning from injury may be rusty
    
    **Betting Implications**
    - ✅ **Bet on team with goalie edge** if line doesn't reflect it
    - ✅ **Fade team with struggling goalie** even if favored
    - ✅ **Look for total value** when elite vs weak goalie
    - ⚠️ **Small samples unreliable** - need 15+ games for confidence
    
    **Quality Start (QS) Definition**
    - SV% > 0.917 in a game (roughly 2 goals allowed on 25 shots)
    - Elite goalies have 60%+ QS rate
    - Backup goalies often below 40% QS rate
    """)

add_betting_oracle_footer()
