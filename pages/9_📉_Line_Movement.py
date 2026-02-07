"""Line movement tracking page."""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from src.utils.odds_storage import save_odds_snapshot, get_game_odds_history, get_todays_movements, get_all_odds_files
from src.models.line_movement import analyze_moneyline_movement, analyze_total_movement
from src.utils.styles import apply_custom_css
from footer import add_betting_oracle_footer

st.set_page_config(page_title="Oracle on Ice - Hockey Predictions", page_icon="📉", layout="wide")
apply_custom_css()

st.title("📉 Line Movement Tracker")

st.markdown("""
Track line movements to identify sharp action and betting opportunities.
- **Steam moves**: Fast, significant line changes (sharp money)
- **Reverse line**: Movement against public betting
- **Half-point total moves**: Often indicate sharp action
""")

# Today's significant moves
st.subheader("Notable Movements")

movements = get_todays_movements()
if movements:
    movements_data = []
    for move in movements:
        # Determine signal
        ml_move = move["ml_move"]
        total_move = move["total_move"]
        
        signal = []
        if abs(ml_move) >= 20:
            signal.append("🔥 Steam ML")
        elif abs(ml_move) >= 10:
            signal.append("📈 ML Move")
        
        if abs(total_move) >= 0.5:
            direction = "Over" if total_move > 0 else "Under"
            signal.append(f"⚡ Sharp {direction}")
        
        movements_data.append({
            "Game": move["matchup"],
            "Open ML": move["opening_ml"],
            "Current ML": move["current_ml"],
            "ML Move": f"{ml_move:+d}",
            "Open Total": move["opening_total"],
            "Current Total": move["current_total"],
            "Total Move": f"{total_move:+.1f}",
            "Signal": " | ".join(signal) if signal else "Stable"
        })
    
    movements_df = pd.DataFrame(movements_data)
    st.dataframe(movements_df, use_container_width=True, hide_index=True)
else:
    st.info("No significant line movements detected. Record odds below to start tracking.")

# Tracked games overview
st.subheader("Tracked Games")

tracked_files = get_all_odds_files()
if tracked_files:
    tracked_df = pd.DataFrame(tracked_files)
    st.dataframe(tracked_df, use_container_width=True, hide_index=True)
    
    # Game selection for detailed view
    if tracked_files:
        selected_game = st.selectbox(
            "Select game for detailed movement",
            [f"{g['matchup']} ({g['game_id']})" for g in tracked_files]
        )
        
        if selected_game:
            game_id = selected_game.split("(")[-1].strip(")")
            odds_history = get_game_odds_history(game_id)
            
            if odds_history and odds_history.get("snapshots"):
                st.subheader(f"Movement Chart - {selected_game.split('(')[0].strip()}")
                
                snapshots = odds_history["snapshots"]
                
                # Build dataframe for charting
                chart_data = {
                    "Time": [s["timestamp"][:19] for s in snapshots],
                    "Home ML": [s["home_ml"] for s in snapshots],
                    "Total": [s["total"] for s in snapshots]
                }
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### Moneyline Movement")
                    ml_df = pd.DataFrame({
                        "Home ML": chart_data["Home ML"]
                    })
                    st.line_chart(ml_df)
                
                with col2:
                    st.markdown("### Total Movement")
                    total_df = pd.DataFrame({
                        "Total": chart_data["Total"]
                    })
                    st.line_chart(total_df)
                
                # Analysis
                if len(snapshots) >= 2:
                    opening = snapshots[0]
                    current = snapshots[-1]
                    
                    # Estimate hours until game (placeholder)
                    hours_until = 2.0  # Would calculate from game time
                    
                    ml_analysis = analyze_moneyline_movement(
                        opening["home_ml"],
                        current["home_ml"],
                        hours_until
                    )
                    
                    total_analysis = analyze_total_movement(
                        opening["total"],
                        current["total"],
                        opening["over_odds"],
                        current["over_odds"]
                    )
                    
                    st.subheader("Movement Analysis")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Moneyline**")
                        st.write(f"Type: {ml_analysis.movement_type.value.title()}")
                        st.write(f"Direction: {ml_analysis.direction.title()}")
                        st.write(f"Magnitude: {ml_analysis.magnitude}")
                        st.write(f"Sharp Action: {'Yes' if ml_analysis.is_sharp_action else 'No'}")
                        st.info(ml_analysis.recommendation)
                    
                    with col2:
                        st.markdown("**Total**")
                        st.write(f"Type: {total_analysis.movement_type.value.title()}")
                        st.write(f"Direction: {total_analysis.direction.title()}")
                        st.write(f"Magnitude: {total_analysis.magnitude:.1f}")
                        st.write(f"Sharp Action: {'Yes' if total_analysis.is_sharp_action else 'No'}")
                        st.info(total_analysis.recommendation)

else:
    st.info("No games tracked yet. Use the form below to start recording odds.")

# Manual odds entry
st.subheader("Record Odds Snapshot")

st.markdown("""
Manually track odds throughout the day. Key times to record:
- **Opening lines** (morning of game day)
- **Midday** (12-2 PM)
- **2 hours before game** (detect steam moves)
- **30 minutes before game** (final sharp action)
""")

# Reference guide
with st.expander("📚 Movement Interpretation Guide"):
    st.markdown("""
    ### Moneyline Movements
    - **10-15 cents**: Minor movement, watch for trend
    - **15-20 cents**: Moderate movement, possible sharp action
    - **20+ cents**: Significant movement, likely sharp money
    - **Late steam (< 2 hrs)**: High confidence sharp action
    
    ### Total Movements
    - **0.5 goals**: Significant - indicates sharp opinion
    - **1.0+ goals**: Very significant - strong sharp consensus
    - **Juice moves only**: Sharp action without moving total (smaller positions)
    
    ### Movement Types
    - **Steam**: Fast, sharp movement (follow)
    - **Drift**: Gradual movement (less significant)
    - **Reverse**: Line moves against public (very sharp)
    - **Stable**: No meaningful movement
    
    ### Best Signals
    ✅ Model agrees with line movement direction  
    ✅ Steam move within 2 hours of game  
    ✅ Model has 5%+ edge over current line  
    ✅ Reverse line movement (against public team)
    """)

add_betting_oracle_footer()
