"""Machine learning model for game predictions."""
from pathlib import Path
from typing import Optional, Dict, Any
import pickle
import pandas as pd
from datetime import datetime

from .features import NHLFeatureEngineer
from .training import NHLModelTrainer

class NHLPredictor:
    """ML-based game outcome predictor using trained models."""

    def __init__(self, model_path: str = None):
        self.model_path = Path(model_path) if model_path else self._find_latest_model()
        self.model_data = None
        self.feature_engineer = NHLFeatureEngineer()
        self.trainer = NHLModelTrainer()

    def _find_latest_model(self) -> Path:
        """Find the most recently trained model."""
        model_dir = Path("data_files/models")
        if not model_dir.exists():
            return Path("data_files/models/game_outcome_gradient_boosting_latest.pkl")

        # Look for model files
        model_files = list(model_dir.glob("game_outcome_*.pkl"))
        if not model_files:
            return Path("data_files/models/game_outcome_gradient_boosting_latest.pkl")

        # Return the most recent one
        return max(model_files, key=lambda x: x.stat().st_mtime)

    def load(self) -> bool:
        """Load trained model from disk."""
        if not self.model_path.exists():
            print(f"Model file not found: {self.model_path}")
            return False

        try:
            with open(self.model_path, "rb") as f:
                self.model_data = pickle.load(f)
            print(f"Loaded model from {self.model_path}")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

    def save(self, model_data: Dict, filename: str = None) -> Path:
        """Save model data to disk."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"game_outcome_{timestamp}.pkl"

        save_path = Path("data_files/models") / filename
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "wb") as f:
            pickle.dump(model_data, f)

        print(f"Model saved to {save_path}")
        return save_path

    def predict_game(self, home_team: str, away_team: str, game_date: str = None) -> Optional[Dict[str, Any]]:
        """
        Predict the outcome of a game.

        Args:
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            game_date: Game date (YYYY-MM-DD), defaults to today

        Returns:
            Dictionary with prediction results or None if prediction fails
        """
        if not self.model_data:
            if not self.load():
                return None

        try:
            # Create game dict for feature engineering
            game = {
                'home_team': home_team,
                'away_team': away_team,
                'date': game_date or datetime.now().strftime("%Y-%m-%d")
            }

            # Load historical data and team stats
            games_df = self.feature_engineer.load_historical_games(['2023-24', '2024-25'])
            team_stats = self.feature_engineer.load_team_stats()

            # Create features
            features = self.feature_engineer.create_game_features(game, games_df, team_stats)

            # Make prediction
            prediction = self.trainer.predict_game(self.model_data, features)

            # Add additional context
            result = {
                **prediction,
                'home_team': home_team,
                'away_team': away_team,
                'game_date': game['date'],
                'model_version': self.model_data.get('saved_at', 'unknown'),
                'features_used': len(self.model_data.get('feature_columns', []))
            }

            return result

        except Exception as e:
            print(f"Error predicting game {away_team} @ {home_team}: {e}")
            return None

    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the loaded model."""
        if not self.model_data:
            return None

        training_info = self.model_data.get('training_info', {})
        return {
            'model_path': str(self.model_path),
            'saved_at': self.model_data.get('saved_at'),
            'training_date': self.model_data.get('saved_at'),  # Alias for compatibility
            'metrics': self.model_data.get('metrics', {}),
            'n_features': len(self.model_data.get('feature_columns', [])),
            'feature_columns': self.model_data.get('feature_columns', [])[:10],  # First 10
            'model_type': training_info.get('model_type', 'gradient_boosting'),
            'n_training_samples': training_info.get('n_games', 0),
            'seasons_used': training_info.get('seasons', []),
            'feature_importance': self.model_data.get('feature_importance', {}),
        }

    def train_new_model(self, seasons: list = None, model_type: str = "gradient_boosting",
                       hyperparameter_tune: bool = False) -> bool:
        """
        Train a new model and update the predictor to use it.

        Args:
            seasons: List of seasons to train on
            model_type: Type of model to train
            hyperparameter_tune: Whether to tune hyperparameters

        Returns:
            True if training successful
        """
        try:
            print("Training new model...")
            result = self.trainer.train_game_outcome_model(
                seasons=seasons,
                model_type=model_type,
                hyperparameter_tune=hyperparameter_tune
            )

            # Save the model
            model_path = self.save(result, f"game_outcome_{model_type}_latest.pkl")
            self.model_path = model_path
            self.model_data = result

            print("New model trained and loaded successfully")
            return True

        except Exception as e:
            print(f"Error training new model: {e}")
            return False

    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the loaded model.

        Returns:
            Dictionary with model metadata, or None if no model loaded
        """
        if not self.model_data:
            return None

        training_info = self.model_data.get('training_info', {})
        metrics = self.model_data.get('metrics', {})

        return {
            'model_type': training_info.get('model_type', 'unknown'),
            'training_samples': training_info.get('n_games', 0),
            'n_features': training_info.get('n_features', 0),
            'test_accuracy': metrics.get('test_accuracy', 0),
            'cross_val_accuracy': metrics.get('cv_accuracy_mean', 0),
            'feature_importance': self.model_data.get('feature_importance', {}),
            'training_date': training_info.get('trained_at', 'unknown'),
            'seasons': training_info.get('seasons', [])
        }

    def validate_predictions(self, test_games: list = None) -> Optional[Dict[str, Any]]:
        """
        Validate model predictions against actual outcomes.

        Args:
            test_games: List of game dicts to validate against (optional)

        Returns:
            Validation results
        """
        if not self.model_data:
            return None

        try:
            # Use recent games for validation if none provided
            if test_games is None:
                games_df = self.feature_engineer.load_historical_games(['2024-25'])
                # Get last 50 games for validation
                recent_games = games_df.tail(50)
                test_games = [game.to_dict() for _, game in recent_games.iterrows()]

            # Convert to DataFrame for validation
            validation_df = pd.DataFrame(test_games)

            return self.trainer.validate_model_calibration(self.model_data, validation_df)

        except Exception as e:
            print(f"Error validating predictions: {e}")
            return None
