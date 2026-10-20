"""
train_models.py
---------------
CN_AI Project — Network Session Classification
-----------------------------------------------
This script implements the full ML training pipeline:

  Dataset (synthetic prototype)
       ↓
  Feature selection + preprocessing
       ↓
  Stratified train/test split (80/20)
       ↓
  StratifiedKFold cross-validation
       ↓
  GridSearchCV hyperparameter tuning
       ↓
  Model training (LR, RF, SVM)
       ↓
  Model comparison (macro F1)
       ↓
  Final model selection + saving

Target: label (Human | Bot | Suspicious)

NOTE: The dataset is a SYNTHETIC PROTOTYPE.
      Performance metrics reflect prototype/baseline only.
      Do NOT interpret results as real-world network traffic performance.
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import argparse
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import (
    train_test_split,
    StratifiedKFold,
    GridSearchCV,
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    ConfusionMatrixDisplay,
    confusion_matrix,
)
import joblib

warnings.filterwarnings("ignore")

# ----------------------------------------------------------------------------─
# CONFIGURATION
# ----------------------------------------------------------------------------─

RANDOM_STATE = 42
TEST_SIZE = 0.20
CV_FOLDS = 5
SCORING_METRIC = "f1_macro"

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "sentinelnet_sample_500.csv")
MODELS_DIR = os.path.join(BASE_DIR, "ai", "models")
FINAL_MODEL_PATH = os.path.join(MODELS_DIR, "final_model.joblib")
METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")

# Class order for confusion matrix display
CLASS_ORDER = ["Human", "Bot", "Suspicious"]


# ----------------------------------------------------------------------------─
# LOAD DATA
# ----------------------------------------------------------------------------─

def load_data(path: str) -> pd.DataFrame:
    """Load the raw dataset from CSV."""
    print(f"\n{'='*60}")
    print("STEP 1: LOAD DATA")
    print(f"{'='*60}")
    df = pd.read_csv(path)
    print(f"  Loaded: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"  Columns: {df.columns.tolist()}")
    print(f"\n  Label distribution:")
    print(df["label"].value_counts().to_string(header=False))
    return df


# ----------------------------------------------------------------------------─
# DEFINE FEATURES
# ----------------------------------------------------------------------------─

def define_features():
    """
    Return the feature and target column names.

    EXCLUDED (data leakage / identifier rules):
      - session_id  : identifier only
      - device_id   : excluded to prevent device memorization
      - timestamp   : raw date string; no temporal features in this iteration
      - label       : this is the target — never a feature
      - bot_tier    : bot-generation metadata; unavailable to a live classifier
    """
    numerical_features = [
        "requests_per_sec",
        "session_duration",
        "packet_size_mean",
        "packet_size_var",
        "request_interval_mean",
        "request_interval_var",
        "bytes_transferred",
        "num_connections",
    ]
    categorical_features = ["protocol"]
    target = "label"
    return numerical_features, categorical_features, target


# ----------------------------------------------------------------------------─
# PREPROCESS DATA
# ----------------------------------------------------------------------------─

def build_preprocessor(numerical_features: list, categorical_features: list) -> ColumnTransformer:
    """
    Build a ColumnTransformer that:
      - Scales numerical features with StandardScaler
      - Encodes categorical features with OneHotEncoder (drop='first' to avoid multicollinearity)

    IMPORTANT: This preprocessor must be fit ONLY on training data.
               It is embedded inside each Pipeline to prevent leakage.
    """
    numerical_transformer = StandardScaler()

    categorical_transformer = OneHotEncoder(
        drop="first",          # avoid dummy variable trap; protocol has 2 values (TCP, UDP)
        handle_unknown="ignore",
        sparse_output=False,
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numerical_transformer, numerical_features),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop",      # drop any columns not explicitly listed
    )
    return preprocessor


# ----------------------------------------------------------------------------─
# TRAIN / TEST SPLIT
# ----------------------------------------------------------------------------─

def split_data(df: pd.DataFrame, numerical_features: list, categorical_features: list, target: str):
    """
    Stratified 80/20 train/test split.
    Stratification preserves class proportions in both sets.
    The test set is set aside and NOT used for any tuning or selection.
    """
    print(f"\n{'='*60}")
    print("STEP 2: TRAIN / TEST SPLIT")
    print(f"{'='*60}")

    feature_cols = numerical_features + categorical_features
    X = df[feature_cols]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    print(f"  Training set : {X_train.shape[0]} samples")
    print(f"  Test set     : {X_test.shape[0]} samples")
    print(f"\n  Training class distribution:")
    print(y_train.value_counts().to_string(header=False))
    print(f"\n  Test class distribution:")
    print(y_test.value_counts().to_string(header=False))

    return X_train, X_test, y_train, y_test


# ----------------------------------------------------------------------------─
# DEFINE MODELS + HYPERPARAMETER GRIDS
# ----------------------------------------------------------------------------─

def get_model_configs(preprocessor: ColumnTransformer) -> dict:
    """
    Return a dict of model configurations.
    Each entry contains:
      - pipeline : sklearn Pipeline (preprocessor + classifier)
      - param_grid : hyperparameter search space for GridSearchCV

    Three models are compared:
      1. Logistic Regression
      2. Random Forest Classifier
      3. Support Vector Machine (SVM)
    """
    configs = {
        "Logistic Regression": {
            "pipeline": Pipeline([
                ("preprocessor", preprocessor),
                ("classifier", LogisticRegression(
                    max_iter=1000,
                    random_state=RANDOM_STATE,
                    class_weight="balanced",   # handles class imbalance (100 Suspicious vs 200 each)
                )),
            ]),
            "param_grid": {
                "classifier__C": [0.01, 0.1, 1, 10, 100],
                "classifier__solver": ["lbfgs", "saga"],
            },
        },
        "Random Forest": {
            "pipeline": Pipeline([
                ("preprocessor", preprocessor),
                ("classifier", RandomForestClassifier(
                    random_state=RANDOM_STATE,
                    class_weight="balanced",
                )),
            ]),
            "param_grid": {
                "classifier__n_estimators": [100, 200],
                "classifier__max_depth": [None, 10, 20],
                "classifier__min_samples_split": [2, 5],
                "classifier__min_samples_leaf": [1, 2],
            },
        },
        "SVM": {
            "pipeline": Pipeline([
                ("preprocessor", preprocessor),
                ("classifier", SVC(
                    random_state=RANDOM_STATE,
                    class_weight="balanced",
                    probability=True,          # enables predict_proba for future FastAPI confidence output
                )),
            ]),
            "param_grid": {
                "classifier__C": [0.1, 1, 10],
                "classifier__kernel": ["rbf", "linear"],
                "classifier__gamma": ["scale", "auto"],
            },
        },
    }
    return configs


# ----------------------------------------------------------------------------─
# CROSS-VALIDATION + HYPERPARAMETER TUNING
# ----------------------------------------------------------------------------─

def tune_and_evaluate_models(configs: dict, X_train: pd.DataFrame, y_train: pd.Series) -> dict:
    """
    For each model:
      1. Run GridSearchCV with StratifiedKFold cross-validation on training data ONLY.
      2. Select best hyperparameters by f1_macro.
      3. Record cross-validation score.

    The test set is NEVER touched here.
    """
    print(f"\n{'='*60}")
    print("STEP 3: CROSS-VALIDATION + HYPERPARAMETER TUNING")
    print(f"        Scoring: {SCORING_METRIC} | CV folds: {CV_FOLDS}")
    print(f"{'='*60}")

    cv_strategy = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    tuned_results = {}

    for model_name, config in configs.items():
        print(f"\n  -- Tuning: {model_name} --")

        grid_search = GridSearchCV(
            estimator=config["pipeline"],
            param_grid=config["param_grid"],
            cv=cv_strategy,
            scoring=SCORING_METRIC,
            n_jobs=-1,
            verbose=0,
            refit=True,    # refit best model on entire training set after search
        )
        grid_search.fit(X_train, y_train)

        best_cv_score = grid_search.best_score_
        best_params = grid_search.best_params_

        print(f"    Best CV {SCORING_METRIC}: {best_cv_score:.4f}")
        print(f"    Best params: {best_params}")

        tuned_results[model_name] = {
            "best_estimator": grid_search.best_estimator_,
            "best_params": best_params,
            "cv_f1_macro": round(best_cv_score, 4),
        }

    return tuned_results


# ----------------------------------------------------------------------------─
# EVALUATION ON TEST SET
# ----------------------------------------------------------------------------─

def evaluate_on_test(tuned_results: dict, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """
    Evaluate each tuned model on the held-out test set.
    This is the FIRST time the test set is used.

    Computes:
      - Accuracy
      - Precision (macro + weighted)
      - Recall    (macro + weighted)
      - F1-score  (macro + weighted)
      - Full classification report
    """
    print(f"\n{'='*60}")
    print("STEP 4: EVALUATION ON HELD-OUT TEST SET")
    print(f"{'='*60}")

    evaluation_results = {}

    for model_name, result in tuned_results.items():
        pipeline = result["best_estimator"]
        y_pred = pipeline.predict(X_test)

        acc      = accuracy_score(y_test, y_pred)
        prec_mac = precision_score(y_test, y_pred, average="macro",    zero_division=0)
        rec_mac  = recall_score(y_test,   y_pred, average="macro",    zero_division=0)
        f1_mac   = f1_score(y_test,       y_pred, average="macro",    zero_division=0)
        prec_w   = precision_score(y_test, y_pred, average="weighted", zero_division=0)
        rec_w    = recall_score(y_test,   y_pred, average="weighted", zero_division=0)
        f1_w     = f1_score(y_test,       y_pred, average="weighted", zero_division=0)
        report   = classification_report(y_test, y_pred, target_names=CLASS_ORDER, zero_division=0)

        print(f"\n  -- {model_name} --")
        print(f"    Accuracy         : {acc:.4f}")
        print(f"    Precision (macro): {prec_mac:.4f}")
        print(f"    Recall    (macro): {rec_mac:.4f}")
        print(f"    F1        (macro): {f1_mac:.4f}")
        print(f"\n    Classification Report:")
        print(report)

        evaluation_results[model_name] = {
            "pipeline":        pipeline,
            "best_params":     result["best_params"],
            "cv_f1_macro":     result["cv_f1_macro"],
            "accuracy":        round(acc,      4),
            "precision_macro": round(prec_mac, 4),
            "recall_macro":    round(rec_mac,  4),
            "f1_macro":        round(f1_mac,   4),
            "precision_weighted": round(prec_w, 4),
            "recall_weighted":    round(rec_w,  4),
            "f1_weighted":        round(f1_w,   4),
            "classification_report": report,
            "y_pred": y_pred,
        }

    return evaluation_results


# ----------------------------------------------------------------------------─
# MODEL COMPARISON TABLE
# ----------------------------------------------------------------------------─

def print_comparison_table(evaluation_results: dict):
    """Print a formatted side-by-side comparison of all models."""
    print(f"\n{'='*60}")
    print("STEP 5: MODEL COMPARISON TABLE")
    print(f"{'='*60}")

    rows = []
    for model_name, res in evaluation_results.items():
        rows.append({
            "Model":        model_name,
            "Accuracy":     res["accuracy"],
            "Precision":    res["precision_macro"],
            "Recall":       res["recall_macro"],
            "F1 (macro)":   res["f1_macro"],
            "CV F1 (macro)": res["cv_f1_macro"],
        })

    df_compare = pd.DataFrame(rows).set_index("Model")
    print()
    print(df_compare.to_string())
    print()
    print(f"  Primary selection criterion: F1 (macro) on test set")


# ----------------------------------------------------------------------------─
# FINAL MODEL SELECTION
# ----------------------------------------------------------------------------─

def select_best_model(evaluation_results: dict) -> tuple:
    """
    Select the model with the highest macro F1 on the test set.
    Returns (model_name, result_dict).
    """
    print(f"\n{'='*60}")
    print("STEP 6: FINAL MODEL SELECTION")
    print(f"{'='*60}")

    best_name = max(evaluation_results, key=lambda m: evaluation_results[m]["f1_macro"])
    best = evaluation_results[best_name]

    print(f"\n  [OK] Best model: {best_name}")
    print(f"    F1 (macro) on test set: {best['f1_macro']:.4f}")

    return best_name, best


# ----------------------------------------------------------------------------─
# SAVE MODEL + METADATA
# ----------------------------------------------------------------------------─

def save_model_and_metadata(
    best_name: str,
    best_result: dict,
    numerical_features: list,
    categorical_features: list,
    dataset_type: str = "synthetic prototype",
    data_path: str = DATA_PATH,
    sample_count: int = 500,
):
    """
    Save the best pipeline and a metadata JSON to ai/models/.
    When dataset_type is 'synthetic prototype', also saves a permanent fallback copy.
    """
    print(f"\n{'='*60}")
    print("STEP 7: SAVE FINAL MODEL + METADATA")
    print(f"{'='*60}")

    os.makedirs(MODELS_DIR, exist_ok=True)

    # Save the trained pipeline
    joblib.dump(best_result["pipeline"], FINAL_MODEL_PATH)
    print(f"\n  Saved model -> {FINAL_MODEL_PATH}")

    # Build metadata — all values come from actual evaluation results
    dataset_note = (
        f"REAL NETWORK CAPTURE DATASET ({sample_count} sessions). "
        "Evaluated via 5-fold Stratified CV and held-out test split on real lab traffic."
        if dataset_type == "real"
        else (
            f"SYNTHETIC PROTOTYPE DATASET ({sample_count} sessions). "
            "Metrics reflect prototype/baseline performance only. "
            "Do NOT interpret as real-world network traffic performance."
        )
    )

    metadata = {
        "model_name":          best_name,
        "dataset_type":        dataset_type,
        "dataset_path":        os.path.relpath(data_path, BASE_DIR) if os.path.isabs(data_path) else data_path,
        "sample_count":        sample_count,
        "feature_names":       numerical_features + categorical_features,
        "numerical_features":  numerical_features,
        "categorical_features": categorical_features,
        "target_classes":      CLASS_ORDER,
        "training_config": {
            "test_size":         TEST_SIZE,
            "random_state":      RANDOM_STATE,
            "cv_folds":          CV_FOLDS,
            "scoring_metric":    SCORING_METRIC,
            "class_weight":      "balanced",
        },
        "best_hyperparameters": best_result["best_params"],
        "evaluation_metrics": {
            "accuracy":              best_result["accuracy"],
            "precision_macro":       best_result["precision_macro"],
            "recall_macro":          best_result["recall_macro"],
            "f1_macro":              best_result["f1_macro"],
            "precision_weighted":    best_result["precision_weighted"],
            "recall_weighted":       best_result["recall_weighted"],
            "f1_weighted":           best_result["f1_weighted"],
            "cv_f1_macro":           best_result["cv_f1_macro"],
        },
        "dataset_note": dataset_note,
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    print(f"  Saved metadata -> {METADATA_PATH}")

    # Preserve synthetic baseline model as permanent fallback
    fallback_model_path = os.path.join(MODELS_DIR, "synthetic_fallback_model.joblib")
    fallback_meta_path = os.path.join(MODELS_DIR, "synthetic_model_metadata.json")
    if dataset_type == "synthetic prototype" or not os.path.exists(fallback_model_path):
        joblib.dump(best_result["pipeline"], fallback_model_path)
        with open(fallback_meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
        print(f"  Preserved synthetic fallback model -> {fallback_model_path}")


# ----------------------------------------------------------------------------─
# CONFUSION MATRIX PLOT
# ----------------------------------------------------------------------------─

def plot_confusion_matrices(evaluation_results: dict, y_test: pd.Series, dataset_type: str = "synthetic prototype"):
    """
    Plot confusion matrices for all models side-by-side.
    Saved to ai/models/confusion_matrices.png
    """
    fig, axes = plt.subplots(1, len(evaluation_results), figsize=(6 * len(evaluation_results), 5))

    for ax, (model_name, res) in zip(axes, evaluation_results.items()):
        cm = confusion_matrix(y_test, res["y_pred"], labels=CLASS_ORDER)
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=CLASS_ORDER)
        disp.plot(ax=ax, colorbar=False, cmap="Blues")
        ax.set_title(f"{model_name}\n(F1 macro: {res['f1_macro']:.3f})", fontsize=11)

    title_dataset = "Real Lab Dataset" if dataset_type == "real" else "Synthetic Prototype Dataset"
    plt.suptitle(f"Confusion Matrices — Network Session Classification\n({title_dataset})", fontsize=13, y=1.02)
    plt.tight_layout()
    save_path = os.path.join(MODELS_DIR, "confusion_matrices.png")
    os.makedirs(MODELS_DIR, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Saved confusion matrices -> {save_path}")


# ----------------------------------------------------------------------------─
# COMPARISON BAR CHART
# ----------------------------------------------------------------------------─

def plot_model_comparison(evaluation_results: dict, dataset_type: str = "synthetic prototype"):
    """
    Bar chart comparing Accuracy, Precision, Recall, F1 across all models.
    Saved to ai/models/model_comparison.png
    """
    models = list(evaluation_results.keys())
    metrics = {
        "Accuracy":       [evaluation_results[m]["accuracy"]          for m in models],
        "Precision (macro)": [evaluation_results[m]["precision_macro"] for m in models],
        "Recall (macro)": [evaluation_results[m]["recall_macro"]      for m in models],
        "F1 (macro)":     [evaluation_results[m]["f1_macro"]          for m in models],
    }

    x = np.arange(len(models))
    width = 0.20
    fig, ax = plt.subplots(figsize=(10, 5))

    for i, (metric_name, values) in enumerate(metrics.items()):
        bars = ax.bar(x + i * width, values, width, label=metric_name)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=8)

    title_dataset = "Real Lab Dataset" if dataset_type == "real" else "Synthetic Prototype Dataset"
    ax.set_xlabel("Model")
    ax.set_ylabel("Score")
    ax.set_title(f"Model Comparison — Network Session Classification\n({title_dataset})")
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(models)
    ax.set_ylim(0, 1.10)
    ax.legend(loc="lower right")
    plt.tight_layout()

    save_path = os.path.join(MODELS_DIR, "model_comparison.png")
    os.makedirs(MODELS_DIR, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved model comparison chart -> {save_path}")


# ----------------------------------------------------------------------------─
# MAIN
# ----------------------------------------------------------------------------─

def main():
    parser = argparse.ArgumentParser(description="SentinelNet Machine Learning Training Pipeline")
    parser.add_argument(
        "--data",
        default=DATA_PATH,
        help="Path to training dataset CSV (default: data/raw/sentinelnet_sample_500.csv)",
    )
    parser.add_argument(
        "--dataset-type",
        choices=["real", "synthetic prototype"],
        default=None,
        help="Explicit dataset type declaration ('real' or 'synthetic prototype')",
    )
    args = parser.parse_args()

    data_path = os.path.abspath(args.data)
    if args.dataset_type:
        dataset_type = args.dataset_type
    elif "real" in data_path.lower():
        dataset_type = "real"
    else:
        dataset_type = "synthetic prototype"

    print("\n" + "=" * 65)
    print("SENTINELNET AI TRAINING PIPELINE")
    print("=" * 65)
    print(f"  Dataset path : {data_path}")
    print(f"  Dataset type : {dataset_type.upper()}")
    print("  Target classes: Human | Bot | Suspicious\n")

    # 1. Load
    df = load_data(data_path)

    # 2. Define features (no leakage columns)
    numerical_features, categorical_features, target = define_features()

    # 3. Split (stratified 80/20 — test set untouched until evaluation)
    X_train, X_test, y_train, y_test = split_data(
        df, numerical_features, categorical_features, target
    )

    # 4. Build preprocessor (fitted inside Pipeline — no leakage)
    preprocessor = build_preprocessor(numerical_features, categorical_features)

    # 5. Define model configs + hyperparameter grids
    configs = get_model_configs(preprocessor)

    # 6. GridSearchCV + StratifiedKFold on training data only
    tuned_results = tune_and_evaluate_models(configs, X_train, y_train)

    # 7. Evaluate all tuned models on held-out test set (first time test set is touched)
    evaluation_results = evaluate_on_test(tuned_results, X_test, y_test)

    # 8. Print comparison table
    print_comparison_table(evaluation_results)

    # 9. Select best model by macro F1
    best_name, best_result = select_best_model(evaluation_results)

    # 10. Save model and metadata
    save_model_and_metadata(
        best_name=best_name,
        best_result=best_result,
        numerical_features=numerical_features,
        categorical_features=categorical_features,
        dataset_type=dataset_type,
        data_path=data_path,
        sample_count=len(df),
    )

    # 11. Generate visualisations
    plot_confusion_matrices(evaluation_results, y_test, dataset_type=dataset_type)
    plot_model_comparison(evaluation_results, dataset_type=dataset_type)

    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"  Final model  : {best_name}")
    print(f"  Dataset type : {dataset_type}")
    print(f"  Saved to     : {FINAL_MODEL_PATH}")
    print(f"  Metadata     : {METADATA_PATH}")
    if dataset_type == "synthetic prototype":
        print(f"\n  NOTE: Results are from a SYNTHETIC PROTOTYPE dataset.")
        print(f"  Do not interpret metrics as real-world performance.\n")
    else:
        print(f"\n  [+] Model successfully trained on real network session captures.\n")


if __name__ == "__main__":
    main()
