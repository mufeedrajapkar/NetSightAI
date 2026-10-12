# AI-CN Integration Contract (V1)

This document defines the data interface between the Computer Networks (CN) module and the AI/ML classification module for SentinelNet.

## Purpose

The AI module is responsible for classifying network sessions as `Human`, `Bot`, or `Suspicious`. The CN module captures raw network traffic and produces session-level statistics. 

This contract specifies exactly what fields the CN module must provide to the AI module for live classification.

## Expected Input Schema

The CN module passes a single record (e.g. JSON object or dictionary) to the AI module containing the following 9 features:

| Field Name | Data Type | Expected Meaning / Description |
|------------|-----------|---------------------------------|
| `requests_per_sec` | Float | Number of requests/packets per second during the session |
| `session_duration` | Float | Total duration of the session in seconds |
| `packet_size_mean` | Float | Average size of packets in the session (bytes) |
| `packet_size_var` | Float | Variance of packet sizes in the session |
| `request_interval_mean` | Float | Average time between consecutive requests/packets (seconds) |
| `request_interval_var` | Float | Variance of request/packet intervals |
| `bytes_transferred` | Integer / Float | Total number of bytes transferred in the session |
| `num_connections` | Integer | Total number of connections made within this session |
| `protocol` | String | Network protocol used (e.g., "TCP", "UDP") |

### Excluded Fields (Do Not Send to Classifier)

The following metadata fields may be present in CN sessions but must **NOT** be passed to the ML classifier for prediction:
* `session_id`: Identifier only, no predictive value.
* `device_id`: Excluded to prevent the model from memorizing specific network nodes.
* `timestamp`: Not used as a raw predictive feature.
* `label`: Ground-truth target only.
* `bot_tier`: Ground-truth difficulty metadata only.

## Expected AI Output

The AI module processes the input record through its preprocessing pipeline, classification model, and unsupervised Isolation Forest anomaly detector. It returns a structured dictionary:

```json
{
    "prediction": "Suspicious",
    "verdict": "Suspicious",
    "raw_prediction": "Human",
    "disagreement": true,
    "verdict_reason": "anomaly_detector_disagreement",
    "anomaly_score": 0.0824,
    "is_anomaly": true,
    "top_probability": 0.6541,
    "confidence_threshold": 0.6,
    "probability_estimates": {
        "Human": 0.6541,
        "Bot": 0.2450,
        "Suspicious": 0.1009
    },
    "model_type": "LogisticRegression",
    "features_used": {
        "requests_per_sec": 4.5,
        "session_duration": 12.0,
        "packet_size_mean": 650.0,
        "packet_size_var": 45000.0,
        "request_interval_mean": 0.22,
        "request_interval_var": 0.015,
        "bytes_transferred": 78000,
        "num_connections": 1,
        "protocol": "TCP"
    },
    "metadata": {
        "session_id": "sess_1001",
        "device_id": "PC01"
    }
}
```

### Runtime "Suspicious" Verdict Determination

The final operational verdict is computed dynamically according to the following deterministic priority rules:
1. **Anomaly Detector Disagreement**: If the classifier's `raw_prediction` is `Human` but the Isolation Forest flags `is_anomaly == True`, the final verdict is escalated to **`Suspicious`** (`verdict_reason: "anomaly_detector_disagreement"`).
2. **Low Classification Confidence**: If the classifier's highest probability score is below the confidence threshold (default `0.6`), the verdict is set to **`Suspicious`** (`verdict_reason: "low_confidence"`).
3. **Classifier Consensus**: Otherwise, the final verdict accepts the classifier's `raw_prediction` (`verdict_reason: "classifier_consensus"`).

Both `raw_prediction` and `verdict` are explicitly returned to allow the dashboard to display disagreements and security escalation alerts.

## Note on Synthetic Data vs Real Data

SentinelNet supports training on both synthetic prototype data and real lab packet captures:
- When trained on synthetic data, metadata is stamped with `"dataset_type": "synthetic prototype"`.
- When trained on real multi-PC lab captures, metadata is stamped with `"dataset_type": "real"`.
All dashboard panels and APIs reflect this provenance.
