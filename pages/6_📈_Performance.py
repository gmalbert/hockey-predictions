"""Track betting recommendation performance and ROI."""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from pathlib import Path
import sys
from collections import defaultdict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.api.nhl_client import NHLClient
from src.utils.bet_storage import (
    load_recommendations, get_performance_metrics, 
    get_recommendations_by_type, evaluate_recommendations
)
from footer import add_betting_oracle_footer

st.set_page_config(page_title="Oracle on Ice - Hockey Predictions", page_icon="📈", layout="wide")
st.title("📈 Model Performance Tracker")

st.markdown("""
Track how well the model's betting recommendations perform against actual game results.
All recommendations are automatically tracked when the model identifies positive expected value.
""")

# Initialize client
@st.cache_resource
def get_client():
    return NHLClient()

client = get_client()

# Load logo
logo_path = Path("data_files/logo.png")
if logo_path.exists():
    st.sidebar.image(str(logo_path), width=150)

# Evaluate recommendations against results
st.sidebar.divider()
with st.sidebar:
    st.subheader("🔄 Update Results")
    if st.button("Evaluate Recommendations", width='stretch', help="Match recommendations with game results"):
        with st.spinner("Evaluating..."):
            evaluate_recommendations()
            st.success("✅ Recommendations evaluated!")
            st.rerun()

# Load all recommendations
all_recs = load_recommendations()
metrics = get_performance_metrics(all_recs)

# Summary metrics
st.subheader("Recommendation Performance Summary")

if all_recs:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Recommendations", metrics["total_recommendations"], help="Total betting recommendations made")
    with col2:
        st.metric("Win Rate", f"{metrics['win_rate']:.1f}%", help="Percentage of winning recommendations (evaluated only)")
    with col3:
        profit_str = f"{metrics['total_profit']:+.2f}u"
        st.metric("Units Profit", profit_str, help="Total profit at 1 unit per bet")
    with col4:
        roi_str = f"{metrics['roi']:+.1f}%"
        st.metric("ROI", roi_str, help="Return on investment")
    
    # Additional stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.caption(f"✅ Wins: {metrics['wins']}")
    with col2:
        st.caption(f"❌ Losses: {metrics['losses']}")
    with col3:
        st.caption(f"⏳ Pending: {metrics['pending']}")
    with col4:
        st.caption(f"📊 Avg Edge: {metrics['avg_edge']:.1f}%")
else:
    st.info("👋 No recommendations tracked yet. The model will automatically save recommendations when it identifies positive expected value bets.")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Recommendations", "0", help="Total betting recommendations made")
    with col2:
        st.metric("Win Rate", "—", help="Percentage of winning recommendations")
    with col3:
        st.metric("Units Profit", "—", help="Total profit at 1 unit per bet")
    with col4:
        st.metric("ROI", "—", help="Return on investment")

# Performance chart
st.subheader("Cumulative Profit (Units)")

if all_recs:
    # Sort recommendations by date and calculate cumulative profit
    evaluated_recs = [r for r in all_recs if r.get("won") is not None]
    
    if evaluated_recs:
        # Sort by date
        evaluated_recs_sorted = sorted(evaluated_recs, key=lambda x: x["date"])
        
        dates = []
        cumulative_profit = []
        profit = 0.0
        
        for rec in evaluated_recs_sorted:
            dates.append(datetime.strptime(rec["date"], "%Y-%m-%d"))
            
            # Calculate profit for this recommendation
            if rec["won"]:
                from src.utils.bet_storage import calculate_profit
                profit += calculate_profit(rec["odds"], 1.0)
            else:
                profit -= 1.0
            
            cumulative_profit.append(profit)
        
        chart_df = pd.DataFrame({
            "Date": dates,
            "Units": cumulative_profit
        })
        
        st.line_chart(chart_df.set_index("Date"), height=300)
    else:
        st.info("No evaluated recommendations yet. Chart will appear once recommendations are evaluated against game results.")
else:
    st.info("Add recommendations to see your performance chart!")

# Breakdown by bet type
st.divider()
st.subheader("Performance by Bet Type")

if all_recs:
    col1, col2, col3 = st.columns(3)
    
    # Moneyline recommendations
    ml_recs = get_recommendations_by_type("Moneyline", all_recs)
    ml_metrics = get_performance_metrics(ml_recs)
    
    with col1:
        st.markdown("**Moneyline**")
        st.metric("Recommendations", ml_metrics["evaluated"])
        st.metric("Win Rate", f"{ml_metrics['win_rate']:.1f}%" if ml_metrics['evaluated'] > 0 else "—")
        st.metric("ROI", f"{ml_metrics['roi']:+.1f}%" if ml_metrics['evaluated'] > 0 else "—")
    
    # Puck Line recommendations
    pl_recs = get_recommendations_by_type("Puck Line", all_recs)
    pl_metrics = get_performance_metrics(pl_recs)
    
    with col2:
        st.markdown("**Puck Line**")
        st.metric("Recommendations", pl_metrics["evaluated"])
        st.metric("Win Rate", f"{pl_metrics['win_rate']:.1f}%" if pl_metrics['evaluated'] > 0 else "—")
        st.metric("ROI", f"{pl_metrics['roi']:+.1f}%" if pl_metrics['evaluated'] > 0 else "—")
    
    # Totals recommendations (Over/Under)
    over_recs = get_recommendations_by_type("Over", all_recs)
    under_recs = get_recommendations_by_type("Under", all_recs)
    totals_recs = over_recs + under_recs
    totals_metrics = get_performance_metrics(totals_recs)
    
    with col3:
        st.markdown("**Totals (O/U)**")
        st.metric("Recommendations", totals_metrics["evaluated"])
        st.metric("Win Rate", f"{totals_metrics['win_rate']:.1f}%" if totals_metrics['evaluated'] > 0 else "—")
        st.metric("ROI", f"{totals_metrics['roi']:+.1f}%" if totals_metrics['evaluated'] > 0 else "—")
else:
    st.info("Performance breakdown will appear here once you have recommendations.")

# Recommendation history
st.divider()
st.subheader("Recommendation History")

if all_recs:
    # Sort recommendations by date (most recent first)
    sorted_recs = sorted(all_recs, key=lambda x: (x["date"], x["id"]), reverse=True)
    
    # Prepare dataframe
    history_data = []
    for rec in sorted_recs:
        # Format profit
        if rec.get("won") is not None:
            from src.utils.bet_storage import calculate_profit
            if rec["won"]:
                profit = calculate_profit(rec["odds"], 1.0)
                profit_str = f"+{profit:.2f}u"
                result_str = "✅ Won"
            else:
                profit_str = "-1.00u"
                result_str = "❌ Lost"
        else:
            profit_str = "—"
            result_str = "⏳ Pending"
        
        history_data.append({
            "ID": rec["id"],
            "Date": rec["date"],
            "Matchup": rec["matchup"],
            "Bet Type": rec["bet_type"],
            "Recommendation": rec["recommendation"],
            "Odds": rec["odds"],
            "Edge": f"{rec['edge_percent']:.1f}%",
            "Result": result_str,
            "Profit": profit_str
        })
    
    df = pd.DataFrame(history_data)
    
    st.dataframe(
        df,
        width='stretch',
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn("#", width="small"),
            "Date": st.column_config.TextColumn("Date", width="small"),
            "Matchup": st.column_config.TextColumn("Matchup", width="medium"),
            "Bet Type": st.column_config.TextColumn("Type", width="small"),
            "Recommendation": st.column_config.TextColumn("Bet", width="small"),
            "Odds": st.column_config.TextColumn("Odds", width="small"),
            "Edge": st.column_config.TextColumn("Edge", width="small"),
            "Result": st.column_config.TextColumn("Result", width="small"),
            "Profit": st.column_config.TextColumn("Profit", width="small"),
        }
    )
else:
    st.info("Your recommendation history will appear here. The model automatically tracks recommendations when it identifies positive expected value.")

# Monthly breakdown
st.divider()
st.subheader("Monthly Performance")

if all_recs:
    # Group recommendations by month
    monthly_data = defaultdict(lambda: {"recs": [], "total_profit": 0.0})
    
    from src.utils.bet_storage import calculate_profit
    
    for rec in all_recs:
        if rec.get("won") is not None:
            rec_date = datetime.strptime(rec["date"], "%Y-%m-%d")
            month_key = rec_date.strftime("%B %Y")
            
            monthly_data[month_key]["recs"].append(rec)
            
            # Calculate profit
            if rec["won"]:
                monthly_data[month_key]["total_profit"] += calculate_profit(rec["odds"], 1.0)
            else:
                monthly_data[month_key]["total_profit"] -= 1.0
    
    # Prepare dataframe
    if monthly_data:
        monthly_rows = []
        for month, data in sorted(monthly_data.items(), key=lambda x: datetime.strptime(x[0], "%B %Y"), reverse=True):
            wins = len([r for r in data["recs"] if r["won"]])
            total_recs = len(data["recs"])
            win_rate = (wins / total_recs * 100) if total_recs > 0 else 0.0
            roi = (data["total_profit"] / total_recs * 100) if total_recs > 0 else 0.0
            
            monthly_rows.append({
                "Month": month,
                "Recommendations": total_recs,
                "Win Rate": f"{win_rate:.1f}%",
                "Units": f"{data['total_profit']:+.2f}",
                "ROI": f"{roi:+.1f}%"
            })
        
        monthly_df = pd.DataFrame(monthly_rows)
        st.dataframe(monthly_df, width='stretch', hide_index=True)
    else:
        st.info("Monthly breakdown will appear once you have evaluated recommendations.")
else:
    st.info("Monthly performance breakdown will appear here.")

# How it works
st.divider()
st.info("""
**📊 How Recommendation Tracking Works:**
- **Automatic tracking**: The model automatically saves recommendations when it identifies positive expected value
- **Edge-based**: Only bets with a calculated edge are recommended
- **1 unit per bet**: Performance is calculated assuming 1 unit wagered per recommendation
- **Evaluation**: Click "Evaluate Recommendations" to match predictions with actual game results
- **Performance metrics**: Win rate, ROI, and profit are calculated from evaluated recommendations only
- **Bet types tracked**: Moneyline, Puck Line (+1.5/-1.5), and Totals (Over/Under)

**💡 Understanding the Metrics:**
- **Edge %**: The difference between the model's probability and the implied odds probability
- **ROI**: Return on investment - profit divided by total amount staked
- **Win Rate**: Percentage of recommendations that won (evaluated only)
- **Pending**: Recommendations that haven't been matched to game results yet
""")

# Add footer
add_betting_oracle_footer()
