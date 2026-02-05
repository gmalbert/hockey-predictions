"""Oracle on Ice - NHL Predictions Platform."""
import streamlit as st
from pathlib import Path
import pandas as pd
from src.api.nhl_client import NHLClient

# Team abbreviation to full name mapping
team_mapping = {
    'ANA': 'Anaheim Ducks',
    'ARI': 'Arizona Coyotes',
    'BOS': 'Boston Bruins',
    'BUF': 'Buffalo Sabres',
    'CAR': 'Carolina Hurricanes',
    'CBJ': 'Columbus Blue Jackets',
    'CGY': 'Calgary Flames',
    'CHI': 'Chicago Blackhawks',
    'COL': 'Colorado Avalanche',
    'DAL': 'Dallas Stars',
    'DET': 'Detroit Red Wings',
    'EDM': 'Edmonton Oilers',
    'FLA': 'Florida Panthers',
    'LAK': 'Los Angeles Kings',
    'LA': 'Los Angeles Kings',  # Alternative abbreviation
    'MIN': 'Minnesota Wild',
    'MTL': 'Montreal Canadiens',
    'MON': 'Montreal Canadiens',  # Alternative abbreviation
    'NJD': 'New Jersey Devils',
    'NJ': 'New Jersey Devils',  # Alternative abbreviation
    'NSH': 'Nashville Predators',
    'NYI': 'New York Islanders',
    'NYR': 'New York Rangers',
    'OTT': 'Ottawa Senators',
    'PHI': 'Philadelphia Flyers',
    'PIT': 'Pittsburgh Penguins',
    'SEA': 'Seattle Kraken',
    'SJS': 'San Jose Sharks',
    'SJ': 'San Jose Sharks',  # Alternative abbreviation
    'STL': 'St. Louis Blues',
    'TBL': 'Tampa Bay Lightning',
    'TB': 'Tampa Bay Lightning',  # Alternative abbreviation
    'TOR': 'Toronto Maple Leafs',
    'VAN': 'Vancouver Canucks',
    'VGK': 'Vegas Golden Knights',
    'WPG': 'Winnipeg Jets',
    'WSH': 'Washington Capitals',
    'WAS': 'Washington Capitals',  # Alternative abbreviation
}

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

def get_dataframe_height(df, row_height=35, header_height=38, padding=2, max_height=600):
    """
    Calculate the optimal height for a Streamlit dataframe based on number of rows.
    
    Args:
        df (pd.DataFrame): The dataframe to display
        row_height (int): Height per row in pixels. Default: 35
        header_height (int): Height of header row in pixels. Default: 38
        padding (int): Extra padding in pixels. Default: 2
        max_height (int): Maximum height cap in pixels. Default: 600 (None for no limit)
    
    Returns:
        int: Calculated height in pixels
    
    Example:
        height = get_dataframe_height(my_df)
        st.dataframe(my_df, height=height)
    """
    num_rows = len(df)
    calculated_height = (num_rows * row_height) + header_height + padding
    
    if max_height is not None:
        return min(calculated_height, max_height)
    return calculated_height

st.sidebar.title("Oracle on Ice")
st.sidebar.markdown("NHL Betting Analytics")
st.sidebar.divider()

# Main content
st.title("🏒 Oracle on Ice")
st.markdown("### NHL Predictions & Betting Analytics")

st.markdown("""
Welcome to **Oracle on Ice** - your data-driven guide to NHL betting insights.

**Key (Predicted) Features:**
- 📊 Advanced prediction models using expected goals (xG)
- 💰 Moneyline and puck line analysis
- 📈 Live line movement tracking
- 🥅 Goalie performance adjustments
- 🏥 Injury impact calculations
- 📈 Model evaluation with MAE metrics

---
""")

# Placeholder metrics
# st.subheader("Today's Overview")
# col1, col2, col3, col4 = st.columns(4)

# with col1:
#     st.metric("Games Today", "—", help="Number of NHL games scheduled")
# with col2:
#     st.metric("Value Bets", "—", help="Bets with positive expected value")
# with col3:
#     st.metric("Model Accuracy", "—", help="Last 30 days")
# with col4:
#     st.metric("MAE (Goals)", "—", help="Mean Absolute Error")

# st.divider()

# # System status
# st.subheader("System Status")
# col1, col2 = st.columns(2)

# with col1:
#     st.markdown("**Data Sources**")
#     st.markdown("- 🟢 NHL Web API")
#     st.markdown("- 🟢 NHL Stats API")

# with col2:
#     st.markdown("**Last Updated**")
#     st.markdown("- Schedule: —")
#     st.markdown("- Standings: —")
#     st.markdown("- Odds: —")

# st.divider()

# Data Preview Tabs
st.subheader("Data Preview (2025-26 Season)")
tab1, tab2, tab3, tab4 = st.tabs(["Team Stats", "Player Stats", "Recent Games", "Today's Odds"])

with tab1:
    try:
        df_team = pd.read_json("data_files/historical/2025-26/team_stats.json")
        df_team = df_team.reset_index(drop=True)
        # Reorder columns
        column_order = [
            'teamFullName', 'gamesPlayed', 'wins', 'losses', 'otLosses', 'points',
            'goalsFor', 'goalsAgainst', 'goalsForPerGame', 'goalsAgainstPerGame',
            'shotsForPerGame', 'shotsAgainstPerGame', 'powerPlayPct', 'penaltyKillPct',
            'faceoffWinPct', 'teamShutouts'
        ]
        df_team = df_team[column_order]
        # Rename columns
        rename_dict = {
            'teamFullName': 'Team',
            'gamesPlayed': 'Games Played',
            'wins': 'Wins',
            'losses': 'Losses',
            'otLosses': 'OT Losses',
            'points': 'Points',
            'goalsFor': 'Goals For',
            'goalsAgainst': 'Goals Against',
            'goalsForPerGame': 'Goals For Per Game',
            'goalsAgainstPerGame': 'Goals Against Per Game',
            'shotsForPerGame': 'Shots For Per Game',
            'shotsAgainstPerGame': 'Shots Against Per Game',
            'powerPlayPct': 'Power Play %',
            'penaltyKillPct': 'Penalty Kill %',
            'faceoffWinPct': 'Faceoff Win %',
            'teamShutouts': 'Shutouts'
        }
        df_team = df_team.rename(columns=rename_dict)
        st.dataframe(df_team, width='stretch', hide_index=True, height=get_dataframe_height(df_team))
    except FileNotFoundError:
        st.error("Team stats data not found.")

with tab2:
    try:
        df_skater = pd.read_json("data_files/historical/2025-26/skater_stats.json")
        df_skater = df_skater.reset_index(drop=True)
        # Reorder columns
        column_order = [
            'lastName', 'teamAbbrevs', 'positionCode', 'gamesPlayed', 'goals', 'assists', 'points',
            'plusMinus', 'penaltyMinutes', 'shots', 'shootingPct', 'timeOnIcePerGame'
        ]
        df_skater = df_skater[column_order]
        # Rename columns
        rename_dict = {
            'lastName': 'Name',
            'teamAbbrevs': 'Team',
            'positionCode': 'Position',
            'gamesPlayed': 'Games Played',
            'goals': 'Goals',
            'assists': 'Assists',
            'points': 'Points',
            'plusMinus': 'Plus/Minus',
            'penaltyMinutes': 'Penalty Minutes',
            'shots': 'Shots',
            'shootingPct': 'Shooting %',
            'timeOnIcePerGame': 'Time On Ice Per Game'
        }
        df_skater = df_skater.rename(columns=rename_dict)
        df_skater['Team'] = df_skater['Team'].map(team_mapping)
        st.dataframe(df_skater, width='stretch', hide_index=True, height=get_dataframe_height(df_skater))
    except FileNotFoundError:
        st.error("Player stats data not found.")

with tab3:
    try:
        df_games = pd.read_json("data_files/historical/2025-26/games.json")
        df_games = df_games.reset_index(drop=True)
        # Sort by date descending and show last 20 games
        df_games['date'] = pd.to_datetime(df_games['date'])
        df_recent = df_games.sort_values('date', ascending=False).head(20)
        # Reorder columns
        column_order = ['date', 'home_team', 'away_team', 'home_score', 'away_score', 'venue', 'went_to_ot']
        df_recent = df_recent[column_order]
        # Rename columns
        rename_dict = {
            'date': 'Date',
            'home_team': 'Home Team',
            'away_team': 'Away Team',
            'home_score': 'Home Score',
            'away_score': 'Away Score',
            'venue': 'Venue',
            'went_to_ot': 'Overtime'
        }
        df_recent = df_recent.rename(columns=rename_dict)
        df_recent['Date'] = df_recent['Date'].dt.strftime('%Y-%m-%d')
        df_recent['Home Team'] = df_recent['Home Team'].map(team_mapping)
        df_recent['Away Team'] = df_recent['Away Team'].map(team_mapping)
        st.dataframe(df_recent, width='stretch', hide_index=True, height=get_dataframe_height(df_recent))
    except FileNotFoundError:
        st.error("Game results data not found.")

with tab4:
    try:
        client = NHLClient()
        odds_data = client.get_espn_odds(days_ahead=14)  # Get games for the next 2 weeks
        
        if odds_data:
            # Convert to DataFrame for display
            df_odds = pd.DataFrame(odds_data)
            df_odds = df_odds.reset_index(drop=True)
            
            # Create display dataframe with professional column names
            df_display = pd.DataFrame({
                'Away Team': df_odds['away_team'],
                'Home Team': df_odds['home_team'],
                'Game Date': pd.to_datetime(df_odds['date'], utc=True).dt.tz_convert('US/Eastern'),
                'Game Status': df_odds['status']
            })
            
            # Format date column
            def format_date(dt):
                if dt.time() == pd.Timestamp('00:00:00', tz='US/Eastern').time():
                    return dt.strftime('%Y-%m-%d')
                else:
                    return dt.strftime('%Y-%m-%d %H:%M')
            df_display['Game Date'] = df_display['Game Date'].apply(format_date)
            
            # Map team abbreviations to full names with fallback
            def safe_map_team(abbrev):
                if pd.isna(abbrev) or abbrev is None or abbrev == "":
                    return "Unknown Team"
                full_name = team_mapping.get(abbrev, abbrev)  # Fallback to abbreviation if not in mapping
                if full_name == abbrev and abbrev != "Unknown":
                    # print(f"Warning: Team abbreviation '{abbrev}' not found in mapping")
                    pass
                return full_name
            
            df_display['Away Team'] = df_display['Away Team'].apply(safe_map_team)
            df_display['Home Team'] = df_display['Home Team'].apply(safe_map_team)
            
            # Add odds columns
            df_display['Home Moneyline'] = ''
            df_display['Away Moneyline'] = ''
            df_display['Home Spread'] = ''
            df_display['Away Spread'] = ''
            df_display['Over Total'] = ''
            df_display['Under Total'] = ''
            
            for idx, row in df_display.iterrows():
                game_odds = df_odds.iloc[idx]['odds']
                if game_odds:
                    for provider_odds in game_odds:
                        ml_home = provider_odds.get('moneyline', {}).get('home')
                        ml_away = provider_odds.get('moneyline', {}).get('away')
                        spread_home_line = provider_odds.get('spread', {}).get('home', {}).get('line')
                        spread_home_odds = provider_odds.get('spread', {}).get('home', {}).get('odds')
                        spread_away_line = provider_odds.get('spread', {}).get('away', {}).get('line')
                        spread_away_odds = provider_odds.get('spread', {}).get('away', {}).get('odds')
                        total_over_line = provider_odds.get('total', {}).get('over', {}).get('line')
                        total_over_odds = provider_odds.get('total', {}).get('over', {}).get('odds')
                        total_under_line = provider_odds.get('total', {}).get('under', {}).get('line')
                        total_under_odds = provider_odds.get('total', {}).get('under', {}).get('odds')
                        
                        # Clean total lines
                        total_over_line_clean = total_over_line.lstrip('o') if total_over_line else None
                        total_under_line_clean = total_under_line.lstrip('u') if total_under_line else None
                        
                        if ml_home:
                            df_display.at[idx, 'Home Moneyline'] = ml_home
                        if ml_away:
                            df_display.at[idx, 'Away Moneyline'] = ml_away
                        if spread_home_line and spread_home_odds:
                            df_display.at[idx, 'Home Spread'] = f"{spread_home_line} ({spread_home_odds})"
                        if spread_away_line and spread_away_odds:
                            df_display.at[idx, 'Away Spread'] = f"{spread_away_line} ({spread_away_odds})"
                        if total_over_line_clean and total_over_odds:
                            df_display.at[idx, 'Over Total'] = f"{total_over_line_clean} ({total_over_odds})"
                        if total_under_line_clean and total_under_odds:
                            df_display.at[idx, 'Under Total'] = f"{total_under_line_clean} ({total_under_odds})"
            
            st.dataframe(df_display, width='stretch', hide_index=True, height=get_dataframe_height(df_display))
        else:
            st.info("No games with odds found.")
            
    except Exception as e:
        st.error(f"Error fetching odds: {str(e)}")

# Footer
st.markdown("---")
st.markdown("*Built with Streamlit • Data from NHL APIs • For entertainment purposes only*")