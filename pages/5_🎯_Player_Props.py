"""Player prop betting analysis."""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import json
from datetime import date, timedelta

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.api.nhl_client import NHLClient
from src.utils.styles import apply_custom_css
from footer import add_betting_oracle_footer

st.set_page_config(page_title="Oracle on Ice - Hockey Predictions", page_icon="🎯", layout="wide")
apply_custom_css()

st.title("🎯 Player Props Analysis")
st.markdown("Analyze player performance and find value in prop betting markets.")

# Initialize client
@st.cache_resource
def get_client():
    return NHLClient()

client = get_client()

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["🎲 Props Analysis", "📊 Player Stats", "🔍 Player Search"])

with tab1:
    st.subheader("Player Props Analysis")
    
    # Get today's games
    try:
        games = client.get_todays_games()
        
        if not games:
            st.info("No NHL games scheduled for today. Check back on game days!")
        else:
            # Filter for only NHL regular season games (game_type == 2)
            nhl_games = [game for game in games if game.get("game_type") == 2]
            
            if not nhl_games:
                st.info("No NHL regular season games scheduled for today.")
            else:
                # Game selector
                game_options = []
                for game in nhl_games:
                    away = client.TEAM_NAMES.get(game.get("away_team", ""), game.get("away_team", ""))
                    home = client.TEAM_NAMES.get(game.get("home_team", ""), game.get("home_team", ""))
                    game_options.append(f"{away} @ {home}")
                
                selected_game = st.selectbox("Select Game", game_options)
                
                if selected_game:
                    # Parse selected game
                    game_idx = game_options.index(selected_game)
                    game = nhl_games[game_idx]
                away_team = game.get("away_team", "")
                home_team = game.get("home_team", "")
                
                st.markdown("---")
                
                # Player selection
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Select Player")
                    team_choice = st.radio("Team", [
                        f"{client.TEAM_NAMES.get(away_team, away_team)} (Away)",
                        f"{client.TEAM_NAMES.get(home_team, home_team)} (Home)"
                    ])
                    
                    selected_team = away_team if "Away" in team_choice else home_team
                    opponent_team = home_team if "Away" in team_choice else away_team
                    
                    # Get players from selected team
                    all_players = client.get_skater_stats(limit=200)
                    team_players = [p for p in all_players if p.get("team") == selected_team]
                    
                    if team_players:
                        # Sort by points
                        team_players.sort(key=lambda x: x.get("points", 0), reverse=True)
                        player_options = [f"{p['name']} ({p.get('position', 'F')})" for p in team_players[:20]]
                        
                        selected_player_name = st.selectbox("Player", player_options)
                        player_idx = player_options.index(selected_player_name)
                        selected_player = team_players[player_idx]
                    else:
                        st.warning("No player data available")
                        selected_player = None
                
                with col2:
                    if selected_player:
                        st.markdown("### Prop Type")
                        prop_type = st.selectbox("Stat", [
                            "Points (Goals + Assists)",
                            "Goals",
                            "Assists", 
                            "Shots on Goal"
                        ])
                        
                        prop_line = st.number_input("Prop Line (O/U)", min_value=0.5, max_value=10.0, value=0.5, step=0.5)
                        
                        over_odds = st.number_input("Over Odds (American)", min_value=-500, max_value=500, value=-110, step=10)
                        under_odds = st.number_input("Under Odds (American)", min_value=-500, max_value=500, value=-110, step=10)
                
                # Analysis section
                if selected_player:
                    st.markdown("---")
                    st.subheader(f"Analysis: {selected_player['name']}")
                    
                    # Season stats
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Games Played", selected_player.get("games", 0))
                        st.metric("Points", selected_player.get("points", 0))
                    
                    with col2:
                        st.metric("Goals", selected_player.get("goals", 0))
                        st.metric("Assists", selected_player.get("assists", 0))
                    
                    with col3:
                        st.metric("Shots", selected_player.get("shots", 0))
                        ppg = selected_player.get("points", 0) / max(selected_player.get("games", 1), 1)
                        st.metric("Points/Game", f"{ppg:.2f}")
                    
                    with col4:
                        gpg = selected_player.get("goals", 0) / max(selected_player.get("games", 1), 1)
                        st.metric("Goals/Game", f"{gpg:.2f}")
                        apg = selected_player.get("assists", 0) / max(selected_player.get("games", 1), 1)
                        st.metric("Assists/Game", f"{apg:.2f}")
                    
                    st.markdown("---")
                    
                    # Calculate hit rate and edge
                    if prop_type == "Points (Goals + Assists)":
                        avg_stat = ppg
                        stat_name = "points"
                    elif prop_type == "Goals":
                        avg_stat = gpg
                        stat_name = "goals"
                    elif prop_type == "Assists":
                        avg_stat = apg
                        stat_name = "assists"
                    else:  # Shots
                        avg_stat = selected_player.get("shots", 0) / max(selected_player.get("games", 1), 1)
                        stat_name = "shots"
                    
                    # Simple model: use season average to estimate probability
                    # This is a simplified Poisson-based estimate
                    import math
                    
                    def poisson_prob_over(avg, line):
                        """Estimate probability of going over using Poisson distribution."""
                        prob_under = 0
                        for k in range(int(line) + 1):
                            prob_under += (avg ** k * math.exp(-avg)) / math.factorial(k)
                        return 1 - prob_under
                    
                    model_over_prob = poisson_prob_over(avg_stat, prop_line)
                    model_under_prob = 1 - model_over_prob
                    
                    # Calculate implied probabilities from odds
                    def american_to_prob(odds):
                        if odds > 0:
                            return 100 / (odds + 100)
                        else:
                            return abs(odds) / (abs(odds) + 100)
                    
                    market_over_prob = american_to_prob(over_odds)
                    market_under_prob = american_to_prob(under_odds)
                    
                    # Calculate edge
                    over_edge = model_over_prob - market_over_prob
                    under_edge = model_under_prob - market_under_prob
                    
                    # Display analysis
                    st.subheader("📊 Prop Analysis")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Over Analysis")
                        st.metric("Line", f"{prop_line} {stat_name}")
                        st.metric("Season Average", f"{avg_stat:.2f}")
                        st.metric("Model Probability", f"{model_over_prob:.1%}")
                        st.metric("Market Probability", f"{market_over_prob:.1%}")
                        
                        edge_pct = over_edge * 100
                        if over_edge > 0.05:
                            st.success(f"**Edge: +{edge_pct:.1f}%** ✅ VALUE BET")
                        elif over_edge > 0:
                            st.info(f"**Edge: +{edge_pct:.1f}%** 📊 SLIGHT VALUE")
                        else:
                            st.warning(f"**Edge: {edge_pct:.1f}%** ⚠️ NO VALUE")
                    
                    with col2:
                        st.markdown("#### Under Analysis")
                        st.metric("Line", f"{prop_line} {stat_name}")
                        st.metric("Hit Rate (Under)", f"{model_under_prob:.1%}")
                        st.metric("Model Probability", f"{model_under_prob:.1%}")
                        st.metric("Market Probability", f"{market_under_prob:.1%}")
                        
                        edge_pct = under_edge * 100
                        if under_edge > 0.05:
                            st.success(f"**Edge: +{edge_pct:.1f}%** ✅ VALUE BET")
                        elif under_edge > 0:
                            st.info(f"**Edge: +{edge_pct:.1f}%** 📊 SLIGHT VALUE")
                        else:
                            st.warning(f"**Edge: {edge_pct:.1f}%** ⚠️ NO VALUE")
                    
                    # Recommendation
                    st.markdown("---")
                    st.subheader("💡 Recommendation")
                    
                    best_edge = max(over_edge, under_edge)
                    
                    if best_edge > 0.05:
                        rec = "**OVER**" if over_edge > under_edge else "**UNDER**"
                        st.success(f"🎯 Strong value on {rec} at {best_edge*100:.1f}% edge")
                        st.markdown(f"""
                        **Reasoning:**
                        - Player's season average: **{avg_stat:.2f} {stat_name}/game**
                        - Line set at: **{prop_line}**
                        - Model suggests {rec} has {best_edge*100:.1f}% better chance than market implies
                        - {"Player performing above this line in majority of games" if over_edge > under_edge else "Player performing below this line in majority of games"}
                        """)
                    elif best_edge > 0:
                        rec = "**OVER**" if over_edge > under_edge else "**UNDER**"
                        st.info(f"📊 Slight value on {rec} at {best_edge*100:.1f}% edge - proceed with caution")
                    else:
                        st.warning("⚠️ No clear value found on either side. Pass on this prop or wait for better lines.")
                    
                    # Historical context
                    with st.expander("📈 Additional Context"):
                        st.markdown(f"""
                        **Recent Form Indicators:**
                        - **Season Stats:** {selected_player.get('points', 0)} points in {selected_player.get('games', 0)} games
                        - **Position:** {selected_player.get('position', 'N/A')}
                        - **Shooting %:** {selected_player.get('shooting_pct', 0):.1f}%
                        - **TOI/Game:** {selected_player.get('toi_pg', 0):.1f} minutes
                        
                        **Matchup Notes:**
                        - Playing against: **{client.TEAM_NAMES.get(opponent_team, opponent_team)}**
                        - {"Home" if selected_team == home_team else "Away"} game advantage
                        
                        **Injury Status:**
                        """)
                        
                        # Check injury status
                        injury_file = Path("data_files/injuries.json")
                        if injury_file.exists():
                            with open(injury_file, 'r') as f:
                                injuries = json.load(f)
                                team_injuries = injuries.get(selected_team, [])
                                player_injured = any(inj.get('player_name', '').lower() in selected_player['name'].lower() for inj in team_injuries)
                                
                                if player_injured:
                                    st.error("⚠️ Player has injury designation - check status before betting!")
                                else:
                                    st.success("✅ No injury concerns reported")
                        else:
                            st.info("Injury data not available")
    
    except Exception as e:
        st.error(f"Error loading games: {e}")
        st.info("Try refreshing the page or come back later")

with tab2:
    st.subheader("League Leaders")
    
    # Prop type selector
    prop_type = st.selectbox("Stat Type", ["Points", "Goals", "Assists", "Shots", "Saves (Goalies)"])

    # Get player stats based on type
    st.markdown(f"### Top Players by {prop_type}")

    # Position mapping function
    def get_full_position(pos_abbrev):
        """Convert position abbreviation to full name."""
        pos_map = {
            "C": "Center",
            "LW": "Left Wing", 
            "RW": "Right Wing",
            "L": "Left Wing",
            "R": "Right Wing",
            "D": "Defense",
            "G": "Goalie",
            "F": "Forward"
        }
        return pos_map.get(pos_abbrev, pos_abbrev)

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
                        "Games Played": p["games_played"],
                        "Wins": p["wins"],
                        "Losses": p["losses"],
                        "OT Losses": p["ot_losses"],
                        "Save %": f"{p['save_pct']:.3f}",
                        "Goals Against Avg": f"{p['gaa']:.2f}",
                        "Shutouts": p["shutouts"],
                        "Saves": p["saves"]
                    }
                    for idx, p in enumerate(players)
                ])
                
                st.dataframe(
                    player_df,
                    use_container_width=True,
                    hide_index=True
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
                        "Position": get_full_position(p.get("position", "")),
                        "Games Played": p["games"],
                        "Goals": p["goals"],
                        "Assists": p["assists"],
                        "Points": p["points"],
                        "Shots": p["shots"],
                        "Shooting %": f"{p['shooting_pct']:.1f}%" if p.get("shooting_pct") else "0%",
                        "Time on Ice/Game": f"{p['toi_pg']:.1f}" if p.get("toi_pg") else "0"
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
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No player stats available.")
                
    except Exception as e:
        st.error(f"Error loading player stats: {e}")

with tab3:
    st.subheader("Player Search")
    
    prop_search_type = st.selectbox("Search Category", ["Skaters", "Goalies"], key="search_type")
    player_search = st.text_input("Search by name", placeholder="Enter player name...")
    
    if player_search:
        try:
            # Filter players
            if prop_search_type == "Goalies":
                players = client.get_goalie_stats(limit=100)
            else:
                players = client.get_skater_stats(limit=200)
            
            matching = [p for p in players if player_search.lower() in p["name"].lower()]
            
            if matching:
                st.success(f"Found {len(matching)} matching player(s)")
                
                for p in matching[:10]:  # Show first 10 matches
                    team_name = client.TEAM_NAMES.get(p['team'], p['team'])
                    with st.expander(f"{p['name']} ({team_name})"):
                        if prop_search_type == "Goalies":
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Games Played", p['games_played'])
                                st.metric("Wins", p['wins'])
                            with col2:
                                st.metric("Save %", f"{p['save_pct']:.3f}")
                                st.metric("GAA", f"{p['gaa']:.2f}")
                            with col3:
                                st.metric("Shutouts", p['shutouts'])
                                st.metric("Saves", p['saves'])
                        else:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Position", get_full_position(p.get('position', 'N/A')))
                                st.metric("Games Played", p['games'])
                                st.metric("Goals", p['goals'])
                            with col2:
                                st.metric("Assists", p['assists'])
                                st.metric("Points", p['points'])
                                st.metric("Shots", p['shots'])
                            with col3:
                                ppg = p['points'] / max(p['games'], 1)
                                st.metric("Points/Game", f"{ppg:.2f}")
                                st.metric("Plus/Minus", p.get('plus_minus', 0))
                                st.metric("Shooting %", f"{p.get('shooting_pct', 0):.1f}%")
            else:
                st.warning("No players found matching that name.")
        except Exception as e:
            st.error(f"Error searching players: {e}")
