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
from src.models.ml_predictor import NHLPredictor
from src.models.training import NHLModelTrainer
from src.utils.styles import apply_custom_css
from footer import add_betting_oracle_footer

st.set_page_config(page_title="Oracle on Ice - Hockey Predictions", page_icon="📊", layout="wide")
apply_custom_css()

# Load logo
logo_path = Path("data_files/logo.png")
if logo_path.exists():
    st.sidebar.image(str(logo_path), width=150)

# Header with refresh button
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.title("📊 Model Performance")
    st.markdown("Track prediction accuracy and identify areas for improvement.")
with header_col2:
    st.write("")  # Spacer
    if st.button("🔄 Refresh Model", help="Reload ML model from disk", width='stretch'):
        st.cache_resource.clear()
        st.rerun()

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

# Load ML model information
@st.cache_resource
def get_ml_predictor():
    predictor = NHLPredictor()
    if predictor.load():
        return predictor
    return None

ml_predictor = get_ml_predictor()
ml_model_info = ml_predictor.get_model_info() if ml_predictor else None

# Calculate ML metrics if model exists
ml_metrics = {}
if ml_model_info and ml_predictor:
    # Use model info directly instead of validation
    ml_metrics = {
        "model_type": ml_model_info.get("model_type", "Unknown"),
        "training_date": ml_model_info.get("training_date", "Unknown"),
        "feature_count": ml_model_info.get("n_features", 0),
        "has_validation": False,
        "model_available": True
    }
else:
    ml_metrics = {"model_available": False}

# Summary metrics
st.subheader("Recent Performance (Last 7 Days)")

# Rule-based model metrics
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

# ML Model Status
st.subheader("🤖 Machine Learning Model Status")

if ml_model_info and ml_metrics.get("model_available", True):  # Default to True if key doesn't exist
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        model_type = ml_model_info.get("model_type", "Not Available")
        st.metric("ML Model Type", model_type.replace('_', ' ').title(), 
                  help="Type of machine learning algorithm used")
    
    with col2:
        if ml_metrics.get("has_validation", False):
            ml_accuracy = ml_metrics.get("accuracy", 0) * 100
            st.metric("ML Accuracy", f"{ml_accuracy:.1f}%", 
                      help="ML model prediction accuracy on validation set")
        else:
            st.metric("ML Status", "Trained", 
                      help="ML model is trained and ready to use")
    
    with col3:
        feature_count = ml_model_info.get("n_features", 0)
        st.metric("Features Used", feature_count, 
                  help="Number of features used in ML model")
    
    with col4:
        training_date = ml_model_info.get("training_date", "Unknown")
        if training_date != "Unknown":
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(training_date)
                training_date_display = dt.strftime('%Y-%m-%d')
            except:
                training_date_display = training_date[:10] if len(str(training_date)) >= 10 else training_date
            st.metric("Last Trained", training_date_display, 
                      help="Date when ML model was last trained")
        else:
            st.metric("Training Status", "Unknown", 
                      help="ML model training date unknown")
else:
    st.info("🤖 **ML Model Not Available** - Train a model using the training pipeline to see ML metrics here.")

# Tabs for different views
tab1, tab2, tab3, tab4 = st.tabs([
    "Goal Predictions", 
    "Calibration", 
    "ML Model Analysis",
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
            st.dataframe(mae_data, hide_index=True, width='stretch')
            
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
            
            st.dataframe(bucket_df, hide_index=True, width='stretch')
            
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
    st.markdown("### 🤖 Machine Learning Model Analysis")
    
    # Debug info (can be removed later)
    with st.expander("🔍 Debug Info", expanded=False):
        st.write({
            "ml_predictor exists": ml_predictor is not None,
            "ml_model_info exists": ml_model_info is not None,
            "ml_metrics keys": list(ml_metrics.keys()),
            "model_available": ml_metrics.get("model_available", "key not found")
        })
        if ml_model_info:
            st.write("Model type:", ml_model_info.get("model_type"))
    
    if ml_model_info:
        # Model Information
        st.markdown("#### Model Information")
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.markdown(f"**Model Type:** {ml_model_info.get('model_type', 'Unknown').replace('_', ' ').title()}")
            training_date = ml_model_info.get('training_date', 'Unknown')
            if training_date != 'Unknown':
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(training_date)
                    training_date = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            st.markdown(f"**Training Date:** {training_date}")
            st.markdown(f"**Features Used:** {ml_model_info.get('n_features', 0)}")
        
        with info_col2:
            st.markdown(f"**Training Samples:** {ml_model_info.get('n_training_samples', 'Unknown'):,}" if isinstance(ml_model_info.get('n_training_samples'), int) else f"**Training Samples:** {ml_model_info.get('n_training_samples', 'Unknown')}")
            seasons = ml_model_info.get('seasons_used', [])
            seasons_str = ', '.join(seasons) if seasons else 'Unknown'
            st.markdown(f"**Seasons Trained:** {seasons_str}")
        
        # Feature Importance (if available)
        if 'feature_importance' in ml_model_info and ml_model_info['feature_importance']:
            st.markdown("#### Feature Importance")
            
            # Convert to DataFrame for display
            importance_data = []
            for feature, importance in ml_model_info['feature_importance'].items():
                importance_data.append({
                    'Feature': feature.replace('_', ' ').title(),
                    'Importance': importance
                })
            
            importance_df = pd.DataFrame(importance_data).sort_values('Importance', ascending=False)
            
            # Display top 10 features
            st.dataframe(importance_df.head(10), hide_index=True, width='stretch')
            
            # Feature importance chart
            st.bar_chart(importance_df.head(10).set_index('Feature'))
        
        # Training Metrics (if available)
        metrics = ml_model_info.get('metrics', {})
        if metrics:
            st.markdown("#### Training Performance")
            
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            
            with metrics_col1:
                st.markdown("**Accuracy Metrics**")
                train_acc = metrics.get('train_accuracy', 0)
                test_acc = metrics.get('test_accuracy', 0)
                cv_acc = metrics.get('cv_accuracy_mean', 0)
                
                st.metric("Training Accuracy", f"{train_acc:.1%}")
                st.metric("Test Accuracy", f"{test_acc:.1%}")
                st.metric("Cross-Val Accuracy", f"{cv_acc:.1%}")
            
            with metrics_col2:
                st.markdown("**Loss Metrics**")
                train_loss = metrics.get('train_log_loss', 0)
                test_loss = metrics.get('test_log_loss', 0)
                
                st.metric("Training Log Loss", f"{train_loss:.3f}")
                st.metric("Test Log Loss", f"{test_loss:.3f}")
                st.metric("CV Std Dev", f"{metrics.get('cv_accuracy_std', 0):.3%}")
            
            with metrics_col3:
                st.markdown("**Classification Metrics**")
                precision = metrics.get('precision', 0)
                recall = metrics.get('recall', 0)
                f1 = metrics.get('f1_score', 0)
                
                st.metric("Precision", f"{precision:.3f}")
                st.metric("Recall", f"{recall:.3f}")
                st.metric("F1 Score", f"{f1:.3f}")
        
        # Model Actions
        st.markdown("#### Model Actions")
        
        action_col1, action_col2, action_col3 = st.columns(3)
        
        with action_col1:
            if st.button("🔄 Retrain Model", help="Train a new ML model with latest data"):
                with st.spinner("Training new model..."):
                    trainer = NHLModelTrainer()
                    trainer.train_game_outcome_model()
                    st.success("Model retrained! Refresh page to see updated metrics.")
                    st.rerun()
        
        with action_col2:
            if st.button("📊 Validate Model", help="Run validation on current model"):
                with st.spinner("Validating model..."):
                    validation = ml_predictor.validate_predictions()
                    if validation:
                        st.success("Validation complete! Check metrics above.")
                        st.rerun()
                    else:
                        st.error("Validation failed. Check model and data.")
        
        with action_col3:
            if st.button("📈 Feature Analysis", help="Analyze feature correlations"):
                st.info("Feature analysis coming in next update")
    
    else:
        st.info("🤖 **No ML Model Available**")
        st.markdown("""
        To see ML model metrics here:
        
        1. **Train a model** using the training pipeline:
           ```python
           from src.models.training import NHLModelTrainer
           trainer = NHLModelTrainer()
           trainer.train_game_outcome_model()
           ```
        
        2. **Or use the ML predictor** to train programmatically:
           ```python
           from src.models.ml_predictor import NHLPredictor
           predictor = NHLPredictor()
           predictor.train_new_model()
           ```
        
        3. **Refresh this page** to see the metrics appear
        """)

with tab4:
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
