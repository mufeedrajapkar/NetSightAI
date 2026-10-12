"""
adversarial_eval.py
-------------------
SentinelNet - Adversarial Evasion Robustness Evaluation Suite
=============================================================
Evaluates the robustness of the SentinelNet ML classifier, the Isolation Forest
anomaly detector, and the hybrid verdict engine against Tier 4 adversarial
mimicking bots.

Adversary Threat Model:
-----------------------
The attacker knows the feature set of the statistical network classifier.
The attacker shapes:
  1. Inter-arrival intervals (request_interval_mean, request_interval_var)
  2. Request rates (requests_per_sec)
  3. Packet sizes (packet_size_mean, packet_size_var via payload padding)
to match the empirical distributions observed in benign human traffic.

Evaluation:
-----------
Runs N simulated adversarial sessions through AIBridge and measures:
  - Classifier Evasion Rate: % classified as "Human" by the supervised model alone.
  - Anomaly Detector Evasion Rate: % not flagged by Isolation Forest.
  - Hybrid Defense Evasion Rate: % where final SentinelNet verdict remains "Human".
  - Suspicious Catch Rate: % diverted to "Suspicious" via hybrid consensus/anomaly logic.

Outputs:
  - ai/models/adversarial_results.json
"""

import os
import sys
import json
import numpy as np
import pandas as pd

# Add repo root to path
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_THIS_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from CN.agent.ai_bridge import AIBridge, REQUIRED_FEATURES

OUTPUT_JSON_PATH = os.path.join(_THIS_DIR, "models", "adversarial_results.json")
SYNTHETIC_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "sentinelnet_sample_500.csv")
REAL_DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "sentinelnet_real_dataset.csv")


def load_human_distribution():
    """Load empirical Human feature parameters from real or prototype dataset."""
    path = REAL_DATA_PATH if os.path.exists(REAL_DATA_PATH) else SYNTHETIC_DATA_PATH
    if not os.path.exists(path):
        # Fallback constants if data files are missing
        return {
            "request_interval_mean": (0.807, 0.513),
            "request_interval_var": (0.958, 1.507),
            "requests_per_sec": (1.734, 1.032),
            "packet_size_mean": (698.3, 217.0),
            "packet_size_var": (145692.0, 126734.0),
            "session_duration": (94.6, 65.2),
            "bytes_transferred": (110083.0, 116695.0),
            "num_connections": (6.17, 2.20),
        }

    df = pd.read_csv(path)
    h_df = df[df["label"] == "Human"]
    if len(h_df) == 0:
        h_df = df

    stats = {}
    for col in [
        "request_interval_mean", "request_interval_var", "requests_per_sec",
        "packet_size_mean", "packet_size_var", "session_duration",
        "bytes_transferred", "num_connections"
    ]:
        if col in h_df.columns:
            stats[col] = (float(h_df[col].mean()), float(h_df[col].std()))
        else:
            stats[col] = (1.0, 0.5)
    return stats


def generate_adversarial_sessions(n_samples: int = 100, mode: str = "full_mimicry", seed: int = 42):
    """
    Generate synthetic feature rows representing Tier 4 adversarial sessions.
    Mode 'delay_only': Shapes intervals and rate to human, but packet sizes remain bot-like.
    Mode 'full_mimicry': Shapes intervals, rates, and packet sizes into human distribution.
    """
    rng = np.random.default_rng(seed)
    h_stats = load_human_distribution()

    sessions = []
    for i in range(n_samples):
        # Sample human-like timing
        interval_mean = max(0.1, rng.normal(h_stats["request_interval_mean"][0], h_stats["request_interval_mean"][1]))
        interval_var = max(0.01, rng.normal(h_stats["request_interval_var"][0], h_stats["request_interval_var"][1]))
        rps = max(0.2, rng.normal(h_stats["requests_per_sec"][0], h_stats["requests_per_sec"][1]))

        if mode in ("full_mimicry", "full_feature_mimicry"):
            # Attacker shapes packet sizes and timing
            pkt_mean = max(64.0, rng.normal(h_stats["packet_size_mean"][0], h_stats["packet_size_mean"][1]))
            pkt_var = max(100.0, rng.normal(h_stats["packet_size_var"][0], h_stats["packet_size_var"][1]))
            duration = max(5.0, rng.normal(h_stats["session_duration"][0], h_stats["session_duration"][1]))
            bytes_tx = max(1000.0, rng.normal(h_stats["bytes_transferred"][0], h_stats["bytes_transferred"][1]))
            conns = max(1, int(round(rng.normal(h_stats["num_connections"][0], h_stats["num_connections"][1]))))
        else:
            # Attacker only shapes timing; payload is automated/fixed (small packets, 1 connection)
            pkt_mean = 250.0 + rng.normal(0, 30.0)
            pkt_var = 500.0 + rng.normal(0, 50.0)
            duration = max(5.0, rng.normal(30.0, 10.0))
            bytes_tx = pkt_mean * rps * duration
            conns = 1

        session = {
            "session_id": f"adv_sess_{mode}_{i:03d}",
            "device_id": f"device_adv_{i % 5:02d}",
            "requests_per_sec": float(round(rps, 4)),
            "session_duration": float(round(duration, 3)),
            "packet_size_mean": float(round(pkt_mean, 2)),
            "packet_size_var": float(round(pkt_var, 2)),
            "request_interval_mean": float(round(interval_mean, 4)),
            "request_interval_var": float(round(interval_var, 4)),
            "bytes_transferred": float(round(bytes_tx, 1)),
            "num_connections": int(conns),
            "protocol": "TCP",
            "label": "bot_adversarial",
            "bot_tier": "tier4",
            "provenance": "simulated",
        }
        sessions.append(session)

    return sessions


def evaluate_adversarial(n_samples: int = 100):
    """Run evaluation and save adversarial benchmark results."""
    print("=" * 70)
    print("SentinelNet -- Tier 4 Adversarial Evasion Robustness Benchmark")
    print("=" * 70)

    bridge = AIBridge()

    # Evaluate both delay-only and full mimicry
    scenarios = [
        ("delay_mimicry_only", "Adversary manipulates request intervals and rates only"),
        ("full_feature_mimicry", "Adversary shapes timing, rate, and packet size distributions")
    ]

    scenario_results = {}

    for mode, description in scenarios:
        samples = generate_adversarial_sessions(n_samples=n_samples, mode=mode if mode != "delay_mimicry_only" else "delay_only")
        
        raw_preds = []
        verdicts = []
        if_anomalies = []
        anomaly_scores = []
        disagreements = []

        for row in samples:
            res = bridge.predict(row)
            raw_preds.append(res["raw_prediction"])
            verdicts.append(res["verdict"])
            if_anomalies.append(res["is_anomaly"])
            anomaly_scores.append(res["anomaly_score"])
            disagreements.append(res["disagreement"])

        total = len(samples)
        # Evasion against supervised classifier alone: how many were classified "Human"
        classifier_evasions = sum(1 for p in raw_preds if p == "Human")
        classifier_evasion_rate = classifier_evasions / total

        # Evasion against Isolation Forest alone: how many avoided anomaly flag
        if_evasions = sum(1 for a in if_anomalies if a is False)
        if_evasion_rate = if_evasions / total

        # Evasion against full hybrid SentinelNet verdict: how many ended up with "Human" verdict
        hybrid_evasions = sum(1 for v in verdicts if v == "Human")
        hybrid_evasion_rate = hybrid_evasions / total

        # How many were flagged as Suspicious by hybrid defense
        suspicious_verdicts = sum(1 for v in verdicts if v == "Suspicious")
        suspicious_rate = suspicious_verdicts / total

        # How many were caught outright as Bot
        bot_verdicts = sum(1 for v in verdicts if v == "Bot")
        bot_rate = bot_verdicts / total

        scenario_results[mode] = {
            "description": description,
            "total_sessions": total,
            "classifier_evasion_rate": round(classifier_evasion_rate, 4),
            "isolation_forest_evasion_rate": round(if_evasion_rate, 4),
            "hybrid_sentinelnet_evasion_rate": round(hybrid_evasion_rate, 4),
            "suspicious_rescue_rate": round(suspicious_rate, 4),
            "bot_detection_rate": round(bot_rate, 4),
            "mean_anomaly_score": round(float(np.mean([s for s in anomaly_scores if s is not None])), 4) if anomaly_scores else None,
            "disagreement_rate": round(sum(1 for d in disagreements if d) / total, 4),
        }

        print(f"\nScenario: {mode} ({description})")
        print(f"  Sessions tested:             {total}")
        print(f"  Classifier Evasion Rate:     {classifier_evasion_rate * 100:.1f}% (supervised model fooled)")
        print(f"  Isolation Forest Evasion:    {if_evasion_rate * 100:.1f}%")
        print(f"  Suspicious Verdict Catches:  {suspicious_rate * 100:.1f}% (hybrid defense rescue)")
        print(f"  Outright Bot Verdicts:       {bot_rate * 100:.1f}%")
        print(f"  Final SentinelNet Evasion:   {hybrid_evasion_rate * 100:.1f}% (uncaught sessions)")

    # Security Analysis & Recommendations
    vulnerability_analysis = (
        "Statistical L4/L7 flow features (inter-arrival intervals, request rates, packet sizes) "
        "can be manipulated by a sophisticated adversary to mimic benign human distributions. "
        "While timing manipulation partially fools the Random Forest classifier, "
        "the Isolation Forest and hybrid verdict engine flag anomalies or disagreements as 'Suspicious'."
    )

    recommended_countermeasures = [
        {
            "dimension": "Transport Layer (CN)",
            "feature": "TCP Window Size & Initial Congestion Window Dynamics",
            "rationale": "Real OS TCP stacks (Linux, Windows, iOS) follow distinct congestion control window trajectories that synthetic socket bots rarely match."
        },
        {
            "dimension": "Cryptographic / TLS Layer",
            "feature": "TLS Client Hello Fingerprinting (JA3 / JA4 / Cipher Suites)",
            "rationale": "Python requests/urllib TLS fingerprint differs drastically from real modern browsers (Chrome/Firefox/Safari TLS extensions, GREASE)."
        },
        {
            "dimension": "Application Layer Telemetry",
            "feature": "Payload Byte Entropy & Header Ordering",
            "rationale": "Automated payload generators exhibit repeated patterns and non-standard HTTP/2 header sequences."
        },
        {
            "dimension": "Client Interaction (L7)",
            "feature": "Biometric DOM & Mouse Movement Telemetry",
            "rationale": "Physical input events (bezier-curve mouse velocity, keystroke flight times) are orthogonal to network packet timings."
        }
    ]

    output_payload = {
        "status": "success",
        "benchmark_provenance": "simulated",
        "scenarios": scenario_results,
        "vulnerability_analysis": vulnerability_analysis,
        "recommended_countermeasures": recommended_countermeasures,
    }

    os.makedirs(os.path.dirname(OUTPUT_JSON_PATH), exist_ok=True)
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    print(f"\n[+] Adversarial evaluation results saved to: {OUTPUT_JSON_PATH}")
    return output_payload


if __name__ == "__main__":
    evaluate_adversarial(n_samples=100)
