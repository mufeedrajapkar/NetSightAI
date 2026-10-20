# AI Module Documentation

This document is the handoff/documentation guide for the AI/ML classifier developed in CN_AI.

The purpose is to allow other team members working on the Computer Networks module and bot-AI module to understand what the AI classifier does, how it was built, what its inputs are, what its outputs are, and how they should integrate with it.

## 1. PROJECT OVERVIEW

The AI module analyzes network-session metadata and classifies sessions into:
- Human
- Bot
- Suspicious

The AI module receives behavioral/network-session features produced by the CN side and uses supervised machine learning to classify the session.

The AI module does NOT capture packets itself.

## 2. DATASET

Dataset: `data/raw/sentinelnet_sample_500.csv`

This is a SYNTHETIC PROTOTYPE DATASET.

It contains:
- 500 rows
- Human: 200
- Bot: 200
- Suspicious: 100

These results are prototype/baseline results and must not be interpreted as real-world network traffic performance.

## 3. FEATURES USED BY THE CLASSIFIER

The classifier uses exactly 9 features:

1. `requests_per_sec`: Number of requests per second.
2. `session_duration`: Total duration of the session.
3. `packet_size_mean`: Average size of packets in the session.
4. `packet_size_var`: Variance in packet sizes.
5. `request_interval_mean`: Average time interval between requests.
6. `request_interval_var`: Variance in request intervals.
7. `bytes_transferred`: Total bytes transferred during the session.
8. `num_connections`: Number of connections made.
9. `protocol`: Network protocol used.

## 4. FEATURES EXCLUDED

The following features were excluded from the model:

- `session_id`: This is an identifier and holds no predictive value.
- `device_id`: Excluded to avoid device-specific memorization by the model.
- `timestamp`: The raw timestamp is not used in the first iteration.
- `label`: This is the target variable to be predicted.
- `bot_tier`: This is not available to a normal live classifier and would cause data leakage if included.

## 5. PREPROCESSING PIPELINE

The preprocessing pipeline is structured as follows:

ColumnTransformer
        ↓
Numerical features → StandardScaler
Protocol → OneHotEncoder
        ↓
ML classifier

Preprocessing is contained inside the saved Pipeline and is fitted only on training data. 
The categorical encoding uses `OneHotEncoder(drop='first')`, meaning that the encoded `protocol` feature includes `protocol_UDP`.

## 6. TRAINING STRATEGY

- 80/20 train/test split
- stratification
- `random_state=42`
- test set untouched until final evaluation

Cross-validation:
- StratifiedKFold
- 5 folds
- `shuffle=True`
- `random_state=42`

Primary model-selection metric:
- `f1_macro`

## 7. MODELS

The three models tested were:
1. Logistic Regression
2. Random Forest
3. Support Vector Machine (SVM)

The purpose was model comparison rather than assuming a particular algorithm would win.
`GridSearchCV` was used for hyperparameter tuning.

## 8. ACTUAL RESULTS

Verified results for the tested models:

**Logistic Regression**
- Accuracy: 0.91
- Precision: 0.8988
- Recall: 0.925
- Macro F1: 0.9069
- CV F1: 0.8866

**SVM**
- Accuracy: 0.89
- Precision: 0.8787
- Recall: 0.900
- Macro F1: 0.8861
- CV F1: 0.8800

**Random Forest**
- Accuracy: 0.87
- Precision: 0.8537
- Recall: 0.875
- Macro F1: 0.8585
- CV F1: 0.8714

Logistic Regression was selected because it achieved the highest macro F1 in the actual experiment. This conclusion applies to the current synthetic prototype dataset and experiment, and should not be considered the "best model for real-world traffic."

## 9. FINAL MODEL

Path: `ai/models/final_model.joblib`

The saved object is a self-contained Pipeline containing:
- preprocessing
- final Logistic Regression classifier

It can accept a raw 9-feature session record without requiring a separately loaded preprocessing object.

## 10. SINGLE-SESSION INFERENCE

The file `ai/test_prediction.py` provides a standalone test of the saved model.

**Input:** 9 raw session features
**Output:**
- predicted class
- probability distribution

The model currently supports `predict()` and `predict_proba()`. Note that the probability distribution represents the model probability output, not a generic confidence measure.

## 11. SHAP EXPLAINABILITY

The file `ai/explainability.py` is used to explain why an individual session was classified as Human, Bot, or Suspicious.

For the final Logistic Regression model, a `LinearExplainer` is used. The preprocessing transformation is handled before SHAP analysis. The explanation identifies influential features.

Currently observed important features:
- `packet_size_var`
- `num_connections`
- `requests_per_sec`
- `packet_size_mean`
- `request_interval_var`

These are observations from the current synthetic prototype model, not universal network-traffic rules.

## 12. AI-CN INTEGRATION

The future CN module must provide these 9 fields:
- `requests_per_sec`
- `session_duration`
- `packet_size_mean`
- `packet_size_var`
- `request_interval_mean`
- `request_interval_var`
- `bytes_transferred`
- `num_connections`
- `protocol`

Refer to `ai/CONTRACT.md` for the formal integration contract.

**Intended flow:**
CN network/session processing
        ↓
9 session features
        ↓
AI classifier
        ↓
Human / Bot / Suspicious
        ↓
SHAP explanation

## 13. ANOMALY DETECTION & HYBRID VERDICT PIPELINE

In addition to supervised classification, SentinelNet includes an unsupervised **Isolation Forest** pipeline:
- **Baseline Training**: Fitted strictly on benign `Human` sessions with a 5% contamination factor (`ai/models/isolation_forest.joblib`).
- **Hybrid Decision Engine**: If the supervised classifier outputs `Human` but the Isolation Forest flags an anomaly (`is_anomaly == True`), the final verdict is escalated to `Suspicious` (`verdict_reason: "anomaly_detector_disagreement"`).
- **Confidence Guardrail**: If classifier top probability is `< 0.6`, the verdict is routed to `Suspicious` (`verdict_reason: "low_confidence"`).

## 14. WHAT THE AI MODULE DOES NOT DO

The AI module does NOT:
- perform MITM or SSL decryption
- inspect encrypted application payloads (L7 body contents)
- contain Data Warehousing & Mining (DWM) components

## 15. FILE GUIDE

- `ai/train_models.py` → training, preprocessing, CV, GridSearchCV, model comparison, parameterized `--data` retraining
- `ai/build_dataset.py` → dataset aggregator and schema validator across multi-PC captures
- `ai/anomaly_detection.py` → Isolation Forest anomaly detector trained on benign Human baseline
- `ai/bot_tier_analysis.py` → empirical per-tier F1, recall, precision, and Cohen's d feature separation analysis
- `ai/adversarial_eval.py` → Tier 4 delay and packet-shaping adversarial evasion benchmark
- `ai/evaluate.py` → evaluation, metrics, confusion matrices, inference testing
- `ai/explainability.py` → SHAP explanations
- `ai/test_prediction.py` → standalone single-session inference test
- `ai/CONTRACT.md` → formal CN → AI input contract with hybrid verdict rules
- `ai/models/final_model.joblib` → trained final classification pipeline
- `ai/models/isolation_forest.joblib` → trained Isolation Forest anomaly detection artifact
- `ai/models/bot_tier_results.json` → empirical tier benchmark results and metrics
- `ai/models/adversarial_results.json` → adversarial evasion rates and countermeasures
- `ai/models/bot_tier_curve.png` → generated F1 difficulty curve plot
- `ai/models/model_metadata.json` → model and experiment provenance metadata
- `notebooks/01_data_exploration.ipynb` → dataset exploration and EDA

## 16. CURRENT STATUS

**AI MODULE + CN INTEGRATION = VERIFIED & FULLY OPERATIONAL**

Verified:
- No data leakage; strict column validation
- Reproducible training/evaluation on synthetic baseline and real PCAP captures
- Isolation Forest anomaly detection operational
- Dynamic Suspicious verdict escalation operational
- Empirical Bot Tier difficulty curve generated and exposed
- Tier 4 Adversarial evasion suite benchmarked
- Single-session and batch inference through `AIBridge` verified with 102 automated tests
