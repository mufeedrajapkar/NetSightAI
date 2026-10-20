"""
bot_tier_analysis.py
--------------------
CN_AI Project — Bot Sophistication Tier Difficulty Experiment

Evaluates the trained SentinelNet classification model across distinct bot tiers:
  - Human (baseline non-adversarial traffic)
  - Tier 1: Naive Bot (fixed 0.5s interval, deterministic)
  - Tier 2: Jittered Bot (random 0.2s - 2.0s uniform intervals)
  - Tier 3: Mimicking Bot (empirical human interval sampling + pauses)

Outputs:
  - ai/models/bot_tier_results.json: structured evaluation matrix and feature separation stats
  - ai/models/bot_tier_curve.png: visualization of Detection F1 vs Bot Sophistication Tier
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "ai", "models")
MODEL_PATH = os.path.join(MODELS_DIR, "final_model.joblib")
SYNTHETIC_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "sentinelnet_sample_500.csv")
REAL_DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "sentinelnet_real_dataset.csv")
RESULTS_JSON_PATH = os.path.join(MODELS_DIR, "bot_tier_results.json")
PLOT_PATH = os.path.join(MODELS_DIR, "bot_tier_curve.png")

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

TIER_METADATA = {
    "Tier1": {
        "id": "tier1",
        "name": "Tier 1 - Naive Bot",
        "sophistication": "Low",
        "description": "Fixed 0.5s interval requests against single endpoint; deterministic timing profile.",
    },
    "Tier2": {
        "id": "tier2",
        "name": "Tier 2 - Jittered Bot",
        "sophistication": "Medium",
        "description": "Uniform random delays (0.2s - 2.0s), randomized queries, rotating User-Agents.",
    },
    "Tier3": {
        "id": "tier3",
        "name": "Tier 3 - Mimicking Bot",
        "sophistication": "High",
        "description": "Empirical human delay distribution, reading pauses (5-15s), realistic browsing paths.",
    },
}


def compute_feature_separation(human_df: pd.DataFrame, tier_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Compute standardized mean difference (Cohen's d) between Human and Tier features.
    Smallest distance represents features that separate the tier from Human the LEAST.
    """
    separation = []
    for col in NUMERICAL_FEATURES:
        if col in human_df.columns and col in tier_df.columns:
            h_vals = human_df[col].dropna()
            t_vals = tier_df[col].dropna()

            h_mean, t_mean = h_vals.mean(), t_vals.mean()
            h_var, t_var = h_vals.var(ddof=1), t_vals.var(ddof=1)
            pooled_std = np.sqrt(((h_var if not np.isnan(h_var) else 0) + (t_var if not np.isnan(t_var) else 0)) / 2.0 + 1e-9)

            d = abs(h_mean - t_mean) / pooled_std if pooled_std > 0 else 0.0
            separation.append({
                "feature": col,
                "cohens_d": round(float(d), 4),
                "human_mean": round(float(h_mean), 4),
                "tier_mean": round(float(t_mean), 4),
            })

    # Sort ascending so least-separated (hardest to distinguish) features come first
    separation.sort(key=lambda x: x["cohens_d"])
    return separation


def evaluate_tier_experiment(
    data_path: str, model_path: str
) -> Dict[str, Any]:
    """
    Run complete bot tier analysis against the trained classifier.
    """
    print("\n" + "=" * 65)
    print("BOT TIER BEHAVIORAL DIFFICULTY EXPERIMENT")
    print("=" * 65)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Trained model not found at: {model_path}. Run ai/train_models.py first.")

    # 1. Determine dataset source
    is_real = False
    chosen_path = data_path
    if data_path and os.path.exists(data_path):
        chosen_path = data_path
        if "real" in chosen_path.lower():
            is_real = True
    elif os.path.exists(REAL_DATA_PATH):
        chosen_path = REAL_DATA_PATH
        is_real = True
    else:
        chosen_path = SYNTHETIC_DATA_PATH
        print(f"\n[!] NOTICE: Real dataset not found. Falling back to synthetic prototype dataset:")
        print(f"    Path: {SYNTHETIC_DATA_PATH}")

    df = pd.read_csv(chosen_path)
    print(f"  Loaded dataset   : {chosen_path}")
    print(f"  Dataset origin   : {'REAL CAPTURES' if is_real else 'SYNTHETIC PROTOTYPE'}")
    print(f"  Total sessions   : {len(df)}")

    # 2. Load model
    pipeline = joblib.load(model_path)
    model_name = getattr(pipeline.named_steps.get("classifier"), "__class__", type(pipeline)).__name__
    print(f"  Evaluating Model : {model_name}\n")

    # 3. Separate Human and Tiers
    human_df = df[df["label"].str.lower() == "human"].copy()
    if human_df.empty:
        raise ValueError("Dataset does not contain any 'Human' labeled sessions!")

    # Ground truth predictions on human
    human_preds = pipeline.predict(human_df)
    human_probs = pipeline.predict_proba(human_df) if hasattr(pipeline, "predict_proba") else None
    classes = list(pipeline.classes_)
    bot_idx = classes.index("Bot") if "Bot" in classes else 0
    human_idx = classes.index("Human") if "Human" in classes else 0

    results_by_tier = []
    plot_tiers = []
    plot_f1s = []
    plot_recalls = []

    print("-" * 65)
    print(f"{'Tier':<22} | {'Samples':<7} | {'Det Rate':<9} | {'Precision':<9} | {'F1':<6}")
    print("-" * 65)

    for tier_key, meta in TIER_METADATA.items():
        # Match case-insensitively
        tier_mask = df["bot_tier"].astype(str).str.lower() == tier_key.lower()
        tier_df = df[tier_mask].copy()

        if tier_df.empty:
            print(f"{meta['name']:<22} | {'0 (skip)':<7} | {'N/A':<9} | {'N/A':<9} | {'N/A':<6}")
            continue

        tier_preds = pipeline.predict(tier_df)
        tier_probs = pipeline.predict_proba(tier_df) if hasattr(pipeline, "predict_proba") else None

        # Binary confusion vs Human
        # Positive class: Bot (from tier)
        # Negative class: Human
        tp = np.sum(tier_preds == "Bot")
        fn = np.sum(tier_preds != "Bot")
        fp = np.sum(human_preds == "Bot")
        tn = np.sum(human_preds != "Bot")

        det_rate = float(tp / len(tier_df)) if len(tier_df) > 0 else 0.0
        precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = det_rate
        f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        mean_bot_p = float(np.mean(tier_probs[:, bot_idx])) if tier_probs is not None else 0.0
        mean_human_p = float(np.mean(tier_probs[:, human_idx])) if tier_probs is not None else 0.0

        separation = compute_feature_separation(human_df, tier_df)
        least_separated = separation[:3]  # top 3 closest to human

        is_match = (f1 >= 0.70)
        status_label = "Match (Bot)" if is_match else "Mismatch / Evading (Human)"

        behavior_notes = (
            f"Least separated features from Human: {', '.join([x['feature'] for x in least_separated])}. "
            f"Mean bot confidence: {mean_bot_p*100:.2f}%, mean human confidence: {mean_human_p*100:.2f}%."
        )

        tier_res = {
            "id": meta["id"],
            "name": meta["name"],
            "sophistication": meta["sophistication"],
            "description": meta["description"],
            "sample_count": len(tier_df),
            "expected_label": "Bot",
            "baseline_result": status_label,
            "detection_rate": round(det_rate, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "bot_probability": round(mean_bot_p, 6),
            "human_probability": round(mean_human_p, 6),
            "least_separated_features": least_separated,
            "all_feature_separation": separation,
            "behavior_notes": behavior_notes,
        }

        results_by_tier.append(tier_res)
        plot_tiers.append(meta["name"].split(" - ")[0])
        plot_f1s.append(f1)
        plot_recalls.append(recall)

        print(f"{meta['name']:<22} | {len(tier_df):<7} | {det_rate*100:>7.2f}% | {precision*100:>7.2f}% | {f1:.4f}")

    print("-" * 65 + "\n")

    # 4. Generate Plot: Detection F1 vs Bot Sophistication Tier
    os.makedirs(MODELS_DIR, exist_ok=True)
    if plot_tiers:
        fig, ax = plt.subplots(figsize=(8, 5))
        x = np.arange(len(plot_tiers))
        width = 0.35

        rects1 = ax.bar(x - width/2, plot_f1s, width, label='F1 Score', color='#3b82f6')
        rects2 = ax.bar(x + width/2, plot_recalls, width, label='Detection Rate (Recall)', color='#10b981')

        ax.set_ylabel('Score', fontsize=11)
        ax.set_title(f'Bot Tier Detection Difficulty Curve\n({"Real Captured Dataset" if is_real else "Synthetic Prototype Dataset"})', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(plot_tiers, fontsize=10)
        ax.set_ylim(0, 1.15)
        ax.legend(loc='upper right')
        ax.grid(axis='y', linestyle='--', alpha=0.5)

        for rect in rects1 + rects2:
            height = rect.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        plt.savefig(PLOT_PATH, dpi=150)
        plt.close()
        print(f"  [OK] Saved difficulty curve plot -> {PLOT_PATH}")

    # 5. Save structured JSON
    matches_count = sum(1 for t in results_by_tier if "Match" in t["baseline_result"] and "Mismatch" not in t["baseline_result"])
    mismatches_count = len(results_by_tier) - matches_count

    output_payload = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "model_type": model_name,
        "dataset_type": "real" if is_real else "synthetic prototype",
        "dataset_path": os.path.relpath(chosen_path, BASE_DIR) if os.path.isabs(chosen_path) else chosen_path,
        "tiers": results_by_tier,
        "evaluation_summary": {
            "total_tiers": len(results_by_tier),
            "matches": matches_count,
            "mismatches": mismatches_count,
            "source": f"Empirical Model Evaluation ({'Real' if is_real else 'Synthetic Prototype'} Data)",
            "limitation_note": (
                "Real traffic exhibits distinct distribution properties. "
                "Higher sophistication tiers incorporate human pause dynamics that decrease detection F1."
            ),
        },
    }

    with open(RESULTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=4)
    print(f"  [OK] Saved structured results   -> {RESULTS_JSON_PATH}\n")

    return output_payload


def main():
    parser = argparse.ArgumentParser(description="SentinelNet Bot Tier Difficulty Experiment CLI")
    parser.add_argument("--data", default=None, help="Path to evaluation dataset CSV")
    parser.add_argument("--model", default=MODEL_PATH, help="Path to trained model joblib")
    args = parser.parse_args()

    try:
        evaluate_tier_experiment(args.data, args.model)
    except Exception as exc:
        print(f"\n[ERROR] Bot tier evaluation failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
