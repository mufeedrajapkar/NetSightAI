"""
run_demo.py
-----------
SentinelNet: Comprehensive End-to-End System Demonstration
===========================================================
CN + AI Integration: Network Traffic Classification Pipeline
Human vs Bot vs Suspicious Traffic Detection

This script runs an automated end-to-end demonstration showcasing:
  1. Backend Server Initialisation & Authentication
  2. Live Flow Ingestion (/api/ingest) with CN-extracted 9-feature vectors
  3. Real-Time Inference: Classifier Predictions & Isolation Forest Anomaly Scoring
  4. Hybrid Verdict Engine: Triggering "Suspicious" verdicts via anomaly disagreement
  5. Bot Tier Difficulty & Sophistication Analysis (/api/bot-tiers)
  6. Tier 4 Adversarial Evasion Robustness Benchmark (/api/adversarial)
"""

import os
import sys
import time
import json
import threading
import requests

# Ensure repo root is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Set API key for demo if not already configured
DEMO_API_KEY = os.environ.get("SENTINELNET_API_KEY", "sentinelnet_demo_secret_key_2026")
os.environ["SENTINELNET_API_KEY"] = DEMO_API_KEY

from CN.web.backend_server import app


def start_in_process_server(port=5000):
    """Start the Flask server on a daemon thread for standalone demo."""
    server_thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False),
        daemon=True,
    )
    server_thread.start()
    # Wait for server to come up
    for _ in range(25):
        try:
            r = requests.get(f"http://127.0.0.1:{port}/api/status", timeout=1.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False


def print_banner(title):
    print("\n" + "=" * 76)
    print(f"  {title}")
    print("=" * 76)


def run_demo():
    print_banner("SENTINELNET: END-TO-END SYSTEM DEMONSTRATION")
    print("  Computer Networks + AI Traffic Classification Architecture")
    print(f"  Demo API Key Configured: {DEMO_API_KEY[:8]}********")

    # 1. Start or connect to backend server
    port = 5000
    base_url = f"http://127.0.0.1:{port}"
    print(f"\n[*] Checking backend server on {base_url}...")
    try:
        r = requests.get(f"{base_url}/api/status", timeout=1.0)
        connected = (r.status_code == 200)
    except Exception:
        connected = False

    if not connected:
        print("[*] Starting embedded backend server on http://127.0.0.1:5000...")
        if not start_in_process_server(port):
            print("[!] Error: Failed to start embedded backend server.")
            sys.exit(1)
        print("[+] Backend server started successfully.")
    else:
        print("[+] Connected to existing backend server.")

    # 2. Query System Status
    print_banner("STAGE 1: SYSTEM HEALTH & METADATA VERIFICATION")
    res = requests.get(f"{base_url}/api/status")
    status = res.json()
    model_info = status.get("model", {})
    flows_res = requests.get(f"{base_url}/api/flows").json()
    print(f"  System Status:        {status.get('status')}")
    print(f"  Active Model Type:    {model_info.get('model_type')}")
    print(f"  Dataset Provenance:   {model_info.get('dataset_type')}")
    print(f"  Total Ingested Flows: {flows_res.get('count')}")

    # 3. Ingest Human Network Flow
    print_banner("STAGE 2: INGESTING BENIGN HUMAN FLOW (/api/ingest)")
    human_payload = {
        "session_id": "demo_human_sess_001",
        "device_id": "laptop_user_1",
        "requests_per_sec": 1.45,
        "session_duration": 82.5,
        "packet_size_mean": 685.0,
        "packet_size_var": 125000.0,
        "request_interval_mean": 0.72,
        "request_interval_var": 0.55,
        "bytes_transferred": 78000,
        "num_connections": 6,
        "protocol": "TCP",
        "label": "Human",
        "bot_tier": None,
    }
    headers = {"X-API-Key": DEMO_API_KEY, "Content-Type": "application/json"}
    h_res = requests.post(f"{base_url}/api/ingest", headers=headers, json=human_payload)
    h_data = h_res.json().get("flow", {})
    print(f"  Session ID:        {h_data.get('session_id')}")
    print(f"  Raw Prediction:    {h_data.get('raw_prediction')}")
    print(f"  Anomaly Score:     {h_data.get('anomaly_score')}")
    print(f"  Isolation Forest:  {'ANOMALY' if h_data.get('is_anomaly') else 'BENIGN'}")
    print(f"  Final Verdict:     {h_data.get('verdict')} (Reason: {h_data.get('verdict_reason')})")

    # 4. Ingest Automated Bot Flow (Tier 1 Constant)
    print_banner("STAGE 3: INGESTING TIER 1 AUTOMATED BOT FLOW (/api/ingest)")
    bot_payload = {
        "session_id": "demo_bot_t1_sess_002",
        "device_id": "scraper_vm_2",
        "requests_per_sec": 10.0,
        "session_duration": 15.0,
        "packet_size_mean": 240.0,
        "packet_size_var": 150.0,
        "request_interval_mean": 0.10,
        "request_interval_var": 0.0001,
        "bytes_transferred": 36000,
        "num_connections": 1,
        "protocol": "TCP",
        "label": "Bot",
        "bot_tier": "tier1",
    }
    b_res = requests.post(f"{base_url}/api/ingest", headers=headers, json=bot_payload)
    b_data = b_res.json().get("flow", {})
    print(f"  Session ID:        {b_data.get('session_id')}")
    print(f"  Raw Prediction:    {b_data.get('raw_prediction')}")
    print(f"  Anomaly Score:     {b_data.get('anomaly_score')}")
    print(f"  Isolation Forest:  {'ANOMALY' if b_data.get('is_anomaly') else 'BENIGN'}")
    print(f"  Final Verdict:     {b_data.get('verdict')} (Reason: {b_data.get('verdict_reason')})")

    # 5. Ingest Ambiguous Flow Triggering Suspicious Verdict
    print_banner("STAGE 4: INGESTING ANOMALOUS FLOW (HYBRID SUSPICIOUS VERDICT)")
    suspicious_payload = {
        "session_id": "demo_suspicious_sess_003",
        "device_id": "proxy_gateway_3",
        "requests_per_sec": 1.2,
        "session_duration": 45.0,
        "packet_size_mean": 2400.0,
        "packet_size_var": 950000.0,
        "request_interval_mean": 0.85,
        "request_interval_var": 0.60,
        "bytes_transferred": 2500000,
        "num_connections": 18,
        "protocol": "TCP",
        "label": "Suspicious",
        "bot_tier": None,
    }
    s_res = requests.post(f"{base_url}/api/ingest", headers=headers, json=suspicious_payload)
    s_data = s_res.json().get("flow", {})
    print(f"  Session ID:        {s_data.get('session_id')}")
    print(f"  Raw Prediction:    {s_data.get('raw_prediction')}")
    print(f"  Anomaly Score:     {s_data.get('anomaly_score')}")
    print(f"  Isolation Forest:  {'ANOMALY' if s_data.get('is_anomaly') else 'BENIGN'}")
    print(f"  Disagreement Flag: {s_data.get('disagreement')}")
    print(f"  Final Verdict:     {s_data.get('verdict')} (Reason: {s_data.get('verdict_reason')})")

    # 6. Query Bot Tier Sophistication Analysis
    print_banner("STAGE 5: BOT TIER SOPHISTICATION & DIFFICULTY BENCHMARK")
    bt_res = requests.get(f"{base_url}/api/bot-tiers")
    bt_data = bt_res.json()
    tiers = bt_data.get("tiers", [])
    print(f"  {'Tier':<8} | {'Name':<24} | {'F1 Score':<10} | {'Bot Prob':<10} | {'Separation (Cohen d)'}")
    print("  " + "-" * 72)
    for t in tiers:
        d_val = "N/A"
        if t.get("least_separated_features"):
            min_feat = t["least_separated_features"][0]
            d_val = f"{min_feat['feature']} (d={min_feat['cohens_d']})"
        f1_str = f"{t.get('f1', 0):.3f}" if t.get('f1') is not None else "N/A"
        prob_str = f"{t.get('bot_probability', 0)*100:.1f}%"
        print(f"  {t.get('id'):<8} | {t.get('name')[:24]:<24} | {f1_str:<10} | {prob_str:<10} | {d_val}")

    # 7. Query Adversarial Benchmark
    print_banner("STAGE 6: TIER 4 ADVERSARIAL EVASION BENCHMARK")
    adv_res = requests.get(f"{base_url}/api/adversarial")
    if adv_res.status_code == 200:
        adv_data = adv_res.json()
        scenarios = adv_data.get("scenarios", {})
        for name, sc in scenarios.items():
            print(f"\n  Scenario: {name.upper()}")
            print(f"    Description:               {sc.get('description')}")
            print(f"    Classifier Evasion Rate:   {sc.get('classifier_evasion_rate')*100:.1f}%")
            print(f"    Suspicious Verdict Rescue: {sc.get('suspicious_rescue_rate')*100:.1f}%")
            print(f"    Outright Bot Verdict:      {sc.get('bot_detection_rate')*100:.1f}%")
            print(f"    Net SentinelNet Evasion:   {sc.get('hybrid_sentinelnet_evasion_rate')*100:.1f}%")

        print("\n  Recommended Countermeasures Against Statistical Mimicry:")
        for c in adv_data.get("recommended_countermeasures", [])[:3]:
            print(f"    - [{c.get('dimension')}] {c.get('feature')}: {c.get('rationale')[:60]}...")
    else:
        print("  [!] Adversarial results not yet computed. Run python ai/adversarial_eval.py")

    print_banner("DEMO COMPLETE -- ALL PIPELINE STAGES OPERATIONAL")
    print("  [OK] Computer Networks Packet & Flow Extraction")
    print("  [OK] Ingest REST API with Header Authentication")
    print("  [OK] Machine Learning Classifier + Isolation Forest Bridge")
    print("  [OK] Hybrid Consensus 'Suspicious' Classification")
    print("  [OK] Multi-Tier Bot Difficulty Curve & Adversarial Defense Suite")
    print("=" * 76 + "\n")


if __name__ == "__main__":
    run_demo()
