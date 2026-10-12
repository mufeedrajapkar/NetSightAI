"""
ai_bridge.py
------------
CN_AI Project — Computer Networks to AI Classification Bridge
-------------------------------------------------------------
Connects the Computer Networks (CN) flow feature extraction output
to the AI Machine Learning classification pipeline.

Contract Reference: ai/CONTRACT.md
Model Artifact:     ai/models/final_model.joblib
Metadata:           ai/models/model_metadata.json

Semantic note — contract feature naming vs. CN measurements:
  The AI contract uses 'requests_per_sec', 'request_interval_mean', and
  'request_interval_var' as feature names. In the physical CN flow context
  these represent network packet transmission rate and inter-packet arrival
  intervals, not application-layer HTTP request counts.  The names are
  preserved unchanged so that the CN output is compatible with the existing
  model pipeline without re-training.  This mismatch is documented here and
  in ai/CONTRACT.md and must be considered when interpreting model outputs.

  'packet_count' is a raw packet counter maintained by the CN module and is
  distinct from 'num_connections'.  It is never passed to the model.
"""

import os
import joblib
import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

_THIS_FILE = os.path.abspath(__file__)
# CN/agent/ai_bridge.py  →  CN/agent  →  CN  →  repo root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_THIS_FILE)))
DEFAULT_MODEL_PATH = os.path.join(BASE_DIR, "ai", "models", "final_model.joblib")
DEFAULT_IF_PATH = os.path.join(BASE_DIR, "ai", "models", "isolation_forest.joblib")


# ---------------------------------------------------------------------------
# Contract constants
# ---------------------------------------------------------------------------

# Ordered list of the 9 features the ML pipeline expects.
# The DataFrame column order must match this list exactly.
REQUIRED_FEATURES = [
    "requests_per_sec",
    "session_duration",
    "packet_size_mean",
    "packet_size_var",
    "request_interval_mean",
    "request_interval_var",
    "bytes_transferred",
    "num_connections",
    "protocol",
]

# Subset that must be finite, non-negative numbers.
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

# Protocols accepted by the trained OHE preprocessor.
# Derived from: model.named_steps['preprocessor'].transformers_[1][1].categories_
# Update this set if the model is retrained with additional protocol values.
SUPPORTED_PROTOCOLS = {"TCP", "UDP"}

# Fields that originate from the CN module but are not model features.
# Only fields *actually present* in the incoming dict are forwarded to metadata.
# (We never invent values that were not supplied.)
_KNOWN_METADATA_FIELDS = {
    "session_id",
    "device_id",
    "packet_count",
    "label",
    "bot_tier",
    "packets_per_sec",
    "packet_interval_mean",
    "packet_interval_var",
}

# All contract feature names, as a set, for fast membership checks.
_REQUIRED_FEATURES_SET = set(REQUIRED_FEATURES)


# ---------------------------------------------------------------------------
# AIBridge class
# ---------------------------------------------------------------------------

class AIBridge:
    """
    Bridge between CN flow feature dictionaries and the AI classifier pipeline.

    The model pipeline is loaded lazily on first use and then cached for the
    lifetime of this object so repeated calls do not re-read the file.
    """
    model_path: str = DEFAULT_MODEL_PATH
    if_path: str = DEFAULT_IF_PATH
    confidence_threshold: float = 0.6
    _model = None
    _classes: list = None
    _model_type: str = None
    _if_model = None
    _if_loaded: bool = False

    def __init__(self, model_path: str = None, if_path: str = None, confidence_threshold: float = 0.6):
        self.model_path: str = model_path or DEFAULT_MODEL_PATH
        self.if_path: str = if_path or DEFAULT_IF_PATH
        self.confidence_threshold: float = confidence_threshold
        self._model = None          # cached scikit-learn Pipeline
        self._classes: list = None  # list of class-label strings, from model.classes_
        self._model_type: str = None
        self._if_model = None       # cached Isolation Forest pipeline
        self._if_loaded: bool = False

    def load_isolation_forest(self):
        """
        Load Isolation Forest pipeline lazily.
        If file is missing or unreadable, returns None without raising.
        """
        if getattr(self, "_if_loaded", False):
            return getattr(self, "_if_model", None)

        target_path = getattr(self, "if_path", DEFAULT_IF_PATH)
        if os.path.exists(target_path):
            try:
                self._if_model = joblib.load(target_path)
            except Exception as exc:
                print(f"[!] Warning: Failed to load Isolation Forest from {target_path}: {exc}")
                self._if_model = None
        else:
            self._if_model = None

        self._if_loaded = True
        return self._if_model

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def load_model(self):
        """
        Load the saved scikit-learn pipeline from disk.

        The result is cached; subsequent calls return the cached object without
        reading the file again.

        Raises:
            FileNotFoundError: If the model artifact does not exist.
            RuntimeError: If the file cannot be deserialised or if the loaded
                object does not expose the expected interface.
        """
        if self._model is not None:
            return self._model

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"AI model artifact not found at: {self.model_path}. "
                "Run ai/train_models.py to create it."
            )

        try:
            loaded = joblib.load(self.model_path)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to deserialise the AI model from {self.model_path}: {exc}"
            ) from exc

        # Verify the required interface is present.
        if not hasattr(loaded, "predict"):
            raise RuntimeError(
                "Loaded object does not have a predict() method. "
                "Expected a scikit-learn estimator or Pipeline."
            )
        if not hasattr(loaded, "predict_proba"):
            raise RuntimeError(
                "Loaded model does not support probability estimates "
                "(predict_proba is not available). "
                "Re-train with probability=True or use a model that supports it."
            )
        if not hasattr(loaded, "classes_"):
            raise RuntimeError(
                "Loaded model does not expose classes_. "
                "Cannot map probability estimates to class labels."
            )

        self._model = loaded
        self._classes = list(loaded.classes_)

        # Resolve a human-readable model type name for reporting.
        if hasattr(loaded, "named_steps") and "classifier" in loaded.named_steps:
            self._model_type = type(loaded.named_steps["classifier"]).__name__
        else:
            self._model_type = type(loaded).__name__

        return self._model

    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------

    def validate_features(self, feature_dict: dict) -> dict:
        """
        Validate and extract the 9 model input features from *feature_dict*.

        Only the contract fields are included in the returned dictionary.
        Metadata and CN alias fields are intentionally excluded here; the
        caller (predict()) handles them separately.

        Returns:
            dict: Exactly the 9 contract features, ready for DataFrame creation.

        Raises:
            TypeError:  If feature_dict is not a dict.
            ValueError: If any required field is absent, has an invalid type,
                        is NaN/infinite, is negative, or uses an unsupported
                        protocol value.
        """
        if not isinstance(feature_dict, dict):
            raise TypeError(
                f"feature_dict must be a dict; got {type(feature_dict).__name__}."
            )

        # --- 1. Check presence of all 9 required features ---------------
        missing = [f for f in REQUIRED_FEATURES if f not in feature_dict or feature_dict[f] is None]
        if missing:
            raise ValueError(
                f"Missing required AI contract feature(s): {missing}. "
                f"All 9 required features must be present: {REQUIRED_FEATURES}"
            )

        # --- 2. Validate numerical fields --------------------------------
        clean: dict = {}
        for field in REQUIRED_FEATURES:
            clean[field] = feature_dict[field]

        for field in NUMERICAL_FEATURES:
            val = clean[field]

            # Type check (numpy scalars are also acceptable)
            if not isinstance(val, (int, float, np.number)):
                raise ValueError(
                    f"Invalid type for '{field}': expected a numeric value, "
                    f"got {type(val).__name__!r} with value {val!r}."
                )

            # Reject NaN and infinity
            try:
                is_nan = np.isnan(val)
                is_inf = np.isinf(val)
            except (TypeError, ValueError):
                is_nan = is_inf = False

            if is_nan:
                raise ValueError(
                    f"'{field}' is NaN. All numerical features must be finite."
                )
            if is_inf:
                raise ValueError(
                    f"'{field}' is infinite. All numerical features must be finite."
                )

            # Reject negative traffic metrics
            if val < 0:
                raise ValueError(
                    f"'{field}' is negative ({val!r}). "
                    "Physical network traffic features cannot be negative."
                )

        # --- 3. Validate protocol ----------------------------------------
        raw_protocol = clean["protocol"]
        if not isinstance(raw_protocol, str) or not raw_protocol.strip():
            raise ValueError(
                f"'protocol' must be a non-empty string; got {raw_protocol!r}."
            )
        normalised_protocol = raw_protocol.strip().upper()
        if normalised_protocol not in SUPPORTED_PROTOCOLS:
            raise ValueError(
                f"Unsupported protocol: {raw_protocol!r}. "
                f"Supported values are: {sorted(SUPPORTED_PROTOCOLS)}. "
                "The trained model was fitted only on these protocol values."
            )
        clean["protocol"] = normalised_protocol

        return clean

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, feature_dict: dict) -> dict:
        """
        Classify one network flow / session.

        Args:
            feature_dict: Dictionary produced by CN ``extract_features()`` /
                ``FlowProcessor.process_packet()``.  Must contain the 9 contract
                features.  Any additional CN fields (e.g. ``session_id``,
                ``packet_count``) are passed through in the ``metadata`` key of
                the result but are never passed to the model.

        Returns:
            dict with keys:
              - ``prediction``          : str, one of the model's class labels
              - ``probability_estimates``: dict mapping each class label to its
                                          estimated probability (sums to ~1.0)
              - ``model_type``          : str, name of the classifier algorithm
              - ``features_used``       : dict of the exact 9 features used
              - ``metadata``            : dict of CN fields that were present in
                                          the input but are not model features;
                                          only fields actually supplied are included

        Raises:
            TypeError, ValueError: From validate_features() if input is invalid.
            FileNotFoundError, RuntimeError: If the model cannot be loaded.
            RuntimeError: If inference fails.
        """
        model = self.load_model()
        clean_features = self.validate_features(feature_dict)

        # Build one-row DataFrame with columns in the exact required order.
        input_df = pd.DataFrame([clean_features])[REQUIRED_FEATURES]

        # Run inference.
        try:
            raw_prediction = model.predict(input_df)[0]
            raw_probabilities = model.predict_proba(input_df)[0]
        except Exception as exc:
            raise RuntimeError(f"Inference failed: {exc}") from exc

        prediction = str(raw_prediction)

        # Map probabilities to class names using the model's actual classes_ order.
        probability_estimates = {
            str(cls): round(float(prob), 6)
            for cls, prob in zip(self._classes, raw_probabilities)
        }

        # Score with Isolation Forest lazily (if available)
        if_model = self.load_isolation_forest()
        anomaly_score = None
        is_anomaly = None
        if if_model is not None:
            try:
                # Invert decision_function so higher positive values represent higher anomaly
                raw_decision = float(if_model.decision_function(input_df)[0])
                anomaly_score = round(float(-raw_decision), 4)
                if_pred = if_model.predict(input_df)[0]
                is_anomaly = bool(if_pred == -1)
            except Exception as exc:
                print(f"[!] Warning: Anomaly scoring failed: {exc}")

        # Compute runtime Suspicious verdict
        # Rule (a): Classifier says Human but Isolation Forest flags anomaly -> Suspicious
        # Rule (b): Top probability < confidence_threshold -> Suspicious
        top_prob = max(probability_estimates.values()) if probability_estimates else 0.0

        if raw_prediction == "Human" and is_anomaly is True:
            verdict = "Suspicious"
            verdict_reason = "anomaly_detector_disagreement"
        elif top_prob < self.confidence_threshold:
            verdict = "Suspicious"
            verdict_reason = f"low_confidence ({top_prob:.3f} < {self.confidence_threshold})"
        else:
            verdict = str(raw_prediction)
            verdict_reason = "classifier_consensus"

        disagreement = (str(raw_prediction) != verdict)

        # Collect only metadata fields that were actually supplied by CN.
        # We never invent fields that are not in the input.
        metadata = {
            key: feature_dict[key]
            for key in feature_dict
            if key not in _REQUIRED_FEATURES_SET
        }

        return {
            "prediction": verdict,
            "verdict": verdict,
            "raw_prediction": str(raw_prediction),
            "disagreement": disagreement,
            "verdict_reason": verdict_reason,
            "anomaly_score": anomaly_score,
            "is_anomaly": is_anomaly,
            "top_probability": round(float(top_prob), 6),
            "confidence_threshold": self.confidence_threshold,
            "probability_estimates": probability_estimates,
            "model_type": self._model_type,
            "features_used": clean_features,
            "metadata": metadata,
        }


# ---------------------------------------------------------------------------
# Module-level convenience helpers
# ---------------------------------------------------------------------------

_default_bridge: AIBridge = None


def get_bridge(model_path: str = None) -> AIBridge:
    """
    Return a module-level singleton AIBridge instance.

    A new instance is created only when model_path differs from the cached one.
    """
    global _default_bridge
    if _default_bridge is None or (
        model_path is not None and _default_bridge.model_path != model_path
    ):
        _default_bridge = AIBridge(model_path=model_path)
    return _default_bridge


def classify_flow(feature_dict: dict, model_path: str = None) -> dict:
    """Convenience wrapper: classify a single flow using the default bridge."""
    return get_bridge(model_path=model_path).predict(feature_dict)
