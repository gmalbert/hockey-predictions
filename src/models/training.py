"""Model training and evaluation pipeline."""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pickle
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, log_loss, classification_report, confusion_matrix
from sklearn.calibration import CalibratedClassifierCV
import matplotlib.pyplot as plt
import seaborn as sns

from .features import NHLFeatureEngineer

class NHLModelTrainer:
    """Training pipeline for NHL prediction models."""

    def __init__(self, model_dir: str = "data_files/models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.feature_engineer = NHLFeatureEngineer()
        self.scaler = StandardScaler()

    def train_game_outcome_model(
        self,
        seasons: List[str] = None,
        test_size: float = 0.2,
        model_type: str = "gradient_boosting",
        hyperparameter_tune: bool = False
    ) -> Dict[str, Any]:
        """
        Train a model to predict game outcomes.

        Args:
            seasons: List of seasons to train on
            test_size: Fraction of data for testing
            model_type: Type of model ('gradient_boosting', 'random_forest', 'logistic')
            hyperparameter_tune: Whether to perform hyperparameter tuning

        Returns:
            Dictionary with model, metrics, and metadata
        """
        print("Loading training data...")
        X, y = self.feature_engineer.prepare_training_data(seasons)

        if X.empty or len(y) == 0:
            raise ValueError("No training data available")

        print(f"Training on {len(X)} games with {len(X.columns)} features")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Initialize model
        if model_type == "gradient_boosting":
            if hyperparameter_tune:
                param_grid = {
                    'n_estimators': [100, 200, 300],
                    'max_depth': [3, 4, 5],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'subsample': [0.8, 0.9, 1.0]
                }
                base_model = GradientBoostingClassifier(random_state=42)
                model = GridSearchCV(base_model, param_grid, cv=5, scoring='neg_log_loss', n_jobs=-1)
            else:
                model = GradientBoostingClassifier(
                    n_estimators=200,
                    max_depth=4,
                    learning_rate=0.1,
                    subsample=0.9,
                    random_state=42
                )
        elif model_type == "random_forest":
            if hyperparameter_tune:
                param_grid = {
                    'n_estimators': [100, 200, 300],
                    'max_depth': [10, 20, None],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4]
                }
                base_model = RandomForestClassifier(random_state=42)
                model = GridSearchCV(base_model, param_grid, cv=5, scoring='neg_log_loss', n_jobs=-1)
            else:
                model = RandomForestClassifier(
                    n_estimators=200,
                    max_depth=10,
                    min_samples_split=5,
                    random_state=42
                )
        elif model_type == "logistic":
            model = LogisticRegression(random_state=42, max_iter=1000)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        # Train model
        print("Training model...")
        if hyperparameter_tune and hasattr(model, 'fit'):
            model.fit(X_train_scaled, y_train)
            best_model = model.best_estimator_
            print(f"Best parameters: {model.best_params_}")
        else:
            model.fit(X_train_scaled, y_train)
            best_model = model

        # Calibrate probabilities for better probability estimates
        calibrated_model = CalibratedClassifierCV(best_model, method='isotonic', cv=5)
        calibrated_model.fit(X_train_scaled, y_train)

        # Evaluate model
        print("Evaluating model...")
        metrics = self._evaluate_model(calibrated_model, X_train_scaled, X_test_scaled, y_train, y_test)

        # Feature importance (for tree-based models)
        feature_importance = None
        if hasattr(best_model, 'feature_importances_'):
            feature_importance = dict(zip(X.columns, best_model.feature_importances_))
            feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))

        # Save model
        model_path = self.model_dir / f"game_outcome_{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        
        training_info = {
            "seasons": seasons,
            "n_games": len(X),
            "n_features": len(X.columns),
            "model_type": model_type,
            "hyperparameter_tuned": hyperparameter_tune,
            "trained_at": datetime.now().isoformat()
        }
        
        self._save_model(calibrated_model, X.columns.tolist(), metrics, model_path, 
                        training_info=training_info, feature_importance=feature_importance)

        result = {
            "model": calibrated_model,
            "feature_columns": X.columns.tolist(),
            "scaler": self.scaler,
            "metrics": metrics,
            "feature_importance": feature_importance,
            "model_path": str(model_path),
            "training_info": {
                "seasons": seasons,
                "n_games": len(X),
                "n_features": len(X.columns),
                "model_type": model_type,
                "hyperparameter_tuned": hyperparameter_tune,
                "trained_at": datetime.now().isoformat()
            }
        }

        print(f"Model trained and saved to {model_path}")

        return result

    def _evaluate_model(self, model, X_train, X_test, y_train, y_test) -> Dict[str, float]:
        """Evaluate model performance."""
        # Training predictions
        train_pred = model.predict(X_train)
        train_proba = model.predict_proba(X_train)

        # Test predictions
        test_pred = model.predict(X_test)
        test_proba = model.predict_proba(X_test)

        # Calculate metrics
        metrics = {
            "train_accuracy": accuracy_score(y_train, train_pred),
            "test_accuracy": accuracy_score(y_test, test_pred),
            "train_log_loss": log_loss(y_train, train_proba),
            "test_log_loss": log_loss(y_test, test_proba),
        }

        # Cross-validation scores
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
        metrics["cv_accuracy_mean"] = cv_scores.mean()
        metrics["cv_accuracy_std"] = cv_scores.std()

        # Additional metrics
        tn, fp, fn, tp = confusion_matrix(y_test, test_pred).ravel()
        metrics["precision"] = tp / (tp + fp) if (tp + fp) > 0 else 0
        metrics["recall"] = tp / (tp + fn) if (tp + fn) > 0 else 0
        metrics["f1_score"] = 2 * metrics["precision"] * metrics["recall"] / (metrics["precision"] + metrics["recall"]) if (metrics["precision"] + metrics["recall"]) > 0 else 0

        return metrics

    def _save_model(self, model, feature_columns: List[str], metrics: Dict, filepath: Path,
                   training_info: Dict = None, feature_importance: Dict = None):
        """Save trained model to disk."""
        model_data = {
            "model": model,
            "feature_columns": feature_columns,
            "scaler": self.scaler,
            "metrics": metrics,
            "saved_at": datetime.now().isoformat()
        }
        
        if training_info:
            model_data["training_info"] = training_info
        if feature_importance:
            model_data["feature_importance"] = feature_importance

        with open(filepath, "wb") as f:
            pickle.dump(model_data, f)

    def load_model(self, model_path: str) -> Optional[Dict]:
        """Load trained model from disk."""
        filepath = Path(model_path)
        if not filepath.exists():
            print(f"Model file not found: {filepath}")
            return None

        with open(filepath, "rb") as f:
            model_data = pickle.load(f)

        # Restore scaler
        self.scaler = model_data.get("scaler", StandardScaler())

        return model_data

    def predict_game(self, model_data: Dict, game_features: Dict) -> Dict[str, float]:
        """
        Make prediction for a single game.

        Args:
            model_data: Loaded model data
            game_features: Feature dictionary for the game

        Returns:
            Dictionary with prediction results
        """
        model = model_data["model"]
        feature_columns = model_data["feature_columns"]

        # Create feature vector
        features = []
        for col in feature_columns:
            features.append(game_features.get(col, 0.0))

        # Scale features
        features_scaled = self.scaler.transform([features])

        # Make prediction
        proba = model.predict_proba(features_scaled)[0]
        prediction = model.predict(features_scaled)[0]

        return {
            "home_win_probability": proba[1],
            "away_win_probability": proba[0],
            "predicted_winner": "home" if prediction == 1 else "away",
            "confidence": max(proba)
        }

    def create_model_comparison_report(self, models: List[Dict], output_path: str = None) -> pd.DataFrame:
        """
        Create a comparison report for multiple trained models.

        Args:
            models: List of trained model results
            output_path: Path to save the report (optional)

        Returns:
            DataFrame with model comparison
        """
        comparison_data = []

        for i, model_result in enumerate(models):
            metrics = model_result["metrics"]
            training_info = model_result["training_info"]

            row = {
                "model_id": i + 1,
                "model_type": training_info["model_type"],
                "seasons": ", ".join(training_info.get("seasons", [])),
                "n_games": training_info["n_games"],
                "n_features": training_info["n_features"],
                "train_accuracy": metrics["train_accuracy"],
                "test_accuracy": metrics["test_accuracy"],
                "train_log_loss": metrics["train_log_loss"],
                "test_log_loss": metrics["test_log_loss"],
                "cv_accuracy_mean": metrics["cv_accuracy_mean"],
                "cv_accuracy_std": metrics["cv_accuracy_std"],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1_score": metrics["f1_score"],
                "hyperparameter_tuned": training_info["hyperparameter_tuned"]
            }
            comparison_data.append(row)

        df = pd.DataFrame(comparison_data)

        if output_path:
            df.to_csv(output_path, index=False)
            print(f"Model comparison report saved to {output_path}")

        return df

    def plot_feature_importance(self, model_result: Dict, top_n: int = 20, save_path: str = None):
        """
        Plot feature importance for tree-based models.

        Args:
            model_result: Result from train_game_outcome_model
            top_n: Number of top features to show
            save_path: Path to save the plot (optional)
        """
        if "feature_importance" not in model_result or not model_result["feature_importance"]:
            print("Feature importance not available for this model type")
            return

        feature_importance = model_result["feature_importance"]

        # Get top N features
        top_features = dict(list(feature_importance.items())[:top_n])

        plt.figure(figsize=(12, 8))
        sns.barplot(x=list(top_features.values()), y=list(top_features.keys()))
        plt.title(f"Top {top_n} Feature Importance")
        plt.xlabel("Importance")
        plt.ylabel("Feature")
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Feature importance plot saved to {save_path}")
        else:
            plt.show()

    def validate_model_calibration(self, model_data: Dict, validation_games: pd.DataFrame) -> Dict[str, float]:
        """
        Validate model calibration using validation games.

        Args:
            model_data: Loaded model data
            validation_games: DataFrame with validation games

        Returns:
            Dictionary with calibration metrics
        """
        actual_outcomes = []
        predicted_probabilities = []

        for _, game in validation_games.iterrows():
            try:
                features = self.feature_engineer.create_game_features(
                    game.to_dict(),
                    validation_games,
                    self.feature_engineer.load_team_stats()
                )

                prediction = self.predict_game(model_data, features)
                actual_outcomes.append(int(game['home_won']))
                predicted_probabilities.append(prediction['home_win_probability'])

            except Exception as e:
                print(f"Error predicting game {game.get('game_id', 'unknown')}: {e}")
                continue

        if not actual_outcomes:
            return {"error": "No valid predictions generated"}

        # Calculate calibration metrics
        actual_outcomes = np.array(actual_outcomes)
        predicted_probabilities = np.array(predicted_probabilities)

        # Brier score (lower is better)
        brier_score = np.mean((predicted_probabilities - actual_outcomes) ** 2)

        # Calibration by bins
        bins = np.linspace(0, 1, 11)
        bin_centers = (bins[:-1] + bins[1:]) / 2

        calibration_data = []
        for i in range(len(bins) - 1):
            mask = (predicted_probabilities >= bins[i]) & (predicted_probabilities < bins[i + 1])
            if np.sum(mask) > 0:
                actual_rate = np.mean(actual_outcomes[mask])
                predicted_rate = bin_centers[i]
                calibration_data.append({
                    "bin_center": bin_centers[i],
                    "actual_rate": actual_rate,
                    "predicted_rate": predicted_rate,
                    "n_games": np.sum(mask)
                })

        return {
            "brier_score": brier_score,
            "calibration_data": calibration_data,
            "n_games_validated": len(actual_outcomes)
        }