"""Identify bets with positive expected value."""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.api.nhl_client import NHLClient
from footer import add_betting_oracle_footer

st.set_page_config(page_title="Value Finder", page_icon="💰", layout="wide")
st.title("💰 Value Finder")

st.markdown("""
Find bets where the model's probability exceeds the implied odds.
A **positive edge** suggests potential value.

*Note: This is a placeholder implementation. Full value calculation requires prediction models.*
""")

# Initialize client
@st.cache_resource
def get_client():
    return NHLClient()

client = get_client()

# Filters
col1, col2, col3 = st.columns(3)
with col1:
    min_edge = st.slider("Minimum Edge %", 0, 20, 3)
with col2:
    bet_types = st.multiselect("Bet Types", ["Moneyline", "Puck Line", "Totals"], default=["Moneyline"])
with col3:
    confidence = st.selectbox("Model Confidence", ["All", "High", "Medium", "Low"])

# Get today's games and odds
st.subheader("Today's Betting Odds")

try:
    odds_data = client.get_espn_odds(days_ahead=7)
    
    if odds_data:
        odds_list = []
        for game in odds_data:
            if game.get("odds"):
                provider = game["odds"][0]
                
                # Parse odds
                home_ml = provider.get("moneyline", {}).get("home")
                away_ml = provider.get("moneyline", {}).get("away")
                
                # Calculate implied probability from American odds
                def implied_prob(odds):
                    if odds is None:
                        return None
                    try:
                        odds = float(odds)
                        if odds > 0:
                            return 100 / (odds + 100)
                        else:
                            return abs(odds) / (abs(odds) + 100)
                    except:
                        return None
                
                home_impl = implied_prob(home_ml)
                away_impl = implied_prob(away_ml)
                
                # Get spread info
                home_spread_line = provider.get("spread", {}).get("home", {}).get("line")
                home_spread_odds = provider.get("spread", {}).get("home", {}).get("odds")
                
                # Get total info
                over_line = provider.get("total", {}).get("over", {}).get("line")
                over_odds = provider.get("total", {}).get("over", {}).get("odds")
                under_odds = provider.get("total", {}).get("under", {}).get("odds")
                
                odds_list.append({
                    "Game": game.get("name", ""),
                    "Home Team": game.get("home_team", ""),
                    "Away Team": game.get("away_team", ""),
                    "Home ML": home_ml if home_ml else "N/A",
                    "Away ML": away_ml if away_ml else "N/A",
                    "Home Impl%": f"{home_impl:.1%}" if home_impl else "N/A",
                    "Away Impl%": f"{away_impl:.1%}" if away_impl else "N/A",
                    "Spread": f"{home_spread_line}" if home_spread_line else "N/A",
                    "Total": f"{over_line}" if over_line else "N/A",
                    "Provider": provider.get("provider", "DraftKings")
                })
        
        if odds_list:
            odds_df = pd.DataFrame(odds_list)
            
            st.dataframe(
                odds_df,
                width='stretch',
                hide_index=True,
                column_config={
                    "Game": st.column_config.TextColumn("Matchup", width="large"),
                    "Home Team": st.column_config.TextColumn("Home", width="small"),
                    "Away Team": st.column_config.TextColumn("Away", width="small"),
                    "Home ML": st.column_config.TextColumn("Home ML", width="small"),
                    "Away ML": st.column_config.TextColumn("Away ML", width="small"),
                    "Home Impl%": st.column_config.TextColumn("Home Prob", width="small", help="Implied probability from odds"),
                    "Away Impl%": st.column_config.TextColumn("Away Prob", width="small", help="Implied probability from odds"),
                    "Spread": st.column_config.TextColumn("Spread", width="small"),
                    "Total": st.column_config.TextColumn("Total", width="small"),
                }
            )
            
            # Show sample calculation
            st.divider()
            st.subheader("How It Works")
            st.markdown("""
            **Value betting** occurs when your estimated probability of an outcome is higher than the implied probability from the odds.
            
            **Example:**
            - Odds: -150 (Implied: 60%)
            - Your Model: 65% win probability
            - **Edge:** +5% (65% - 60%)
            
            **Kelly Criterion** suggests bet sizing based on edge:
            - Kelly % = (Model Prob × (Odds + 1) - 1) / Odds
            
            *Full implementation coming with prediction models in Phase 2.*
            """)
        else:
            st.info("No odds data available.")
    else:
        st.info("Unable to fetch odds data.")
        
except Exception as e:
    st.error(f"Error loading odds: {e}")

# Placeholder value bets section
st.divider()
st.subheader("Identified Value Bets")
st.info("🚧 Value calculation requires prediction models. See roadmap for implementation timeline.")

# Show what value bets would look like
st.markdown("**Sample Format (Coming Soon):**")
sample_df = pd.DataFrame({
    "Game": ["TOR @ MTL", "BOS @ NYR", "COL @ VGK"],
    "Bet": ["MTL ML", "Under 6.0", "COL -1.5"],
    "Odds": ["+125", "-110", "+145"],
    "Model Prob": ["48%", "58%", "42%"],
    "Implied": ["44%", "52%", "41%"],
    "Edge": ["+4.0%", "+6.0%", "+1.0%"],
    "Kelly": ["2.1%", "3.2%", "0.5%"]
})

st.dataframe(sample_df, width='stretch', hide_index=True)

# Add footer
add_betting_oracle_footer()
