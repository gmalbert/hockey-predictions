"""Today's games with predictions and betting value."""
import streamlit as st
import pandas as pd
from datetime import date, datetime, timezone
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.api.nhl_client import NHLClient
from footer import add_betting_oracle_footer

st.set_page_config(page_title="Today's Games", page_icon="📅", layout="wide")
st.title("📅 Today's Games")

# Initialize client
@st.cache_resource
def get_client():
    return NHLClient()

client = get_client()

# Date selector
selected_date = st.date_input("Select Date", value=date.today())

# Get games for selected date
try:
    date_str = selected_date.strftime("%Y-%m-%d")
    schedule = client.get_schedule(date_str)
    
    games_list = []
    for game_week in schedule.get("gameWeek", []):
        for game in game_week.get("games", []):
            # Filter for NHL games only (gameType 2=regular season, 3=playoffs)
            if game.get("gameType") in [2, 3]:
                games_list.append(game)
    
    if games_list:
        # Build games table
        games_data = []
        for game in games_list:
            try:
                game_time = game.get("startTimeUTC", "")
                if game_time:
                    dt = pd.to_datetime(game_time, utc=True).tz_convert('US/Eastern')
                    time_str = dt.strftime('%I:%M %p ET')
                else:
                    time_str = "TBD"
                
                away_abbrev = game.get("awayTeam", {}).get("abbrev", "")
                home_abbrev = game.get("homeTeam", {}).get("abbrev", "")
                
                games_data.append({
                    "Time": time_str,
                    "Away": client.TEAM_NAMES.get(away_abbrev, away_abbrev),
                    "Home": client.TEAM_NAMES.get(home_abbrev, home_abbrev),
                    "Score": f"{game.get('awayTeam', {}).get('score', '—')} - {game.get('homeTeam', {}).get('score', '—')}",
                    "Status": game.get("gameState", ""),
                    "Venue": game.get("venue", {}).get("default", "")
                })
            except Exception as e:
                st.warning(f"Error processing game: {e}")
                continue
        
        if games_data:
            df = pd.DataFrame(games_data)
            
            # Styled dataframe
            st.dataframe(
                df,
                width='stretch',
                hide_index=True,
                column_config={
                    "Time": st.column_config.TextColumn("Time", width="small"),
                    "Away": st.column_config.TextColumn("Away Team", width="medium"),
                    "Home": st.column_config.TextColumn("Home Team", width="medium"),
                    "Score": st.column_config.TextColumn("Score", width="small"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "Venue": st.column_config.TextColumn("Venue", width="medium"),
                }
            )
            
            # Game details sections
            st.subheader("Game Details")
            for i, game in enumerate(games_list[:5]):  # Show first 5 games
                away_abbrev = game.get("awayTeam", {}).get("abbrev", "")
                home_abbrev = game.get("homeTeam", {}).get("abbrev", "")
                away_name = game.get("awayTeam", {}).get("name", {}).get("default", away_abbrev)
                home_name = game.get("homeTeam", {}).get("name", {}).get("default", home_abbrev)
                
                game_time = games_data[i]["Time"] if i < len(games_data) else "TBD"
                
                with st.expander(f"{away_abbrev} @ {home_abbrev} - {game_time}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"### {away_name}")
                        # Get away team stats
                        away_stats = client.get_team_summary(away_abbrev)
                        if away_stats:
                            st.write(f"**Record:** {away_stats['wins']}-{away_stats['losses']}-{away_stats['ot_losses']}")
                            st.write(f"**Goals/Game:** {away_stats['goals_for_pg']:.2f}")
                            st.write(f"**Goals Against:** {away_stats['goals_against_pg']:.2f}")
                            st.write(f"**PP%:** {away_stats['pp_pct']:.1%}")
                            st.write(f"**PK%:** {away_stats['pk_pct']:.1%}")
                        else:
                            st.info("Stats not available")
                    
                    with col2:
                        st.markdown(f"### {home_name}")
                        # Get home team stats
                        home_stats = client.get_team_summary(home_abbrev)
                        if home_stats:
                            st.write(f"**Record:** {home_stats['wins']}-{home_stats['losses']}-{home_stats['ot_losses']}")
                            st.write(f"**Goals/Game:** {home_stats['goals_for_pg']:.2f}")
                            st.write(f"**Goals Against:** {home_stats['goals_against_pg']:.2f}")
                            st.write(f"**PP%:** {home_stats['pp_pct']:.1%}")
                            st.write(f"**PK%:** {home_stats['pk_pct']:.1%}")
                        else:
                            st.info("Stats not available")
        else:
            st.info("No games data available for processing.")
    else:
        st.info("No games scheduled for this date.")
        
except Exception as e:
    st.error(f"Error loading games: {e}")

# Betting odds section
st.divider()
st.subheader("📊 Betting Odds")

try:
    odds_data = client.get_espn_odds(days_ahead=1)
    
    if odds_data:
        odds_list = []
        for game in odds_data:
            if game.get("odds"):
                provider = game["odds"][0]
                odds_list.append({
                    "Matchup": game.get("name", ""),
                    "Home ML": provider.get("moneyline", {}).get("home", "N/A"),
                    "Away ML": provider.get("moneyline", {}).get("away", "N/A"),
                    "Spread": f"{provider.get('spread', {}).get('home', {}).get('line', 'N/A')}",
                    "Total": f"{provider.get('total', {}).get('over', {}).get('line', 'N/A')}",
                    "Provider": provider.get("provider", "DraftKings")
                })
        
        if odds_list:
            odds_df = pd.DataFrame(odds_list)
            st.dataframe(odds_df, width='stretch', hide_index=True)
        else:
            st.info("No odds available for selected date.")
    else:
        st.info("Odds data not available.")
except Exception as e:
    st.warning(f"Unable to load odds: {e}")

# Add footer
add_betting_oracle_footer()
