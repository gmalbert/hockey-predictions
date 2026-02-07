#!/usr/bin/env python3
"""
Weekly model retraining script for GitHub Actions.
Trains the ML model with the latest available data.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.training import NHLModelTrainer

def main():
    """Retrain the ML model with latest data."""
    print("Starting weekly model retraining...")

    try:
        # Initialize trainer
        trainer = NHLModelTrainer()

        # Train model with all available seasons
        # This will automatically use the latest complete seasons
        print("Training model...")
        result = trainer.train_game_outcome_model()

        if result:
            print("✅ Model retraining completed successfully!")
            print(f"Model saved to: {result.get('model_path', 'Unknown')}")
            return True
        else:
            print("❌ Model training failed")
            return False

    except Exception as e:
        print(f"❌ Error during model retraining: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)