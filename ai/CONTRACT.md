# AI-CN Integration Contract (V1)

This document defines the data interface between the future Computer Networks (CN) module and the current AI/ML classification module for the CN_AI project.

## Purpose

The AI module is responsible for classifying network sessions as `Human`, `Bot`, or `Suspicious`. The CN module will be responsible for capturing raw network traffic and producing session-level statistics. 

This contract specifies exactly what fields the CN module must provide to the AI module for live classification.

## Expected Input Schema

The CN module must pass a single record (e.g. JSON object or dictionary) to the AI module containing the following 9 fields:

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

The following fields are present in the synthetic dataset but must **NOT** be passed to the live ML model for prediction:
* `session_id`: Identifier only, no predictive value.
* `device_id`: Excluded to prevent the model from memorizing specific devices.
* `timestamp`: Not used as a raw predictive feature.
* `label`: This is the target that the AI predicts.
* `bot_tier`: Ground-truth metadata only.

## Expected AI Output

The AI module will process the input record through its preprocessing pipeline and classification model. It will conceptually return an output in the following format:

```json
{
    "prediction": "Bot", 
    "probabilities": {
        "Bot": 0.9869,
        "Human": 0.0110,
        "Suspicious": 0.0021
    }
}
```

* **`prediction`**: String. One of `["Human", "Bot", "Suspicious"]`.
* **`probabilities`**: Dictionary mapping classes to confidence scores. Note: The meaning and calibration of these scores depends on the underlying model (e.g., Logistic Regression outputs calibrated probabilities).

## Note on Synthetic Data

The current iteration of the AI module (V1) is trained on a **SYNTHETIC PROTOTYPE DATASET**. The performance metrics and patterns learned reflect this synthetic data and should be considered a prototype/baseline. Do not interpret current performance as indicative of real-world network traffic classification accuracy.
