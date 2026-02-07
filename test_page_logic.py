"""Simulate the Model Performance page loading logic."""
from src.models.ml_predictor import NHLPredictor

print("Simulating Model Performance page loading...")
print()

# Step 1: Load predictor (like @st.cache_resource)
print("1. get_ml_predictor() function simulation:")
predictor = NHLPredictor()
if predictor.load():
    ml_predictor = predictor
    print(f"   ✓ Predictor loaded: {ml_predictor is not None}")
else:
    ml_predictor = None
    print(f"   ✗ Predictor not loaded")

# Step 2: Get model info
print()
print("2. Getting model info:")
ml_model_info = ml_predictor.get_model_info() if ml_predictor else None
print(f"   ml_model_info is None: {ml_model_info is None}")
if ml_model_info:
    print(f"   - Model type: {ml_model_info.get('model_type')}")
    print(f"   - N features: {ml_model_info.get('n_features')}")

# Step 3: Calculate ml_metrics
print()
print("3. Calculate ml_metrics:")
ml_metrics = {}
if ml_model_info and ml_predictor:
    ml_metrics = {
        "model_type": ml_model_info.get("model_type", "Unknown"),
        "training_date": ml_model_info.get("training_date", "Unknown"),
        "feature_count": ml_model_info.get("n_features", 0),
        "has_validation": False,
        "model_available": True
    }
    print(f"   ✓ ml_metrics created with {len(ml_metrics)} keys")
else:
    ml_metrics = {"model_available": False}
    print(f"   ✗ ml_metrics shows model not available")

# Step 4: Check tab3 conditional
print()
print("4. Check tab3 display logic:")
print(f"   ml_model_info is not None: {ml_model_info is not None}")
print(f"   Would show ML model content: {ml_model_info is not None}")

# Step 5: Check ML Model Status conditional
print()
print("5. Check ML Model Status display:")
check1 = ml_model_info is not None
check2 = ml_metrics.get("model_available", True)
print(f"   ml_model_info exists: {check1}")
print(f"   ml_metrics.get('model_available', True): {check2}")
print(f"   Would show status: {check1 and check2}")

print()
if ml_model_info:
    print("✅ SUCCESS: Page should display ML model information")
else:
    print("❌ FAILURE: Page will show 'No ML Model Available'")
