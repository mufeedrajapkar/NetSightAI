"""
anomaly_detection.py
--------------------
CN_AI Project — Unsupervised Anomaly Detection Pipeline

Trains an IsolationForest model solely on genuine HUMAN-labeled sessions.
Because it only observes normal user activity during training, it detects
unseen attack patterns, novel bot evasions, and protocol deviations.

Outputs:
  - ai/models/isolation_forest.joblib: trained preprocessing + IsolationForest pipeline
  - ai/models/isolation_forest_metadata.json: model hyperparameters and training parameters
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import IsolationForest
import joblib

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "ai", "models")
SYNTHETIC_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "sentinelnet_sample_500.csv")
REAL_DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "sentinelnet_real_dataset.csv")
IF_MODEL_PATH = os.path.join(MODELS_DIR, "isolation_forest.joblib")
IF_METADATA_PATH = os.path.join(MODELS_DIR, "isolation_forest_metadata.json")

NUMERICAL_FEATURES = [
    "requests_per_sec",
    "session_duration",
    "packet_size_mean",
    "packet_size_var",
    "request_interval_mean",
    "request_interval_var",
    "bytes_transferred",
    "num_connections",
]
CATEGORICAL_FEATURES = ["protocol"]
ALL_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES


def train_isolation_forest(
    data_path: str = None,
    contamination: float = 0.05,
    random_state: int = 42,
) -> Tuple[Pipeline, Dict[str, Any]]:
    """
    Train Isolation Forest pipeline on HUMAN sessions only.
    """
    print("\n" + "=" * 65)
    print("TRAINING ISOLATION FOREST ANOMALY DETECTOR")
    print("=" * 65)

    # 1. Resolve dataset
    chosen_path = data_path
    if not chosen_path or not os.path.exists(chosen_path):
        if os.path.exists(REAL_DATA_PATH):
            chosen_path = REAL_DATA_PATH
        else:
            chosen_path = SYNTHETIC_DATA_PATH
            print(f"[!] Real data not found. Falling back to synthetic prototype: {SYNTHETIC_DATA_PATH}")

    df = pd.read_csv(chosen_path)
    is_real = "real" in chosen_path.lower()
    print(f"  Dataset path   : {chosen_path}")
    print(f"  Dataset origin : {'Real' if is_real else 'Synthetic Prototype'}")
    print(f"  Total sessions : {len(df)}")

    # 2. Filter to HUMAN only
    human_df = df[df["label"].astype(str).str.lower() == "human"].copy()
    if human_df.empty:
        raise ValueError("Dataset does not contain any 'Human' labeled sessions for training!")

    print(f"  Human sessions : {len(human_df)} (used for training normal boundary)")

    X_train = human_df[ALL_FEATURES]

    # 3. Build preprocessing + model pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERICAL_FEATURES),
            ("cat", OneHotEncoder(categories=[["TCP", "UDP"]], handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )

    iso_forest = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=150,
        max_samples="auto",
        n_jobs=-1,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("isolation_forest", iso_forest),
        ]
    )

    # Train
    pipeline.fit(X_train)
    print("  Model training complete.")

    # 4. Save model artifact
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(pipeline, IF_MODEL_PATH)
    print(f"  Saved model -> {IF_MODEL_PATH}")

    # 5. Metadata
    metadata = {
        "model_name": "IsolationForest",
        "contamination": contamination,
        "n_estimators": 150,
        "random_state": random_state,
        "features": ALL_FEATURES,
        "numerical_features": NUMERICAL_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "training_row_count": len(human_df),
        "dataset_path": os.path.relpath(chosen_path, BASE_DIR) if os.path.isabs(chosen_path) else chosen_path,
        "dataset_type": "real" if is_real else "synthetic prototype",
        "anomaly_decision_boundary": "decision_function < 0 or anomaly_score > 0",
    }

    with open(IF_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    print(f"  Saved metadata -> {IF_METADATA_PATH}")

    # 6. Evaluate anomaly flag distribution across all classes
    eval_results = evaluate_anomaly_detector(pipeline, df)
    metadata["evaluation_on_full_dataset"] = eval_results

    # Update metadata with evaluation
    with open(IF_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)

    return pipeline, metadata


def evaluate_anomaly_detector(pipeline: Pipeline, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Report anomaly flag rate across Human, Tier1, Tier2, Tier3 sessions.
    """
    print("\n" + "-" * 65)
    print("ISOLATION FOREST ANOMALY EVALUATION")
    print("-" * 65)
    print(f"{'Class / Group':<24} | {'Total':<6} | {'Anomalies':<10} | {'Anomaly Rate':<12}")
    print("-" * 65)

    results = {}

    # Check overall classes
    classes = ["Human", "Bot", "Suspicious"]
    for cls in classes:
        sub_df = df[df["label"].astype(str).str.lower() == cls.lower()]
        if sub_df.empty:
            continue
        X = sub_df[ALL_FEATURES]
        preds = pipeline.predict(X)  # +1 inlier, -1 outlier
        anomalies_count = int(np.sum(preds == -1))
        total_count = len(sub_df)
        rate = float(anomalies_count / total_count) if total_count > 0 else 0.0

        results[cls] = {
            "total": total_count,
            "anomalies": anomalies_count,
            "anomaly_rate": round(rate, 4),
        }
        print(f"{cls:<24} | {total_count:<6} | {anomalies_count:<10} | {rate*100:>10.2f}%")

    # Check Bot Tiers specifically
    if "bot_tier" in df.columns:
        print("-" * 65)
        for tier in ["Tier1", "Tier2", "Tier3"]:
            sub_df = df[df["bot_tier"].astype(str).str.lower() == tier.lower()]
            if sub_df.empty:
                continue
            X = sub_df[ALL_FEATURES]
            preds = pipeline.predict(X)
            anomalies_count = int(np.sum(preds == -1))
            total_count = len(sub_df)
            rate = float(anomalies_count / total_count) if total_count > 0 else 0.0

            results[f"Bot_{tier}"] = {
                "total": total_count,
                "anomalies": anomalies_count,
                "anomaly_rate": round(rate, 4),
            }
            print(f"Bot ({tier}){'':<14} | {total_count:<6} | {anomalies_count:<10} | {rate*100:>10.2f}%")

    print("-" * 65 + "\n")
    return results


def main():
    parser = argparse.ArgumentParser(description="SentinelNet Isolation Forest Anomaly Detection Trainer")
    parser.add_argument("--data", default=None, help="Dataset CSV path")
    parser.add_argument("--contamination", type=float, default=0.05, help="Expected normal outlier rate (default: 0.05)")
    args = parser.parse_args()

    try:
        train_isolation_forest(data_path=args.data, contamination=args.contamination)
    except Exception as exc:
        print(f"[ERROR] Failed to train Isolation Forest: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
