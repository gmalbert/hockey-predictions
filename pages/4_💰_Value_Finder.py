"""Identify bets with positive expected value."""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.api.nhl_client import NHLClient
from src.models.expected_goals import TeamMetrics, calculate_expected_goals
from src.models.win_probability import calculate_win_probability
from src.models.totals import predict_total
from src.utils.odds import calculate_edge, american_to_implied
from footer import add_betting_oracle_footer

st.set_page_config(page_title="Value Finder", page_icon="💰", layout="wide")
st.title("💰 Value Finder")

st.markdown("""
Find bets where the model's probability exceeds the implied odds.
A **positive edge** suggests potential value.
""")

# Initialize client
@st.cache_resource
def get_client():
    return NHLClient()

client = get_client()

# Filters
col1, col2, col3 = st.columns(3)
with col1:
    min_edge = st.slider("Minimum Edge %", 0.0, 20.0, 2.0, 0.5)
with col2:
    bet_types = st.multiselect("Bet Types", ["Moneyline", "Totals"], default=["Moneyline", "Totals"])
with col3:
    show_all = st.checkbox("Show All Bets", value=False, help="Show bets even without positive edge")

# Get today's games with predictions
st.subheader("🎯 Value Bets Today")

try:
    from datetime import date
    today = date.today()
    date_str = today.strftime("%Y-%m-%d")
    
    # Get schedule and odds
    schedule = client.get_schedule(date_str)
    odds_data = client.get_espn_odds(days_ahead=1)
    
    games_list = []
    for game_week in schedule.get("gameWeek", []):
        for game in game_week.get("games", []):
            if game.get("gameType") in [2, 3]:
                games_list.append(game)
    
    value_bets = []
    
    if games_list and odds_data:
        for game in games_list:
            try:
                away_abbrev = game.get("awayTeam", {}).get("abbrev", "")
                home_abbrev = game.get("homeTeam", {}).get("abbrev", "")
                
                # Get team stats
                home_stats = client.get_team_summary(home_abbrev)
                away_stats = client.get_team_summary(away_abbrev)
                
                if not home_stats or not away_stats:
                    continue
                
                # Create TeamMetrics
                home_metrics = TeamMetrics(
                    team=home_abbrev,
                    goals_for_pg=home_stats['goals_for_pg'],
                    goals_against_pg=home_stats['goals_against_pg'],
                    shots_for_pg=home_stats.get('shots_for_pg', 30),
                    shots_against_pg=home_stats.get('shots_against_pg', 30),
                    pp_pct=home_stats['pp_pct'],
                    pk_pct=home_stats['pk_pct']
                )
                
                away_metrics = TeamMetrics(
                    team=away_abbrev,
                    goals_for_pg=away_stats['goals_for_pg'],
                    goals_against_pg=away_stats['goals_against_pg'],
                    shots_for_pg=away_stats.get('shots_for_pg', 30),
                    shots_against_pg=away_stats.get('shots_against_pg', 30),
                    pp_pct=away_stats['pp_pct'],
                    pk_pct=away_stats['pk_pct']
                )
                
                # Calculate predictions
                home_xg, away_xg = calculate_expected_goals(home_metrics, away_metrics)
                probs = calculate_win_probability(home_xg, away_xg)
                
                # Find odds for this game
                matchup = f"{away_abbrev} @ {home_abbrev}"
                game_odds = None
                for odds_game in odds_data:
                    if away_abbrev in odds_game.get("name", "") and home_abbrev in odds_game.get("name", ""):
                        game_odds = odds_game
                        break
                
                if game_odds and game_odds.get("odds"):
                    provider = game_odds["odds"][0]
                    home_ml = provider.get("moneyline", {}).get("home")
                    away_ml = provider.get("moneyline", {}).get("away")
                    
                    # Moneyline bets
                    if "Moneyline" in bet_types:
                        if home_ml:
                            home_edge_data = calculate_edge(probs.home_win, int(home_ml))
                            if show_all or home_edge_data["has_value"]:
                                value_bets.append({
                                    "Game": matchup,
                                    "Bet": f"{home_abbrev} ML",
                                    "Odds": int(home_ml),
                                    "Model Prob": f"{home_edge_data['model_prob']:.1f}%",
                                    "Implied": f"{home_edge_data['implied_prob']:.1f}%",
                                    "Edge": f"{home_edge_data['edge_pct']:+.1f}%",
                                    "Kelly": f"{home_edge_data['kelly_fraction']:.2%}",
                                    "Recommendation": "✅ BET" if home_edge_data["edge_pct"] >= min_edge else ("⚠️ Small Edge" if home_edge_data["has_value"] else "❌ No Value")
                                })
                        
                        if away_ml:
                            away_edge_data = calculate_edge(probs.away_win, int(away_ml))
                            if show_all or away_edge_data["has_value"]:
                                value_bets.append({
                                    "Game": matchup,
                                    "Bet": f"{away_abbrev} ML",
                                    "Odds": int(away_ml),
                                    "Model Prob": f"{away_edge_data['model_prob']:.1f}%",
                                    "Implied": f"{away_edge_data['implied_prob']:.1f}%",
                                    "Edge": f"{away_edge_data['edge_pct']:+.1f}%",
                                    "Kelly": f"{away_edge_data['kelly_fraction']:.2%}",
                                    "Recommendation": "✅ BET" if away_edge_data["edge_pct"] >= min_edge else ("⚠️ Small Edge" if away_edge_data["has_value"] else "❌ No Value")
                                })
                    
                    # Totals bets
                    if "Totals" in bet_types:
                        over_line = provider.get("total", {}).get("over", {}).get("line")
                        over_odds = provider.get("total", {}).get("over", {}).get("odds")
                        under_odds = provider.get("total", {}).get("under", {}).get("odds")
                        
                        if over_line and over_odds and under_odds:
                            totals_pred = predict_total(home_xg, away_xg, float(over_line))
                            
                            over_edge_data = calculate_edge(totals_pred.over_prob, int(over_odds))
                            if show_all or over_edge_data["has_value"]:
                                value_bets.append({
                                    "Game": matchup,
                                    "Bet": f"Over {over_line}",
                                    "Odds": int(over_odds),
                                    "Model Prob": f"{over_edge_data['model_prob']:.1f}%",
                                    "Implied": f"{over_edge_data['implied_prob']:.1f}%",
                                    "Edge": f"{over_edge_data['edge_pct']:+.1f}%",
                                    "Kelly": f"{over_edge_data['kelly_fraction']:.2%}",
                                    "Recommendation": "✅ BET" if over_edge_data["edge_pct"] >= min_edge else ("⚠️ Small Edge" if over_edge_data["has_value"] else "❌ No Value")
                                })
                            
                            under_edge_data = calculate_edge(totals_pred.under_prob, int(under_odds))
                            if show_all or under_edge_data["has_value"]:
                                value_bets.append({
                                    "Game": matchup,
                                    "Bet": f"Under {over_line}",
                                    "Odds": int(under_odds),
                                    "Model Prob": f"{under_edge_data['model_prob']:.1f}%",
                                    "Implied": f"{under_edge_data['implied_prob']:.1f}%",
                                    "Edge": f"{under_edge_data['edge_pct']:+.1f}%",
                                    "Kelly": f"{under_edge_data['kelly_fraction']:.2%}",
                                    "Recommendation": "✅ BET" if under_edge_data["edge_pct"] >= min_edge else ("⚠️ Small Edge" if under_edge_data["has_value"] else "❌ No Value")
                                })
                
            except Exception as e:
                st.warning(f"Error processing game {away_abbrev} @ {home_abbrev}: {e}")
                continue
        
        # Display value bets
        if value_bets:
            # Filter by minimum edge
            if not show_all:
                value_bets = [bet for bet in value_bets if float(bet["Edge"].replace("%", "").replace("+", "")) >= min_edge]
            
            if value_bets:
                df = pd.DataFrame(value_bets)
                st.dataframe(
                    df,
                    width='stretch',
                    hide_index=True,
                    column_config={
                        "Game": st.column_config.TextColumn("Matchup", width="medium"),
                        "Bet": st.column_config.TextColumn("Bet", width="small"),
                        "Odds": st.column_config.NumberColumn("Odds", width="small"),
                        "Model Prob": st.column_config.TextColumn("Model", width="small"),
                        "Implied": st.column_config.TextColumn("Implied", width="small"),
                        "Edge": st.column_config.TextColumn("Edge", width="small"),
                        "Kelly": st.column_config.TextColumn("Kelly %", width="small"),
                        "Recommendation": st.column_config.TextColumn("Action", width="medium"),
                    }
                )
                
                # Summary stats
                st.divider()
                good_bets = [b for b in value_bets if "✅" in b["Recommendation"]]
                if good_bets:
                    st.success(f"🎯 Found {len(good_bets)} recommended bet(s) with edge ≥ {min_edge:.1f}%")
                else:
                    st.info(f"No bets meet the minimum edge threshold of {min_edge:.1f}%")
            else:
                st.info(f"No bets found with edge ≥ {min_edge:.1f}%. Try lowering the minimum edge or enabling 'Show All Bets'.")
        else:
            st.info("No betting opportunities found for today's games.")
    else:
        st.warning("No games or odds data available for today.")

except Exception as e:
    st.error(f"Error calculating value bets: {e}")
    import traceback
    st.code(traceback.format_exc())

# How it works section
st.divider()
st.subheader("📖 How It Works")
st.markdown("""
**Value betting** occurs when your estimated probability of an outcome is higher than the implied probability from the odds.

**Example:**
- Odds: -150 (Implied: 60%)
- Model Prediction: 65% win probability
- **Edge:** +5% (65% - 60%)

**Kelly Criterion** suggests optimal bet sizing based on your edge:
- Kelly % = (Decimal Odds × Model Prob - 1) / (Decimal Odds - 1)
- Conservative approach: Use 25-50% of Kelly recommendation

**Recommendations:**
- ✅ **BET**: Edge meets your minimum threshold
- ⚠️ **Small Edge**: Positive edge but below threshold
- ❌ **No Value**: Negative edge, avoid bet
""")

# Add footer
add_betting_oracle_footer()
