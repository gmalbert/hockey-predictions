"""Test script to verify ML model information."""
from src.models.ml_predictor import NHLPredictor

predictor = NHLPredictor()
loaded = predictor.load()
print(f'Model loaded: {loaded}')

if loaded:
    info = predictor.get_model_info()
    print(f'\nModel Info:')
    print(f'  Type: {info.get("model_type")}')
    print(f'  Samples: {info.get("n_training_samples"):,}')
    print(f'  Features: {info.get("n_features")}')
    print(f'  Seasons: {info.get("seasons_used")}')
    print(f'\nMetrics:')
    metrics = info.get('metrics', {})
    print(f'  Test Accuracy: {metrics.get("test_accuracy", 0):.2%}')
    print(f'  CV Accuracy: {metrics.get("cv_accuracy_mean", 0):.2%}')
    print(f'  Precision: {metrics.get("precision", 0):.3f}')
    print(f'  Recall: {metrics.get("recall", 0):.3f}')
    print(f'  F1 Score: {metrics.get("f1_score", 0):.3f}')
    print(f'\nFeature Importance (top 5):')
    fi = info.get('feature_importance', {})
    for i, (feature, importance) in enumerate(sorted(fi.items(), key=lambda x: x[1], reverse=True)[:5]):
        print(f'  {i+1}. {feature}: {importance:.4f}')
