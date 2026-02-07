"""Model performance dashboard."""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import date, timedelta

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from src.utils.prediction_storage import (
    load_predictions_for_date,
    load_game_results,
    match_predictions_to_results,
    daily_evaluation
)
from src.models.evaluation import (
    calculate_accuracy,
    calculate_mae,
    calculate_rmse,
    calibration_buckets,
    calibration_error,
    PredictionResult
)
from src.utils.styles import apply_custom_css
from footer import add_betting_oracle_footer

st.set_page_config(page_title="Oracle on Ice - Hockey Predictions", page_icon="📊", layout="wide")
apply_custom_css()

st.title("📊 Model Performance")
st.markdown("Track prediction accuracy and identify areas for improvement.")

# Load evaluation data for last 7 days
all_predictions = []
for days_ago in range(7):
    check_date = date.today() - timedelta(days=days_ago)
    preds = load_predictions_for_date(check_date)
    results = load_game_results()
    matched = match_predictions_to_results(preds, results)
    all_predictions.extend(matched)

# Calculate aggregate metrics
if all_predictions:
    eval_data = {
        "games_evaluated": len(all_predictions),
        "accuracy": calculate_accuracy(all_predictions),
        "mae_total": calculate_mae(all_predictions, "total"),
        "mae_home": calculate_mae(all_predictions, "home_goals"),
        "mae_away": calculate_mae(all_predictions, "away_goals"),
        "calibration": calibration_error(all_predictions)
    }
else:
    eval_data = {
        "games_evaluated": 0,
        "accuracy": 0,
        "mae_total": 0,
        "mae_home": 0,
        "mae_away": 0,
        "calibration": 0
    }

# Summary metrics
st.subheader("Recent Performance (Last 7 Days)")

col1, col2, col3, col4 = st.columns(4)
with col1:
    accuracy = eval_data.get("accuracy", 0) * 100
    st.metric("Win Prediction Accuracy", f"{accuracy:.1f}%", 
              help="Percentage of correct win/loss predictions")
with col2:
    mae_total = eval_data.get("mae_total", 0)
    quality = "🟢 Excellent" if mae_total < 1.0 else "🟡 Good" if mae_total < 1.5 else "🟠 Fair"
    st.metric("MAE (Total Goals)", f"{mae_total:.2f}", 
              delta=quality,
              help="Mean Absolute Error for total goals prediction")
with col3:
    games_eval = eval_data.get("games_evaluated", 0)
    st.metric("Games Evaluated", games_eval,
              help="Number of predictions with known results")
with col4:
    calib = eval_data.get("calibration", 0)
    calib_quality = "🟢 Good" if calib < 0.05 else "🟡 Fair" if calib < 0.10 else "🟠 Needs Work"
    st.metric("Calibration Error", f"{calib:.3f}",
              delta=calib_quality,
              help="How well predicted probabilities match outcomes (lower is better)")

# Tabs for different views
tab1, tab2, tab3 = st.tabs([
    "Goal Predictions", 
    "Calibration", 
    "Evaluation Guide"
])

with tab1:
    st.markdown("### Goal Prediction Accuracy")
    
    if eval_data.get("games_evaluated", 0) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Mean Absolute Error (MAE)**")
            mae_data = pd.DataFrame({
                "Prediction Type": ["Total Goals", "Home Goals", "Away Goals"],
                "MAE": [
                    eval_data.get("mae_total", 0),
                    eval_data.get("mae_home", 0),
                    eval_data.get("mae_away", 0)
                ]
            })
            st.dataframe(mae_data, hide_index=True, use_container_width=True)
            
            st.info("""
            **MAE Interpretation:**
            - < 1.0: 🟢 Excellent
            - 1.0-1.5: 🟡 Good
            - 1.5-2.0: 🟠 Fair
            - > 2.0: 🔴 Poor
            """)
        
        with col2:
            st.markdown("**Sample Statistics**")
            st.write(f"**Games Analyzed:** {eval_data.get('games_evaluated', 0)}")
            st.write(f"**Accuracy:** {eval_data.get('accuracy', 0) * 100:.1f}%")
            
            # Profitability threshold
            breakeven_accuracy = 52.4  # At -110 odds
            if accuracy >= breakeven_accuracy:
                st.success(f"✅ Above breakeven threshold ({breakeven_accuracy}%)")
            else:
                st.warning(f"⚠️ Below breakeven threshold ({breakeven_accuracy}%)")
    else:
        st.info("No predictions with results yet. Results will be tracked automatically as games are completed.")

with tab2:
    st.markdown("### Probability Calibration")
    
    st.markdown("""
    Well-calibrated models have predicted probabilities that match actual outcomes.
    For example, games where we predict 70% home win probability should see the home team win ~70% of the time.
    """)
    
    # Use already loaded predictions from above
    if all_predictions:
        buckets = calibration_buckets(all_predictions, n_buckets=10)
        
        if buckets:
            bucket_df = pd.DataFrame(buckets, columns=["Predicted Prob", "Actual Win Rate", "Count"])
            
            st.dataframe(bucket_df, hide_index=True, use_container_width=True)
            
            # Visualize calibration
            st.line_chart(bucket_df.set_index("Predicted Prob")["Actual Win Rate"])
            
            calib_err = calibration_error(all_predictions)
            if calib_err < 0.05:
                st.success(f"✅ Well calibrated! (ECE: {calib_err:.3f})")
            elif calib_err < 0.10:
                st.info(f"🟡 Acceptable calibration (ECE: {calib_err:.3f})")
            else:
                st.warning(f"⚠️ Poor calibration - model needs adjustment (ECE: {calib_err:.3f})")
        else:
            st.info("Not enough data for calibration analysis (need 20+ predictions)")
    else:
        st.info("No predictions with results yet for calibration analysis.")

with tab3:
    st.markdown("### Evaluation Metrics Guide")
    
    st.markdown("""
    #### Classification Metrics (Win/Loss Predictions)
    
    | Metric | Description | Target |
    |--------|-------------|--------|
    | **Accuracy** | % of correct win predictions | > 52.4% for profit at -110 odds |
    | **Calibration Error** | How well probabilities match reality | < 0.05 is excellent |
    
    #### Regression Metrics (Goal Predictions)
    
    | Metric | Description | Target |
    |--------|-------------|--------|
    | **MAE** | Mean Absolute Error | < 1.2 goals |
    | **RMSE** | Root Mean Square Error | < 1.5 goals |
    
    #### Minimum Sample Sizes for Confidence
    
    - **Accuracy**: 100+ games
    - **MAE**: 50+ games
    - **Calibration**: 500+ predictions
    - **ROI**: 200+ bets
    
    #### When to Retrain Model
    
    1. Accuracy drops 3%+ over 2 weeks
    2. MAE increases by 0.2+ goals sustained
    3. Calibration error > 0.10
    4. Major roster changes (trades, injuries)
    5. Season transitions (regular → playoffs)
    
    #### Avoiding Overfitting
    
    - Always split data **temporally** (not randomly)
    - Never use future data to predict past
    - Test on out-of-sample games only
    - Monitor performance on new predictions
    """)

# Footer note
st.markdown("---")
st.caption("""
💡 **Tip:** Consistent prediction tracking is key to model improvement. 
Results are tracked automatically as games are completed.
""")

add_betting_oracle_footer()
