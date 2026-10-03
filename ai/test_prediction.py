"""
test_prediction.py
------------------
CN_AI Project — Network Session Classification
-----------------------------------------------
Standalone script to validate single-session inference.
Loads the saved pipeline and simulates a single network session.
"""
import os
import pandas as pd
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "ai", "models")
FINAL_MODEL_PATH = os.path.join(MODELS_DIR, "final_model.joblib")

def main():
    print(f"\n{'='*60}")
    print("TEST PREDICTION: SINGLE SESSION INFERENCE")
    print(f"{'='*60}\n")

    if not os.path.exists(FINAL_MODEL_PATH):
        print(f"Error: Model not found at {FINAL_MODEL_PATH}")
        print("Please run train_models.py first.")
        return

    print(f"Loading model from: {FINAL_MODEL_PATH} ...")
    pipeline = joblib.load(FINAL_MODEL_PATH)
    print("Model loaded successfully.\n")

    # Single session matching the integration contract
    single_session = {
        "requests_per_sec": 4.2,
        "session_duration": 35.5,
        "packet_size_mean": 512,
        "packet_size_var": 120,
        "request_interval_mean": 0.24,
        "request_interval_var": 0.08,
        "bytes_transferred": 45000,
        "num_connections": 8,
        "protocol": "TCP",
    }
    
    # Feature names in the exact order the pipeline expects
    feature_names = [
        "requests_per_sec",
        "session_duration",
        "packet_size_mean",
        "packet_size_var",
        "request_interval_mean",
        "request_interval_var",
        "bytes_transferred",
        "num_connections",
        "protocol"
    ]

    input_df = pd.DataFrame([single_session])[feature_names]

    print("Input Session Data:")
    for k, v in single_session.items():
        print(f"  {k:<25}: {v}")
    
    print("\nRunning prediction...")
    prediction = pipeline.predict(input_df)[0]
    probabilities = pipeline.predict_proba(input_df)[0]
    classes = pipeline.classes_

    model_type = type(pipeline.named_steps["classifier"]).__name__

    print(f"\n{'='*60}")
    print("INFERENCE RESULTS")
    print(f"{'='*60}")
    print(f"  Prediction : {prediction}")
    print(f"  Model      : {model_type}")
    
    print("\n  Probabilities:")
    for cls, prob in sorted(zip(classes, probabilities), key=lambda x: -x[1]):
        print(f"    {cls:<12}: {prob:.4f}")
    
    print(f"\n{'='*60}")
    print("TEST COMPLETED SUCCESSFULLY")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
