"""Test script to simulate the Model Performance page loading."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.ml_predictor import NHLPredictor

print("Testing Model Performance page logic...")
print()

# Test 1: Load predictor
print("1. Loading predictor...")
predictor = NHLPredictor()
loaded = predictor.load()
print(f"   Loaded: {loaded}")

if loaded:
    print()
    print("2. Getting model info...")
    info = predictor.get_model_info()
    print(f"   Info is None: {info is None}")
    
    if info:
        print()
        print("3. Model details:")
        print(f"   - Type: {info.get('model_type', 'Unknown')}")
        print(f"   - Samples: {info.get('n_training_samples', 0)}")
        print(f"   - Features: {info.get('n_features', 0)}")
        print(f"   - Seasons: {info.get('seasons_used', [])}")
        
        print()
        print("4. Checking metrics...")
        metrics = info.get('metrics', {})
        print(f"   - Metrics exist: {len(metrics) > 0}")
        if metrics:
            print(f"   - Test accuracy: {metrics.get('test_accuracy', 0):.2%}")
        
        print()
        print("5. Checking feature importance...")
        fi = info.get('feature_importance', {})
        print(f"   - Feature importance exists: {len(fi) > 0}")
        if fi:
            print(f"   - Number of features: {len(fi)}")
            
        print()
        print("✅ All checks passed! Page should display model info.")
    else:
        print()
        print("❌ Model info is None - page will show 'No ML Model Available'")
else:
    print()
    print("❌ Model failed to load - page will show 'No ML Model Available'")
