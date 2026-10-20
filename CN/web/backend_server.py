"""
backend_server.py
-----------------
SentinelNet - Minimalist Network Intelligence API Server.

Integrates the existing Computer Networks (CN) flow processor, Scapy packet parser,
and AI classifier bridge with the web dashboard frontend.

Endpoints:
- GET  /api/status          : System, Npcap environment, and AI model health
- GET  /api/overview        : Metric summary, prediction distribution, and recent activity
- GET  /api/flows           : List of all analyzed network flows
- GET  /api/flows/<flow_id> : Detailed view of a single flow
- POST /api/replay/<tier>   : Replay PCAP sample (tier1, tier2, tier3) through the pipeline
- GET  /api/bot-tiers       : Bot tier specifications, expected vs predicted matrix
- GET  /api/architecture   : Architecture component definitions and verification statuses
- POST /api/capture/start   : Start live packet capture (if Npcap + Admin available)
- POST /api/capture/stop    : Stop live packet capture
"""

import os
import sys
import time
import uuid
import json
import threading
from typing import Dict, Any, List

from flask import Flask, jsonify, request, make_response, send_file

# Ensure repository root is on sys.path
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from CN.agent.capture.packet_capture import (
    PacketCapture,
    check_environment,
    DEFAULT_BPF_FILTER,
    get_loopback_interface,
    build_bpf_filter,
    is_windows,
)
from CN.agent.flow.flow_processor import FlowProcessor
from CN.agent.ai_bridge import AIBridge, REQUIRED_FEATURES, NUMERICAL_FEATURES, SUPPORTED_PROTOCOLS

app = Flask(__name__)

# ---------------------------------------------------------------------------
# API Authentication Helper
# ---------------------------------------------------------------------------
def get_configured_api_key() -> str:
    """
    Retrieve configured API key from environment variable, .env, or config.json.
    Falls back to a default demo key if none is explicitly specified.
    """
    key = os.environ.get("SENTINELNET_API_KEY")
    if key and key.strip():
        return key.strip()

    env_file = os.path.join(_REPO_ROOT, ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("SENTINELNET_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
        except Exception:
            pass

    config_file = os.path.join(_REPO_ROOT, "config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                data = json.load(f)
                val = data.get("api_key") or data.get("SENTINELNET_API_KEY")
                if val:
                    return str(val).strip()
        except Exception:
            pass

    return None


# ---------------------------------------------------------------------------
# In-Memory Session Store
# ---------------------------------------------------------------------------
_STORE_LOCK = threading.Lock()
_ANALYZED_FLOWS: List[Dict[str, Any]] = []
_ACTIVE_CAPTURE: Dict[str, Any] = {
    "is_capturing": False,
    "capture_instance": None,
    "processor": None,
    "mode": "PCAP Replay (Offline)",
    "start_time": None,
    "interface": None,
    "filter": None,
}

_BRIDGE = AIBridge()


class _ServerCaptureProcessor(FlowProcessor):
    """Custom FlowProcessor that automatically classifies completed sessions and adds them to _ANALYZED_FLOWS."""
    def save_features(self, features):
        super().save_features(features)
        try:
            pred_result = _BRIDGE.predict(features)
            flow_id = features.get("session_id") or f"flow_live_{int(time.time()*1000)%1000000}"
            flow_record = {
                "flow_id": flow_id,
                "session_id": flow_id,
                "device_id": features.get("device_id", "ServerCapture"),
                "tier": features.get("bot_tier", "Live"),
                "source_type": "Server Live Capture",
                "source_file": "Live Sniffer Interface",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "epoch_time": time.time(),
                "expected_label": features.get("label", "Unknown"),
                "predicted_label": pred_result["prediction"],
                "verdict": pred_result.get("verdict", pred_result["prediction"]),
                "raw_prediction": pred_result.get("raw_prediction", pred_result["prediction"]),
                "disagreement": pred_result.get("disagreement", False),
                "verdict_reason": pred_result.get("verdict_reason", "classifier_consensus"),
                "anomaly_score": pred_result.get("anomaly_score"),
                "is_anomaly": pred_result.get("is_anomaly"),
                "is_match": (pred_result["prediction"].lower() == str(features.get("label", "")).lower()) if features.get("label") and features.get("label") != "Unknown" else None,
                "model_type": pred_result.get("model_type", "LogisticRegression"),
                "probability_estimates": pred_result.get("probability_estimates", {}),
                "features": pred_result.get("features_used", {}),
                "metadata": {
                    **pred_result.get("metadata", {}),
                    "device_id": features.get("device_id", "ServerCapture"),
                    "session_id": flow_id,
                },
                "packet_count": int(features.get("packet_count", 0)),
                "raw_packet_count": int(features.get("packet_count", 0)),
                "session_duration": float(features.get("session_duration", 0.0)),
                "bytes_transferred": int(features.get("bytes_transferred", 0)),
                "protocol": features.get("protocol", "TCP"),
            }
            with _STORE_LOCK:
                _ANALYZED_FLOWS.append(flow_record)
        except Exception as exc:
            print(f"[!] Server live capture classification error: {exc}")



# ---------------------------------------------------------------------------
# CORS Configuration (Zero-dependency middleware)
# ---------------------------------------------------------------------------
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-API-Key"
    return response



# ---------------------------------------------------------------------------
# Helper: Replay & Process PCAP File
# ---------------------------------------------------------------------------
def _process_pcap_tier(tier_id: str, label: str = "Bot") -> Dict[str, Any]:
    """Execute PCAP replay through the existing CN and AI pipeline."""
    pcap_filename = f"{tier_id}_sample.pcap"
    pcap_path = os.path.join(_REPO_ROOT, "CN", "data", pcap_filename)

    # Auto-generate sample PCAP if missing
    if not os.path.exists(pcap_path):
        from CN.demos.generate_sample_pcap import (
            generate_tier1_pcap,
            generate_tier2_pcap,
            generate_tier3_pcap,
        )
        generators = {
            "tier1": generate_tier1_pcap,
            "tier2": generate_tier2_pcap,
            "tier3": generate_tier3_pcap,
        }
        if tier_id in generators:
            generators[tier_id](pcap_path)

    capture = PacketCapture(
        device_id="PC01",
        label=label,
        bot_tier=tier_id,
    )
    capture.replay_pcap(pcap_path)
    latest_features = capture.get_latest_features()
    if not latest_features:
        raise ValueError(f"No features extracted from {pcap_filename}")

    result = _BRIDGE.predict(latest_features)
    flow_id = f"flow_{tier_id}_{int(time.time() * 1000) % 1000000}"

    flow_record = {
        "flow_id": flow_id,
        "session_id": flow_id,
        "device_id": "PC01",
        "tier": tier_id,
        "source_type": "PCAP Replay",
        "source_file": pcap_filename,

        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "epoch_time": time.time(),
        "expected_label": label,
        "predicted_label": result["prediction"],
        "verdict": result.get("verdict", result["prediction"]),
        "raw_prediction": result.get("raw_prediction", result["prediction"]),
        "disagreement": result.get("disagreement", False),
        "verdict_reason": result.get("verdict_reason", "classifier_consensus"),
        "anomaly_score": result.get("anomaly_score"),
        "is_anomaly": result.get("is_anomaly"),
        "is_match": (result["prediction"].lower() == label.lower()),
        "model_type": result.get("model_type", "LogisticRegression"),
        "probability_estimates": result.get("probability_estimates", {}),
        "features": result.get("features_used", {}),
        "metadata": result.get("metadata", {}),
        "packet_count": len(capture.parsed_packets),
        "raw_packet_count": len(capture.raw_packets),
        "session_duration": latest_features.get("session_duration", 0.0),
        "bytes_transferred": latest_features.get("bytes_transferred", 0),
        "protocol": latest_features.get("protocol", "TCP"),
    }
    return flow_record


def _seed_initial_flows():
    """Seed initial PCAP replay data so dashboard is immediately informative."""
    with _STORE_LOCK:
        if not _ANALYZED_FLOWS:
            for t in ["tier1", "tier2", "tier3"]:
                try:
                    record = _process_pcap_tier(t)
                    _ANALYZED_FLOWS.append(record)
                except Exception as exc:
                    print(f"[!] Initial seeding error for {t}: {exc}")


def _get_model_metadata() -> dict:
    """Load model_metadata.json to read training provenance and dataset type."""
    meta_path = os.path.join(_REPO_ROOT, "ai", "models", "model_metadata.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"dataset_type": "synthetic prototype", "dataset_note": "Synthetic prototype baseline"}


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/status", methods=["GET"])
def get_status():
    """Return system environment, Npcap readiness, and AI model status."""
    env = check_environment()
    meta = _get_model_metadata()
    try:
        model = _BRIDGE.load_model()
        model_ready = True
        model_classes = list(_BRIDGE._classes) if _BRIDGE._classes else []
        model_type = _BRIDGE._model_type
    except Exception as exc:
        model_ready = False
        model_classes = []
        model_type = f"Error: {exc}"

    return jsonify({
        "status": "online",
        "service": "SentinelNet Backend Intelligence Server",
        "timestamp": time.time(),
        "environment": env,
        "model": {
            "is_loaded": model_ready,
            "model_type": model_type,
            "dataset_type": meta.get("dataset_type", "synthetic prototype"),
            "dataset_note": meta.get("dataset_note", "Synthetic prototype baseline"),
            "classes": model_classes,
            "contract_features": REQUIRED_FEATURES,
            "numerical_features": NUMERICAL_FEATURES,
            "supported_protocols": list(SUPPORTED_PROTOCOLS),
        },
        "operating_mode": "Live Capture" if _ACTIVE_CAPTURE["is_capturing"] else "PCAP Replay (Offline)",
        "active_capture": {
            "is_capturing": _ACTIVE_CAPTURE["is_capturing"],
            "start_time": _ACTIVE_CAPTURE["start_time"],
            "interface": _ACTIVE_CAPTURE.get("interface"),
            "filter": _ACTIVE_CAPTURE.get("filter"),
            "packets_seen": len(_ACTIVE_CAPTURE["capture_instance"].raw_packets) if _ACTIVE_CAPTURE.get("capture_instance") else 0,
        },
    })


@app.route("/api/overview", methods=["GET"])
def get_overview():
    """Return overview summary cards, traffic distribution, and recent activity."""
    with _STORE_LOCK:
        flows = list(_ANALYZED_FLOWS)

    meta = _get_model_metadata()
    total_flows = len(flows)
    human_count = sum(1 for f in flows if f.get("predicted_label") == "Human")
    bot_count = sum(1 for f in flows if f.get("predicted_label") == "Bot")
    suspicious_count = sum(1 for f in flows if f.get("predicted_label") == "Suspicious")

    # Recent activity: latest 10 flows (reversed)
    recent_activity = sorted(flows, key=lambda x: x.get("epoch_time", 0), reverse=True)[:10]

    return jsonify({
        "total_flows": total_flows,
        "dataset_type": meta.get("dataset_type", "synthetic prototype"),
        "counts": {
            "human": human_count,
            "bot": bot_count,
            "suspicious": suspicious_count,
        },
        "distribution": [
            {"name": "Human", "value": human_count, "color": "#10b981"},
            {"name": "Bot", "value": bot_count, "color": "#f97316"},
            {"name": "Suspicious", "value": suspicious_count, "color": "#ef4444"},
        ],
        "capture_mode": "Live Capture" if _ACTIVE_CAPTURE["is_capturing"] else "PCAP Replay (Offline)",
        "model_type": _BRIDGE._model_type or "LogisticRegression",
        "recent_flows": recent_activity,
    })


@app.route("/api/flows", methods=["GET"])
def get_flows():
    """Return all analyzed flows."""
    with _STORE_LOCK:
        flows = sorted(_ANALYZED_FLOWS, key=lambda x: x.get("epoch_time", 0), reverse=True)
    return jsonify({
        "count": len(flows),
        "flows": flows,
    })


@app.route("/api/flows/<flow_id>", methods=["GET"])
def get_flow_detail(flow_id: str):
    """Return detailed metrics for a single flow."""
    with _STORE_LOCK:
        flow = next((f for f in _ANALYZED_FLOWS if f["flow_id"] == flow_id), None)

    if not flow:
        return jsonify({"error": f"Flow with ID '{flow_id}' not found"}), 404

    return jsonify(flow)


@app.route("/api/replay/<tier>", methods=["POST"])
def replay_tier(tier: str):
    """Replay a specific PCAP tier (tier1, tier2, tier3)."""
    tier = tier.lower()
    if tier not in {"tier1", "tier2", "tier3"}:
        return jsonify({"error": f"Invalid tier '{tier}'. Must be 'tier1', 'tier2', or 'tier3'"}), 400

    try:
        flow_record = _process_pcap_tier(tier, label="Bot")
        with _STORE_LOCK:
            _ANALYZED_FLOWS.append(flow_record)

        return jsonify({
            "message": f"Successfully replayed and classified {tier} PCAP",
            "flow": flow_record,
        })
    except Exception as exc:
        return jsonify({"error": f"Replay execution failed: {str(exc)}"}), 500


@app.route("/api/ingest", methods=["POST", "OPTIONS"])
def ingest_flow():
    """
    Ingest a completed session's extracted features from a remote or local capture agent.

    Authentication:
      Requires 'X-API-Key' matching configured secret key.
    """
    if request.method == "OPTIONS":
        return make_response("", 200)

    # 1. API Key Authentication
    expected_key = get_configured_api_key()
    if not expected_key:
        return jsonify({
            "error": "Server configuration error: SENTINELNET_API_KEY is not configured on server"
        }), 500

    provided_key = request.headers.get("X-API-Key")

    if not provided_key or provided_key != expected_key:
        return jsonify({
            "error": "Unauthorized: Missing or invalid X-API-Key header"
        }), 401

    # 2. Parse JSON Payload
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "error": "Bad Request: JSON object payload required"
        }), 400

    # 3. Extract Session Metadata
    session_id = str(data.get("session_id") or f"sess_{int(time.time() * 1000) % 1000000}")
    device_id = str(data.get("device_id") or "PC01")
    timestamp = data.get("timestamp") or time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    expected_label = data.get("label", "Unknown")
    bot_tier = data.get("bot_tier", "None")

    # 4. Map and adapt features to AI Bridge Contract
    features = dict(data)
    if "requests_per_sec" not in features and "packets_per_sec" in features:
        try:
            features["requests_per_sec"] = float(features["packets_per_sec"])
        except (ValueError, TypeError):
            features["requests_per_sec"] = 0.0

    if "request_interval_mean" not in features and "packet_interval_mean" in features:
        try:
            features["request_interval_mean"] = float(features["packet_interval_mean"])
        except (ValueError, TypeError):
            features["request_interval_mean"] = 0.0

    if "request_interval_var" not in features and "packet_interval_var" in features:
        try:
            features["request_interval_var"] = float(features["packet_interval_var"])
        except (ValueError, TypeError):
            features["request_interval_var"] = 0.0

    if "num_connections" not in features:
        try:
            features["num_connections"] = int(features.get("num_connections", 1))
        except (ValueError, TypeError):
            features["num_connections"] = 1

    # Protocol normalization
    raw_proto = str(features.get("protocol", "TCP")).strip().upper()
    features["protocol"] = raw_proto if raw_proto in SUPPORTED_PROTOCOLS else "TCP"

    # Ensure required numerical fields are numbers
    for num_col in NUMERICAL_FEATURES:
        if num_col in features:
            try:
                features[num_col] = float(features[num_col]) if num_col != "num_connections" else int(features[num_col])
            except (ValueError, TypeError):
                features[num_col] = 0.0

    # 5. Route through AI Bridge
    try:
        prediction_result = _BRIDGE.predict(features)
    except Exception as exc:
        return jsonify({
            "error": f"Classification failed: {str(exc)}"
        }), 400

    predicted_label = prediction_result["prediction"]
    flow_id = session_id if session_id.startswith("flow_") else f"flow_{session_id}"

    flow_record = {
        "flow_id": flow_id,
        "session_id": session_id,
        "device_id": device_id,
        "tier": bot_tier if bot_tier and bot_tier != "None" else "Live",
        "source_type": "Live Agent Ingest",
        "source_file": f"Agent {device_id}",
        "timestamp": timestamp,
        "epoch_time": time.time(),
        "expected_label": expected_label,
        "predicted_label": predicted_label,
        "verdict": prediction_result.get("verdict", predicted_label),
        "raw_prediction": prediction_result.get("raw_prediction", predicted_label),
        "disagreement": prediction_result.get("disagreement", False),
        "verdict_reason": prediction_result.get("verdict_reason", "classifier_consensus"),
        "anomaly_score": prediction_result.get("anomaly_score"),
        "is_anomaly": prediction_result.get("is_anomaly"),
        "is_match": (predicted_label.lower() == expected_label.lower()) if expected_label and expected_label != "Unknown" else None,
        "model_type": prediction_result.get("model_type", "LogisticRegression"),
        "probability_estimates": prediction_result.get("probability_estimates", {}),
        "features": prediction_result.get("features_used", {}),
        "metadata": {
            **prediction_result.get("metadata", {}),
            "device_id": device_id,
            "session_id": session_id,
        },
        "packet_count": int(data.get("packet_count", 0)),
        "raw_packet_count": int(data.get("packet_count", 0)),
        "session_duration": float(features.get("session_duration", 0.0)),
        "bytes_transferred": int(features.get("bytes_transferred", 0)),
        "protocol": features["protocol"],
    }

    # 6. Store in thread-safe memory list & server CSV log
    with _STORE_LOCK:
        _ANALYZED_FLOWS.append(flow_record)

    try:
        from CN.agent.csv_writer import save_to_csv
        server_csv_path = os.path.join(_REPO_ROOT, "server_ingested_dataset.csv")
        save_to_csv(data, filename=server_csv_path)
    except Exception:
        pass

    return jsonify({
        "message": "Session successfully ingested and classified",
        "flow_id": flow_id,
        "device_id": device_id,
        "prediction": predicted_label,
        "probability_estimates": prediction_result.get("probability_estimates", {}),
        "flow": flow_record,
    }), 201


@app.route("/api/bot-tiers", methods=["GET"])
def get_bot_tiers():
    """Return the evaluated bot tier definitions from ai/models/bot_tier_results.json."""
    results_path = os.path.join(_REPO_ROOT, "ai", "models", "bot_tier_results.json")
    if not os.path.exists(results_path):
        return jsonify({
            "error": "Bot tier analysis results not found. Run 'python ai/bot_tier_analysis.py' first.",
            "tiers": [],
            "evaluation_summary": {
                "total_tiers": 0,
                "matches": 0,
                "mismatches": 0,
                "source": "None",
                "limitation_note": "No empirical evaluation found. Please execute ai/bot_tier_analysis.py.",
            },
        }), 404

    try:
        with open(results_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        return jsonify({"error": f"Failed to load bot tier results: {exc}"}), 500

    with _STORE_LOCK:
        flows = list(_ANALYZED_FLOWS)

    # Attach any latest live replay runs if present
    tier_results = {}
    for t in ["tier1", "tier2", "tier3"]:
        matching = [f for f in flows if f.get("tier") == t]
        tier_results[t] = matching[-1] if matching else None

    tiers_data = data.get("tiers", [])
    for tier in tiers_data:
        tier_id = tier.get("id")
        tier["latest_run"] = tier_results.get(tier_id)

    return jsonify({
        "tiers": tiers_data,
        "evaluation_summary": data.get("evaluation_summary", {}),
        "dataset_type": data.get("dataset_type", "unknown"),
        "has_curve_plot": os.path.exists(os.path.join(_REPO_ROOT, "ai", "models", "bot_tier_curve.png")),
    })


@app.route("/api/bot-tiers/curve", methods=["GET"])
def get_bot_tier_curve():
    """Serve the generated F1 difficulty curve plot."""
    curve_path = os.path.join(_REPO_ROOT, "ai", "models", "bot_tier_curve.png")
    if os.path.exists(curve_path):
        return send_file(curve_path, mimetype="image/png")
    return jsonify({"error": "Bot tier curve plot not found. Run ai/bot_tier_analysis.py first."}), 404


@app.route("/api/adversarial", methods=["GET"])
def get_adversarial_results():
    """Return Tier 4 adversarial evaluation benchmark results."""
    adv_path = os.path.join(_REPO_ROOT, "ai", "models", "adversarial_results.json")
    if not os.path.exists(adv_path):
        return jsonify({
            "error": "Adversarial results not found. Run ai/adversarial_eval.py first.",
            "status": "not_run"
        }), 404

    try:
        with open(adv_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as exc:
        return jsonify({"error": f"Failed to load adversarial results: {exc}"}), 500


@app.route("/api/architecture", methods=["GET"])
def get_architecture():
    """Return pipeline stages, component descriptions, and validation status."""
    stages = [
        {
            "stage_number": 1,
            "name": "Traffic Ingestion",
            "domain": "Computer Networks",
            "description": "Captures raw TCP/IP packets or reads binary PCAP capture files via Scapy.",
            "components": ["Scapy sniff()", "Scapy rdpcap()", "BPF filter 'tcp and port 5000'"],
            "status": "Verified (PCAP Replay) / Unverified on Windows (Live Sniffing due to Npcap)",
        },
        {
            "stage_number": 2,
            "name": "Packet Parsing",
            "domain": "Computer Networks",
            "description": "Extracts 12-tuple network metadata (IPs, ports, protocol, packet size, TCP flags, sequence numbers).",
            "components": ["packet_parser.py", "TCP flag bitmask decoder"],
            "status": "Verified (Unit & Integration Tested)",
        },
        {
            "stage_number": 3,
            "name": "Flow & Session Tracking",
            "domain": "Computer Networks",
            "description": "Maintains bidirectional 5-tuple flow state, TCP connection lifecycles, and session duration windows.",
            "components": ["FlowTracker", "SessionTracker", "extract_features"],
            "status": "Verified (Stateful Handshake & Connection Counting Tested)",
        },
        {
            "stage_number": 4,
            "name": "AI Bridge & Preprocessing",
            "domain": "Artificial Intelligence",
            "description": "Validates contract schema, checks numerical boundaries, applies StandardScaler and OneHotEncoder.",
            "components": ["ai_bridge.py", "ColumnTransformer", "StandardScaler", "OneHotEncoder"],
            "status": "Verified (29 Contract Invariant Tests)",
        },
        {
            "stage_number": 5,
            "name": "ML Inference & Classification",
            "domain": "Artificial Intelligence",
            "description": "Calculates multinomial logistic regression decision function and produces calibrated probability estimates.",
            "components": ["final_model.joblib", "LogisticRegression", "Softmax probability distribution"],
            "status": "Verified (Trained Baseline Prototype Model)",
        },
    ]

    return jsonify({
        "stages": stages,
        "domains": {
            "computer_networks": [
                "Raw packet capture and PCAP decoding",
                "TCP handshake, data, teardown state tracking",
                "Bidirectional 5-tuple flow tracking",
                "9-feature statistical extraction",
            ],
            "artificial_intelligence": [
                "Feature scaling and protocol encoding",
                "Logistic regression multinomial classifier",
                "Class probability distribution generation",
                "Domain shift and mimicry evasion analysis",
            ],
        },
    })


@app.route("/api/capture/start", methods=["POST"])
def start_capture():
    """Start real live packet capture on server interface."""
    env = check_environment()
    if not env["pcap_available"]:
        return jsonify({
            "error": "Live capture unavailable: Npcap is not installed or libpcap provider unavailable.",
            "details": env["message"],
            "setup_guide": env["setup_guide"],
        }), 400

    if is_windows() and not env["is_admin"]:
        return jsonify({
            "error": "Live capture unavailable: Server process is not running as Administrator on Windows.",
            "details": env["message"],
            "setup_guide": env["setup_guide"],
        }), 400

    with _STORE_LOCK:
        if _ACTIVE_CAPTURE["is_capturing"]:
            cap = _ACTIVE_CAPTURE.get("capture_instance")
            return jsonify({
                "error": "Live packet capture is already active",
                "status": "running",
                "packets": len(cap.raw_packets) if cap else 0,
            }), 409

        data = request.get_json(silent=True) or {}
        chosen_filter = build_bpf_filter(
            filter_str=data.get("filter"),
            port=data.get("port"),
            all_ip=bool(data.get("all_ip", False)),
        )
        chosen_iface = data.get("interface") or env.get("loopback_iface")
        device_id = str(data.get("device_id") or "ServerCapture")
        label = str(data.get("label") or "Human")
        bot_tier = str(data.get("bot_tier") or "Live")

        proc = _ServerCaptureProcessor(
            device_id=device_id,
            label=label,
            bot_tier=bot_tier,
            write_local_csv=False,
        )
        cap = PacketCapture(
            bpf_filter=chosen_filter,
            interface=chosen_iface,
            processor=proc,
            device_id=device_id,
            label=label,
            bot_tier=bot_tier,
        )

        try:
            cap.start()
        except Exception as exc:
            return jsonify({
                "error": f"Failed to start sniffer on interface '{chosen_iface}': {str(exc)}"
            }), 500

        _ACTIVE_CAPTURE["is_capturing"] = True
        _ACTIVE_CAPTURE["capture_instance"] = cap
        _ACTIVE_CAPTURE["processor"] = proc
        _ACTIVE_CAPTURE["start_time"] = time.time()
        _ACTIVE_CAPTURE["interface"] = chosen_iface
        _ACTIVE_CAPTURE["filter"] = chosen_filter
        _ACTIVE_CAPTURE["mode"] = "Live Capture"

    return jsonify({
        "message": "Live packet capture started successfully",
        "status": "running",
        "interface": chosen_iface,
        "filter": chosen_filter,
    })


@app.route("/api/capture/stop", methods=["POST"])
def stop_capture():
    """Stop live packet capture and flush remaining sessions."""
    with _STORE_LOCK:
        if not _ACTIVE_CAPTURE["is_capturing"] or not _ACTIVE_CAPTURE.get("capture_instance"):
            return jsonify({
                "message": "No active packet capture to stop",
                "status": "stopped",
            }), 200

        cap = _ACTIVE_CAPTURE["capture_instance"]
        proc = _ACTIVE_CAPTURE.get("processor")

        cap.stop()
        if proc:
            try:
                proc.save_all_sessions()
            except Exception as exc:
                print(f"[!] Error flushing sessions on capture stop: {exc}")

        packets_seen = len(cap.raw_packets)
        parsed_seen = len(cap.parsed_packets)

        _ACTIVE_CAPTURE["is_capturing"] = False
        _ACTIVE_CAPTURE["capture_instance"] = None
        _ACTIVE_CAPTURE["processor"] = None
        _ACTIVE_CAPTURE["mode"] = "PCAP Replay (Offline)"

    return jsonify({
        "message": "Live packet capture stopped successfully",
        "status": "stopped",
        "packets_captured": packets_seen,
        "packets_parsed": parsed_seen,
    })


@app.route("/api/capture/status", methods=["GET"])
def get_capture_status():
    """Return real-time sniffer runtime status."""
    with _STORE_LOCK:
        is_cap = _ACTIVE_CAPTURE["is_capturing"]
        cap = _ACTIVE_CAPTURE.get("capture_instance")
        pkts = len(cap.raw_packets) if cap else 0
        parsed = len(cap.parsed_packets) if cap else 0
        start_t = _ACTIVE_CAPTURE.get("start_time")
        duration = (time.time() - start_t) if (is_cap and start_t) else 0.0

    return jsonify({
        "is_capturing": is_cap,
        "status": "running" if is_cap else "stopped",
        "interface": _ACTIVE_CAPTURE.get("interface"),
        "filter": _ACTIVE_CAPTURE.get("filter"),
        "packets_seen": pkts,
        "packets_parsed": parsed,
        "start_time": start_t,
        "duration": round(duration, 2),
    })


# ---------------------------------------------------------------------------
# Server Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    configured_key = get_configured_api_key()
    if not configured_key:
        print("[!] FATAL ERROR: SENTINELNET_API_KEY is not set.", file=sys.stderr)
        print("[!] The server refuses to start without a valid API key configured.", file=sys.stderr)
        print("[!] Please set SENTINELNET_API_KEY in your environment, in a root .env file, or config.json.", file=sys.stderr)
        print("[!] See .env.example for template.", file=sys.stderr)
        sys.exit(1)

    _seed_initial_flows()
    port = 5001
    host = os.environ.get("SENTINELNET_HOST", "0.0.0.0")
    print(f"[*] Starting SentinelNet Web Intelligence API on http://{host}:{port}")
    app.run(host=host, port=port, debug=False)
