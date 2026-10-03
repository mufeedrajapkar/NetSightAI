"""
explainability.py
-----------------
CN_AI Project — Network Session Classification
-----------------------------------------------
This script answers:

  "Why did the model classify this network session as Human, Bot, or Suspicious?"

Uses SHAP (SHapley Additive exPlanations) to explain predictions.

Workflow:
  Network session
        |
  Preprocessing (inside Pipeline)
        |
  Final ML model
        |
  Prediction
        |
  SHAP explanation
        |
  Important contributing features

Supports:
  - Global feature importance (what the model relies on overall)
  - Individual session explanation (why THIS session got THIS label)

NOTE: The dataset is a SYNTHETIC PROTOTYPE.
      Explanations reflect learned patterns from synthetic data.
      Do NOT interpret as real-world network behaviour.

Run AFTER train_models.py has been executed and final_model.joblib exists.
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")   # non-interactive backend — safe for scripts without a display
import matplotlib.pyplot as plt
import shap

from sklearn.model_selection import train_test_split
import joblib

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "sentinelnet_sample_500.csv")
MODELS_DIR = os.path.join(BASE_DIR, "ai", "models")
FINAL_MODEL_PATH = os.path.join(MODELS_DIR, "final_model.joblib")
METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")

CLASS_ORDER = ["Human", "Bot", "Suspicious"]


# ─────────────────────────────────────────────────────────────────────────────
# LOAD MODEL + METADATA
# ─────────────────────────────────────────────────────────────────────────────

def load_model_and_metadata():
    """Load the saved pipeline and metadata."""
    print(f"\n{'='*60}")
    print("LOAD MODEL + METADATA")
    print(f"{'='*60}")

    if not os.path.exists(FINAL_MODEL_PATH):
        raise FileNotFoundError(
            f"Model not found at {FINAL_MODEL_PATH}.\n"
            "Run ai/train_models.py first."
        )

    pipeline = joblib.load(FINAL_MODEL_PATH)
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    print(f"  Model       : {metadata['model_name']}")
    print(f"  Features    : {metadata['feature_names']}")
    return pipeline, metadata


# ─────────────────────────────────────────────────────────────────────────────
# RECREATE TEST SET
# ─────────────────────────────────────────────────────────────────────────────

def recreate_test_set(metadata: dict):
    """Recreate the exact held-out test set (reproducible via fixed random_state)."""
    df = pd.read_csv(DATA_PATH)
    feature_cols = metadata["feature_names"]
    X = df[feature_cols]
    y = df["label"]

    _, X_test, _, y_test = train_test_split(
        X, y,
        test_size=metadata["training_config"]["test_size"],
        random_state=metadata["training_config"]["random_state"],
        stratify=y,
    )
    return X_test.reset_index(drop=True), y_test.reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACT PREPROCESSOR AND CLASSIFIER FROM PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def extract_pipeline_components(pipeline):
    """
    Extract the preprocessor and classifier from the sklearn Pipeline.
    The preprocessor transforms raw features; the classifier makes predictions.
    """
    preprocessor = pipeline.named_steps["preprocessor"]
    classifier   = pipeline.named_steps["classifier"]
    return preprocessor, classifier


def get_feature_names_after_preprocessing(preprocessor, numerical_features: list, categorical_features: list) -> list:
    """
    Get the final feature names after ColumnTransformer transformation.
    Numerical features keep their names; OneHotEncoded features get new names.
    """
    num_names = numerical_features.copy()

    # Get OHE feature names (e.g. "protocol_UDP" after drop='first')
    cat_encoder = preprocessor.named_transformers_["cat"]
    cat_names = cat_encoder.get_feature_names_out(categorical_features).tolist()

    return num_names + cat_names


# ─────────────────────────────────────────────────────────────────────────────
# BUILD SHAP EXPLAINER
# ─────────────────────────────────────────────────────────────────────────────

def build_shap_explainer(classifier, X_transformed: np.ndarray, model_name: str):
    """
    Build the appropriate SHAP explainer based on the model type:
      - Tree-based models (Random Forest): TreeExplainer (fast, exact)
      - Linear models (Logistic Regression): LinearExplainer
      - Other (SVM, etc.): KernelExplainer (model-agnostic, slower)

    We use a small background sample for KernelExplainer to keep it fast.
    """
    print(f"\n  Building SHAP explainer for: {model_name}")

    model_type = model_name.lower()

    if "random forest" in model_type or "forest" in model_type or "tree" in model_type:
        explainer = shap.TreeExplainer(classifier)
        print("  Using: TreeExplainer (exact, fast)")
    elif "logistic" in model_type or "linear" in model_type:
        explainer = shap.LinearExplainer(classifier, X_transformed)
        print("  Using: LinearExplainer")
    else:
        # Model-agnostic fallback — use a small background sample
        background = shap.sample(X_transformed, min(50, X_transformed.shape[0]))
        explainer = shap.KernelExplainer(classifier.predict_proba, background)
        print("  Using: KernelExplainer (model-agnostic fallback)")

    return explainer


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL FEATURE IMPORTANCE (bar chart from SHAP)
# ─────────────────────────────────────────────────────────────────────────────

def global_feature_importance(shap_values, feature_names: list, model_name: str, class_names: list):
    """
    Compute and visualize global feature importance using mean |SHAP value|.

    For multiclass: shap_values shape is (n_samples, n_features, n_classes)
    We aggregate across all classes using mean absolute SHAP value per feature.
    """
    print(f"\n{'='*60}")
    print("GLOBAL FEATURE IMPORTANCE (SHAP)")
    print(f"{'='*60}")

    # Handle both old-style list and new Explanation object
    if hasattr(shap_values, "values"):
        sv = shap_values.values   # (n_samples, n_features, n_classes) or (n_samples, n_features)
    else:
        sv = np.array(shap_values)  # list of arrays for multiclass

    if sv.ndim == 3:
        # Multiclass: average |SHAP| across all classes
        mean_abs_shap = np.mean(np.abs(sv), axis=(0, 2))
    elif isinstance(shap_values, list):
        # Old-style list of per-class arrays
        mean_abs_shap = np.mean([np.abs(sv_c) for sv_c in shap_values], axis=0).mean(axis=0)
    else:
        mean_abs_shap = np.abs(sv).mean(axis=0)

    importance_df = pd.DataFrame({
        "Feature": feature_names,
        "Mean |SHAP|": mean_abs_shap,
    }).sort_values("Mean |SHAP|", ascending=False)

    print("\n  Feature importance ranking (mean |SHAP value|):")
    print(f"  {'Rank':<5} {'Feature':<30} {'Mean |SHAP|'}")
    print(f"  {'-'*55}")
    for i, (_, row) in enumerate(importance_df.iterrows(), 1):
        bar = "#" * int(row["Mean |SHAP|"] * 100)
        print(f"  {i:<5} {row['Feature']:<30} {row['Mean |SHAP|']:.4f}  |{bar}")

    # Save bar chart
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = plt.cm.RdYlGn_r(
        np.linspace(0.2, 0.8, len(importance_df))
    )
    bars = ax.barh(importance_df["Feature"][::-1], importance_df["Mean |SHAP|"][::-1], color=colors[::-1])
    ax.set_xlabel("Mean |SHAP value| (impact on prediction)")
    ax.set_title(
        f"Global Feature Importance — {model_name}\n"
        f"(Synthetic Prototype Dataset)"
    )
    for bar, val in zip(bars, importance_df["Mean |SHAP|"][::-1]):
        ax.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height() / 2,
                f"{val:.4f}", va="center", fontsize=9)
    plt.tight_layout()

    save_path = os.path.join(MODELS_DIR, "shap_global_importance.png")
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Saved global importance chart -> {save_path}")

    return importance_df


# ─────────────────────────────────────────────────────────────────────────────
# INDIVIDUAL SESSION EXPLANATION
# ─────────────────────────────────────────────────────────────────────────────

def explain_single_session(
    pipeline,
    explainer,
    session_dict: dict,
    feature_names: list,
    shap_feature_names: list,
    model_name: str,
    class_names: list,
):
    """
    Explain why the model classified a single network session with a specific label.

    Prints the prediction, confidence, and which features pushed the decision
    toward or away from each class.
    """
    print(f"\n{'='*60}")
    print("INDIVIDUAL SESSION EXPLANATION")
    print(f"  (Synthetic example — not real traffic)")
    print(f"{'='*60}")

    # Build input DataFrame in correct feature order
    input_df = pd.DataFrame([session_dict])[feature_names]

    # Predict
    prediction   = pipeline.predict(input_df)[0]
    probabilities = pipeline.predict_proba(input_df)[0]
    classes       = list(pipeline.classes_)

    print(f"\n  Session features:")
    for k, v in session_dict.items():
        print(f"    {k:<30}: {v}")

    print(f"\n  Prediction  : {prediction}")
    print(f"  Confidence breakdown:")
    for cls, prob in sorted(zip(classes, probabilities), key=lambda x: -x[1]):
        bar = "#" * int(prob * 30)
        print(f"    {cls:<12}: {prob:.4f}  |{bar}")

    # Transform through preprocessor for SHAP
    preprocessor = pipeline.named_steps["preprocessor"]
    X_transformed = preprocessor.transform(input_df)

    try:
        sv = explainer.shap_values(X_transformed)
    except Exception as e:
        print(f"\n  [Warning] SHAP explanation failed: {e}")
        print("  Skipping per-feature breakdown.")
        return

    # Handle output shape differences across SHAP versions
    if isinstance(sv, list):
        # Old style: list of (n_samples, n_features) per class
        pred_class_idx = classes.index(prediction)
        sv_for_pred = sv[pred_class_idx][0]
    elif hasattr(sv, "values"):
        sv_arr = sv.values
        if sv_arr.ndim == 3:
            pred_class_idx = classes.index(prediction)
            sv_for_pred = sv_arr[0, :, pred_class_idx]
        else:
            sv_for_pred = sv_arr[0]
    else:
        sv_arr = np.array(sv)
        if sv_arr.ndim == 3:
            pred_class_idx = classes.index(prediction)
            sv_for_pred = sv_arr[0, :, pred_class_idx]
        else:
            sv_for_pred = sv_arr[0]

    print(f"\n  Feature contributions toward '{prediction}' (SHAP values):")
    print(f"  {'Feature':<30} {'SHAP value':>12}  Direction")
    print(f"  {'-'*60}")

    contrib_df = pd.DataFrame({
        "Feature": shap_feature_names,
        "SHAP": sv_for_pred,
    }).sort_values("SHAP", key=abs, ascending=False)

    for _, row in contrib_df.iterrows():
        direction = "pushes -> " + prediction if row["SHAP"] > 0 else "pushes away"
        print(f"  {row['Feature']:<30} {row['SHAP']:>12.4f}  {direction}")

    # Waterfall-style text summary
    top = contrib_df.head(3)
    print(f"\n  Top 3 influential features for this prediction:")
    for i, (_, row) in enumerate(top.iterrows(), 1):
        sign = "+" if row["SHAP"] > 0 else ""
        print(f"    {i}. {row['Feature']}: SHAP = {sign}{row['SHAP']:.4f}")


# ─────────────────────────────────────────────────────────────────────────────
# SHAP SUMMARY PLOT (beeswarm)
# ─────────────────────────────────────────────────────────────────────────────

def plot_shap_summary(shap_values, X_transformed: np.ndarray, shap_feature_names: list, model_name: str):
    """
    Generate SHAP summary (beeswarm) plot for the test set.
    For multiclass: we use the mean across classes for a single aggregated view.
    """
    # Handle multiclass shap_values
    if isinstance(shap_values, list):
        sv_mean = np.mean([np.abs(sv) for sv in shap_values], axis=0)
    elif hasattr(shap_values, "values"):
        sv_arr = shap_values.values
        if sv_arr.ndim == 3:
            sv_mean = np.mean(np.abs(sv_arr), axis=2)
        else:
            sv_mean = sv_arr
    else:
        sv_arr = np.array(shap_values)
        if sv_arr.ndim == 3:
            sv_mean = np.mean(np.abs(sv_arr), axis=2)
        else:
            sv_mean = sv_arr

    fig, ax = plt.subplots(figsize=(8, 5))
    mean_abs = sv_mean.mean(axis=0)
    sorted_idx = np.argsort(mean_abs)[::-1]

    colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(sorted_idx)))
    ax.barh(
        [shap_feature_names[i] for i in sorted_idx[::-1]],
        mean_abs[sorted_idx[::-1]],
        color=colors,
    )
    ax.set_xlabel("Mean |SHAP value|")
    ax.set_title(f"SHAP Feature Importance (Test Set Aggregate)\n{model_name} — Synthetic Prototype")
    plt.tight_layout()

    save_path = os.path.join(MODELS_DIR, "shap_summary.png")
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Saved SHAP summary plot -> {save_path}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("\nCN_AI -- explainability.py")
    print("SHAP-based explanation of network session predictions.")
    print("Dataset: SYNTHETIC PROTOTYPE (500 sessions)\n")

    # 1. Load model and metadata
    pipeline, metadata = load_model_and_metadata()
    model_name = metadata["model_name"]
    feature_names = metadata["feature_names"]
    numerical_features = metadata["numerical_features"]
    categorical_features = metadata["categorical_features"]

    # 2. Recreate test set
    X_test, y_test = recreate_test_set(metadata)

    # 3. Extract preprocessor + classifier
    preprocessor, classifier = extract_pipeline_components(pipeline)

    # 4. Get transformed feature names (after OHE)
    shap_feature_names = get_feature_names_after_preprocessing(
        preprocessor, numerical_features, categorical_features
    )
    print(f"\n  Transformed feature names: {shap_feature_names}")

    # 5. Transform test set through preprocessor
    X_test_transformed = preprocessor.transform(X_test)

    # 6. Build SHAP explainer
    print(f"\n{'='*60}")
    print("BUILD SHAP EXPLAINER")
    print(f"{'='*60}")
    explainer = build_shap_explainer(classifier, X_test_transformed, model_name)

    # 7. Compute SHAP values for test set
    print(f"\n  Computing SHAP values for {X_test_transformed.shape[0]} test samples ...")
    shap_values = explainer.shap_values(X_test_transformed)
    print("  SHAP values computed.")

    # 8. Global feature importance
    importance_df = global_feature_importance(
        shap_values, shap_feature_names, model_name, CLASS_ORDER
    )

    # 9. SHAP summary plot
    plot_shap_summary(shap_values, X_test_transformed, shap_feature_names, model_name)

    # 10. Individual session explanation — synthetic Bot example
    bot_session = {
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
    explain_single_session(
        pipeline, explainer, bot_session,
        feature_names, shap_feature_names,
        model_name, CLASS_ORDER,
    )

    # 11. Individual session explanation — synthetic Human example
    human_session = {
        "requests_per_sec": 1.2,
        "session_duration": 250.0,
        "packet_size_mean": 1200.0,
        "packet_size_var": 800.0,
        "request_interval_mean": 5.5,
        "request_interval_var": 12.0,
        "bytes_transferred": 95000,
        "num_connections": 4,
        "protocol": "TCP",
    }
    explain_single_session(
        pipeline, explainer, human_session,
        feature_names, shap_feature_names,
        model_name, CLASS_ORDER,
    )

    print(f"\n{'='*60}")
    print("EXPLAINABILITY COMPLETE")
    print(f"{'='*60}")
    print(f"\n  Files saved to: {MODELS_DIR}")
    print(f"    shap_global_importance.png")
    print(f"    shap_summary.png\n")


if __name__ == "__main__":
    main()
