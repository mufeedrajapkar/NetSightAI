"""
evaluate.py
-----------
CN_AI Project — Network Session Classification
-----------------------------------------------
This script loads the saved final model and evaluates it on the held-out
test set, producing:

  - Classification report (per-class precision / recall / F1)
  - Confusion matrix (Human | Bot | Suspicious)
  - Model comparison summary table (loaded from model_metadata.json)

Run AFTER train_models.py has been executed and final_model.joblib exists.

NOTE: The dataset is a SYNTHETIC PROTOTYPE.
      Metrics are prototype/baseline only.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)
import joblib

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "sentinelnet_sample_500.csv")
MODELS_DIR = os.path.join(BASE_DIR, "ai", "models")
FINAL_MODEL_PATH = os.path.join(MODELS_DIR, "final_model.joblib")
METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")

RANDOM_STATE = 42
TEST_SIZE = 0.20
CLASS_ORDER = ["Human", "Bot", "Suspicious"]


# ─────────────────────────────────────────────────────────────────────────────
# LOAD MODEL + METADATA
# ─────────────────────────────────────────────────────────────────────────────

def load_model_and_metadata():
    """Load the saved pipeline and its metadata JSON."""
    print(f"\n{'='*60}")
    print("LOAD FINAL MODEL")
    print(f"{'='*60}")

    if not os.path.exists(FINAL_MODEL_PATH):
        raise FileNotFoundError(
            f"Model not found at {FINAL_MODEL_PATH}.\n"
            "Run ai/train_models.py first."
        )

    pipeline = joblib.load(FINAL_MODEL_PATH)
    print(f"  Model loaded from : {FINAL_MODEL_PATH}")

    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    print(f"  Model name        : {metadata['model_name']}")
    print(f"  Features used     : {metadata['feature_names']}")
    print(f"  Target classes    : {metadata['target_classes']}")

    return pipeline, metadata


# ─────────────────────────────────────────────────────────────────────────────
# RECREATE TEST SET
# ─────────────────────────────────────────────────────────────────────────────

def recreate_test_set(metadata: dict):
    """
    Recreate the exact held-out test set using the same random_state and
    test_size as in train_models.py.

    Because the split used a fixed random_state=42, this is fully reproducible.
    """
    from sklearn.model_selection import train_test_split

    df = pd.read_csv(DATA_PATH)
    feature_cols = metadata["feature_names"]
    target = "label"

    X = df[feature_cols]
    y = df[target]

    _, X_test, _, y_test = train_test_split(
        X, y,
        test_size=metadata["training_config"]["test_size"],
        random_state=metadata["training_config"]["random_state"],
        stratify=y,
    )

    print(f"\n  Test set recreated: {X_test.shape[0]} samples")
    print(f"  Test class distribution:")
    print(y_test.value_counts().to_string(header=False))

    return X_test, y_test


# ─────────────────────────────────────────────────────────────────────────────
# DETAILED EVALUATION
# ─────────────────────────────────────────────────────────────────────────────

def evaluate(pipeline, X_test: pd.DataFrame, y_test: pd.Series, model_name: str):
    """
    Run predictions and compute all evaluation metrics.
    Prints the full classification report.
    """
    print(f"\n{'='*60}")
    print(f"EVALUATION: {model_name}")
    print(f"{'='*60}")

    y_pred = pipeline.predict(X_test)

    acc      = accuracy_score(y_test, y_pred)
    prec_mac = precision_score(y_test, y_pred, average="macro",    zero_division=0)
    rec_mac  = recall_score(y_test,   y_pred, average="macro",    zero_division=0)
    f1_mac   = f1_score(y_test,       y_pred, average="macro",    zero_division=0)
    prec_w   = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    rec_w    = recall_score(y_test,   y_pred, average="weighted", zero_division=0)
    f1_w     = f1_score(y_test,       y_pred, average="weighted", zero_division=0)

    print(f"\n  Accuracy              : {acc:.4f}")
    print(f"  Precision (macro avg) : {prec_mac:.4f}")
    print(f"  Recall    (macro avg) : {rec_mac:.4f}")
    print(f"  F1-score  (macro avg) : {f1_mac:.4f}")
    print(f"  Precision (weighted)  : {prec_w:.4f}")
    print(f"  Recall    (weighted)  : {rec_w:.4f}")
    print(f"  F1-score  (weighted)  : {f1_w:.4f}")

    print(f"\n  Full Classification Report:")
    print(f"  {'-'*50}")
    report = classification_report(
        y_test, y_pred,
        target_names=CLASS_ORDER,
        zero_division=0,
    )
    # indent report lines
    for line in report.split("\n"):
        print(f"  {line}")

    return y_pred


# ─────────────────────────────────────────────────────────────────────────────
# CONFUSION MATRIX
# ─────────────────────────────────────────────────────────────────────────────

def plot_confusion_matrix(y_test: pd.Series, y_pred: np.ndarray, model_name: str):
    """Plot and save a confusion matrix for the final model."""
    cm = confusion_matrix(y_test, y_pred, labels=CLASS_ORDER)

    fig, ax = plt.subplots(figsize=(6, 5))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=CLASS_ORDER)
    disp.plot(ax=ax, colorbar=True, cmap="Blues")

    ax.set_title(
        f"Confusion Matrix — {model_name}\n"
        f"(Synthetic Prototype Dataset, n=100 test samples)",
        fontsize=11,
    )
    plt.tight_layout()

    save_path = os.path.join(MODELS_DIR, "final_confusion_matrix.png")
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Saved confusion matrix -> {save_path}")


# ─────────────────────────────────────────────────────────────────────────────
# METADATA COMPARISON SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

def print_metadata_summary(metadata: dict):
    """Print a summary of the saved model metadata and training configuration."""
    print(f"\n{'='*60}")
    print("MODEL METADATA SUMMARY")
    print(f"{'='*60}")

    cfg = metadata["training_config"]
    metrics = metadata["evaluation_metrics"]

    print(f"\n  Model             : {metadata['model_name']}")
    print(f"  Best params       : {metadata['best_hyperparameters']}")
    print(f"\n  Training config:")
    print(f"    Random state    : {cfg['random_state']}")
    print(f"    Test size       : {cfg['test_size']}")
    print(f"    CV folds        : {cfg['cv_folds']}")
    print(f"    Scoring metric  : {cfg['scoring_metric']}")
    print(f"    Class weight    : {cfg['class_weight']}")
    print(f"\n  Evaluation metrics (test set):")
    print(f"    Accuracy        : {metrics['accuracy']}")
    print(f"    Precision macro : {metrics['precision_macro']}")
    print(f"    Recall macro    : {metrics['recall_macro']}")
    print(f"    F1 macro        : {metrics['f1_macro']}")
    print(f"    CV F1 macro     : {metrics['cv_f1_macro']}")
    print(f"\n  Dataset note: {metadata['dataset_note']}")


# ─────────────────────────────────────────────────────────────────────────────
# DEMO PREDICTION (single session)
# ─────────────────────────────────────────────────────────────────────────────

def demo_single_prediction(pipeline, feature_names: list):
    """
    Demonstrate how the saved pipeline will eventually be used in FastAPI.
    Simulates receiving a single network session dict and predicting its class.

    This is not real traffic — it uses a synthetic example.
    """
    print(f"\n{'='*60}")
    print("DEMO: SINGLE SESSION PREDICTION")
    print(f"      (Synthetic example — not real traffic)")
    print(f"{'='*60}")

    # Example session that should look like a Bot (high requests_per_sec, low interval var)
    example_session = {
        "requests_per_sec": 12.5,
        "session_duration": 30.0,
        "packet_size_mean": 480.0,
        "packet_size_var": 50.0,
        "request_interval_mean": 0.08,
        "request_interval_var": 0.002,
        "bytes_transferred": 350000,
        "num_connections": 18,
        "protocol": "TCP",
    }

    # Build input DataFrame in the correct column order
    input_df = pd.DataFrame([example_session])[feature_names]

    prediction = pipeline.predict(input_df)[0]
    probabilities = pipeline.predict_proba(input_df)[0]
    classes = pipeline.classes_

    print(f"\n  Input session features:")
    for k, v in example_session.items():
        print(f"    {k:<30}: {v}")

    print(f"\n  Prediction : {prediction}")
    print(f"  Confidence breakdown:")
    for cls, prob in sorted(zip(classes, probabilities), key=lambda x: -x[1]):
        bar = "#" * int(prob * 30)
        print(f"    {cls:<12}: {prob:.4f}  |{bar}")

    print(f"\n  (Future FastAPI response would return: prediction='{prediction}', "
          f"confidence={max(probabilities):.4f})")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("\nCN_AI -- evaluate.py")
    print("Evaluating saved final model on held-out test set.")
    print("Dataset: SYNTHETIC PROTOTYPE (500 sessions)\n")

    # Load model and metadata
    pipeline, metadata = load_model_and_metadata()

    # Recreate identical test set (same split params as training)
    X_test, y_test = recreate_test_set(metadata)

    # Full evaluation
    y_pred = evaluate(pipeline, X_test, y_test, metadata["model_name"])

    # Confusion matrix
    plot_confusion_matrix(y_test, y_pred, metadata["model_name"])

    # Metadata summary
    print_metadata_summary(metadata)

    # Demo single prediction (future FastAPI workflow)
    demo_single_prediction(pipeline, metadata["feature_names"])

    print(f"\n{'='*60}")
    print("EVALUATION COMPLETE")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
