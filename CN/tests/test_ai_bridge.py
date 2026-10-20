"""
test_ai_bridge.py
-----------------
CN_AI — Integration tests for CN/agent/ai_bridge.py.

Covers:
  - Valid TCP flow through FlowProcessor → AIBridge
  - Valid UDP flow through FlowProcessor → AIBridge
  - Missing required feature
  - Invalid (non-numeric) feature value
  - Negative numeric feature value
  - Infinity feature value
  - Unsupported protocol
  - Prediction contains a class and probability_estimates
  - Probability labels map to the model's actual class order
  - Metadata is preserved but never passed into the model
  - Model is loaded once and reused (caching)
  - Mocked model tests for deterministic validation
  - At least one test uses the actual saved model artifact
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from CN.agent.ai_bridge import (
    AIBridge,
    classify_flow,
    get_bridge,
    REQUIRED_FEATURES,
    SUPPORTED_PROTOCOLS,
    _REQUIRED_FEATURES_SET,
)
from CN.agent.flow.flow_processor import FlowProcessor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_valid_features(**overrides) -> dict:
    """Return a minimal valid 9-feature dict; keyword args override defaults."""
    base = {
        "requests_per_sec": 3.0,
        "session_duration": 10.0,
        "packet_size_mean": 500.0,
        "packet_size_var": 12000.0,
        "request_interval_mean": 0.33,
        "request_interval_var": 0.01,
        "bytes_transferred": 5000,
        "num_connections": 1,
        "protocol": "TCP",
    }
    base.update(overrides)
    return base


def _make_mock_model(classes=("Bot", "Human", "Suspicious"), probabilities=(0.9, 0.07, 0.03)):
    """Build a mock scikit-learn pipeline that returns deterministic outputs."""
    mock = MagicMock()
    mock.classes_ = np.array(classes)
    mock.predict.return_value = np.array([classes[0]])
    mock.predict_proba.return_value = np.array([probabilities])
    mock.named_steps = {"classifier": MagicMock(__class__=type("MockClassifier", (), {}))}
    return mock


def _bridge_with_mock_model(classes=("Bot", "Human", "Suspicious"),
                             probabilities=(0.9, 0.07, 0.03)) -> AIBridge:
    """Return an AIBridge with the model pre-loaded as a mock (no disk I/O)."""
    bridge = AIBridge.__new__(AIBridge)
    bridge.model_path = "/mock/path/model.joblib"
    bridge._model = _make_mock_model(classes, probabilities)
    bridge._classes = list(classes)
    bridge._model_type = "MockClassifier"
    return bridge


# ---------------------------------------------------------------------------
# 1. Model caching
# ---------------------------------------------------------------------------

class TestModelCaching:
    def test_model_loaded_once_and_reused(self):
        """get_bridge() returns the same instance; load_model() caches the object."""
        bridge_a = get_bridge()
        bridge_b = get_bridge()
        assert bridge_a is bridge_b, "get_bridge() must return the same singleton"

        model_first = bridge_a.load_model()
        model_second = bridge_a.load_model()
        assert model_first is model_second, "load_model() must return the cached object"

    def test_classes_and_model_type_populated_after_load(self):
        """After loading, _classes and _model_type are set from the real model."""
        bridge = get_bridge()
        bridge.load_model()
        assert bridge._classes is not None
        assert len(bridge._classes) == 3
        assert set(bridge._classes) == {"Bot", "Human", "Suspicious"}
        assert bridge._model_type is not None


# ---------------------------------------------------------------------------
# 2. Valid flows — using actual saved model
# ---------------------------------------------------------------------------

class TestValidFlowsWithRealModel:
    """These tests exercise the full stack including the real final_model.joblib."""

    def _run_processor(self, packets, device_id="PC01", label="Human", bot_tier="None"):
        processor = FlowProcessor(device_id=device_id, label=label, bot_tier=bot_tier)
        last = None
        for p in packets:
            last = processor.process_packet(p)
        return last

    def test_valid_tcp_flow(self):
        """
        A TCP flow through FlowProcessor must be classifiable via AIBridge.
        The result must contain a valid prediction, probability estimates that
        sum to ~1.0, correctly separated metadata, and exactly 9 features_used.
        """
        packets = [
            {"time": 100.0, "src_ip": "192.168.1.10", "dst_ip": "93.184.216.34",
             "src_port": 55100, "dst_port": 80, "protocol": "TCP", "packet_size": 64,
             "is_syn": True, "is_ack": False, "seq": 1000},
            {"time": 100.05, "src_ip": "93.184.216.34", "dst_ip": "192.168.1.10",
             "src_port": 80, "dst_port": 55100, "protocol": "TCP", "packet_size": 64,
             "is_syn": True, "is_ack": True, "seq": 5000},
            {"time": 100.06, "src_ip": "192.168.1.10", "dst_ip": "93.184.216.34",
             "src_port": 55100, "dst_port": 80, "protocol": "TCP", "packet_size": 54,
             "is_syn": False, "is_ack": True, "seq": 1001},
            {"time": 100.30, "src_ip": "192.168.1.10", "dst_ip": "93.184.216.34",
             "src_port": 55100, "dst_port": 80, "protocol": "TCP", "packet_size": 980,
             "is_syn": False, "is_ack": True, "seq": 1001},
            {"time": 100.60, "src_ip": "93.184.216.34", "dst_ip": "192.168.1.10",
             "src_port": 80, "dst_port": 55100, "protocol": "TCP", "packet_size": 1400,
             "is_syn": False, "is_ack": True, "seq": 5001},
        ]
        features = self._run_processor(packets, device_id="PC01", label="Human")

        bridge = AIBridge()
        result = bridge.predict(features)

        # Prediction shape
        assert "prediction" in result
        assert result["prediction"] in {"Human", "Bot", "Suspicious"}

        # Probability estimates
        estimates = result["probability_estimates"]
        assert isinstance(estimates, dict)
        assert set(estimates.keys()) == {"Bot", "Human", "Suspicious"}
        assert abs(sum(estimates.values()) - 1.0) < 1e-2

        # features_used: exactly the 9 contract fields, in order
        assert list(result["features_used"].keys()) == REQUIRED_FEATURES
        assert result["features_used"]["protocol"] == "TCP"
        assert result["features_used"]["num_connections"] == 1

        # Metadata preserved and not in features_used
        assert "session_id" in result["metadata"]
        assert result["metadata"]["session_id"] == "PC01_S1"
        assert "device_id" in result["metadata"]
        assert result["metadata"]["device_id"] == "PC01"
        assert "packet_count" in result["metadata"]
        assert result["metadata"]["packet_count"] == 5
        assert "label" in result["metadata"]

        for key in result["metadata"]:
            assert key not in _REQUIRED_FEATURES_SET, (
                f"Metadata key '{key}' must not be a contract feature."
            )

    def test_valid_udp_flow(self):
        """A UDP flow must also produce a valid structured result."""
        packets = [
            {"time": 200.0, "src_ip": "192.168.1.20", "dst_ip": "8.8.8.8",
             "src_port": 61234, "dst_port": 53, "protocol": "UDP", "packet_size": 85},
            {"time": 200.06, "src_ip": "8.8.8.8", "dst_ip": "192.168.1.20",
             "src_port": 53, "dst_port": 61234, "protocol": "UDP", "packet_size": 180},
        ]
        features = self._run_processor(
            packets, device_id="PC02", label="Bot", bot_tier="Tier1"
        )

        result = classify_flow(features)

        assert result["prediction"] in {"Human", "Bot", "Suspicious"}
        assert result["features_used"]["protocol"] == "UDP"
        assert result["features_used"]["num_connections"] == 1
        assert result["metadata"].get("device_id") == "PC02"
        assert result["metadata"].get("bot_tier") == "Tier1"


# ---------------------------------------------------------------------------
# 3. validate_features — deterministic tests using mocked model
# ---------------------------------------------------------------------------

class TestValidateFeatures:
    """
    Validation tests use a mocked model so results are independent of the
    actual model artifact and always fast.
    """

    def setup_method(self):
        self.bridge = _bridge_with_mock_model()

    # --- Missing features -----------------------------------------------

    def test_missing_single_required_feature(self):
        feats = _minimal_valid_features()
        del feats["request_interval_mean"]
        with pytest.raises(ValueError) as exc:
            self.bridge.predict(feats)
        assert "request_interval_mean" in str(exc.value)
        assert "Missing required" in str(exc.value)

    def test_missing_multiple_required_features(self):
        feats = _minimal_valid_features()
        del feats["session_duration"]
        del feats["bytes_transferred"]
        with pytest.raises(ValueError) as exc:
            self.bridge.predict(feats)
        msg = str(exc.value)
        assert "session_duration" in msg
        assert "bytes_transferred" in msg

    def test_feature_present_but_none_counts_as_missing(self):
        feats = _minimal_valid_features(num_connections=None)
        with pytest.raises(ValueError) as exc:
            self.bridge.predict(feats)
        assert "num_connections" in str(exc.value)

    # --- Invalid numeric values -----------------------------------------

    def test_non_numeric_feature_raises(self):
        feats = _minimal_valid_features(requests_per_sec="fast")
        with pytest.raises(ValueError) as exc:
            self.bridge.predict(feats)
        msg = str(exc.value)
        assert "requests_per_sec" in msg

    def test_nan_raises(self):
        feats = _minimal_valid_features(packet_size_mean=float("nan"))
        with pytest.raises(ValueError) as exc:
            self.bridge.predict(feats)
        assert "NaN" in str(exc.value)
        assert "packet_size_mean" in str(exc.value)

    def test_positive_infinity_raises(self):
        feats = _minimal_valid_features(bytes_transferred=float("inf"))
        with pytest.raises(ValueError) as exc:
            self.bridge.predict(feats)
        assert "infinite" in str(exc.value)
        assert "bytes_transferred" in str(exc.value)

    def test_negative_infinity_raises(self):
        feats = _minimal_valid_features(session_duration=float("-inf"))
        with pytest.raises(ValueError) as exc:
            self.bridge.predict(feats)
        # Negative inf is both negative and infinite; either message is acceptable.
        msg = str(exc.value)
        assert "session_duration" in msg

    def test_negative_value_raises(self):
        feats = _minimal_valid_features(session_duration=-5.0)
        with pytest.raises(ValueError) as exc:
            self.bridge.predict(feats)
        assert "negative" in str(exc.value).lower()
        assert "session_duration" in str(exc.value)

    def test_zero_is_valid(self):
        """Zero is a valid non-negative value for all numerical features."""
        feats = _minimal_valid_features(
            requests_per_sec=0.0,
            session_duration=0.0,
            packet_size_mean=0.0,
            packet_size_var=0.0,
            request_interval_mean=0.0,
            request_interval_var=0.0,
            bytes_transferred=0,
            num_connections=1,
        )
        result = self.bridge.predict(feats)
        assert result["prediction"] in {"Bot", "Human", "Suspicious"}

    # --- Protocol validation --------------------------------------------

    def test_unsupported_protocol_raises(self):
        feats = _minimal_valid_features(protocol="ICMP")
        with pytest.raises(ValueError) as exc:
            self.bridge.predict(feats)
        msg = str(exc.value)
        assert "ICMP" in msg or "Unsupported protocol" in msg

    def test_empty_protocol_raises(self):
        feats = _minimal_valid_features(protocol="")
        with pytest.raises(ValueError):
            self.bridge.predict(feats)

    def test_protocol_case_insensitive_tcp(self):
        """Lower-case 'tcp' must be accepted and normalised to 'TCP'."""
        feats = _minimal_valid_features(protocol="tcp")
        result = self.bridge.predict(feats)
        assert result["features_used"]["protocol"] == "TCP"

    def test_protocol_case_insensitive_udp(self):
        feats = _minimal_valid_features(protocol="udp")
        result = self.bridge.predict(feats)
        assert result["features_used"]["protocol"] == "UDP"

    # --- Input type check -----------------------------------------------

    def test_non_dict_input_raises(self):
        with pytest.raises(TypeError):
            self.bridge.predict([1, 2, 3])


# ---------------------------------------------------------------------------
# 4. Output structure — mocked model
# ---------------------------------------------------------------------------

class TestOutputStructure:
    def setup_method(self):
        self.bridge = _bridge_with_mock_model(
            classes=("Bot", "Human", "Suspicious"),
            probabilities=(0.90, 0.07, 0.03),
        )

    def test_prediction_key_is_string(self):
        result = self.bridge.predict(_minimal_valid_features())
        assert isinstance(result["prediction"], str)

    def test_probability_estimates_keys_match_classes(self):
        """Keys of probability_estimates must be the model's actual class labels."""
        result = self.bridge.predict(_minimal_valid_features())
        estimates = result["probability_estimates"]
        assert set(estimates.keys()) == {"Bot", "Human", "Suspicious"}

    def test_probability_estimates_values_are_floats(self):
        result = self.bridge.predict(_minimal_valid_features())
        for v in result["probability_estimates"].values():
            assert isinstance(v, float)

    def test_probability_estimates_sum_to_one(self):
        result = self.bridge.predict(_minimal_valid_features())
        total = sum(result["probability_estimates"].values())
        assert abs(total - 1.0) < 1e-4

    def test_features_used_keys_exactly_required_features_in_order(self):
        result = self.bridge.predict(_minimal_valid_features())
        assert list(result["features_used"].keys()) == REQUIRED_FEATURES

    def test_features_used_excludes_metadata(self):
        feats = _minimal_valid_features(
            session_id="S001", device_id="PC99", packet_count=42
        )
        result = self.bridge.predict(feats)
        assert "session_id" not in result["features_used"]
        assert "device_id" not in result["features_used"]
        assert "packet_count" not in result["features_used"]

    def test_metadata_contains_only_supplied_cn_fields(self):
        """
        Metadata must contain only the non-contract keys that were actually
        present in the input.  No extra fields must be invented.
        """
        feats = _minimal_valid_features(session_id="SX", packet_count=7)
        result = self.bridge.predict(feats)
        assert result["metadata"]["session_id"] == "SX"
        assert result["metadata"]["packet_count"] == 7
        # device_id was NOT supplied — must not appear in metadata
        assert "device_id" not in result["metadata"]

    def test_no_metadata_when_none_supplied(self):
        """When input has only the 9 contract features, metadata must be empty."""
        result = self.bridge.predict(_minimal_valid_features())
        assert result["metadata"] == {}

    def test_packet_count_distinct_from_num_connections_in_features_used(self):
        """
        packet_count is a CN metadata field and must never appear in features_used.
        num_connections is a model feature and must appear in features_used.
        """
        feats = _minimal_valid_features(num_connections=1, packet_count=250)
        result = self.bridge.predict(feats)
        assert "num_connections" in result["features_used"]
        assert result["features_used"]["num_connections"] == 1
        assert "packet_count" not in result["features_used"]
        assert result["metadata"]["packet_count"] == 250


# ---------------------------------------------------------------------------
# 5. Model-loading errors
# ---------------------------------------------------------------------------

class TestModelLoadingErrors:
    def test_missing_model_file_raises_file_not_found(self):
        bridge = AIBridge(model_path="/nonexistent/path/model.joblib")
        with pytest.raises(FileNotFoundError):
            bridge.load_model()

    def test_model_without_predict_proba_raises_runtime_error(self):
        bridge = AIBridge.__new__(AIBridge)
        bridge.model_path = "/mock/path/model.joblib"
        bridge._model = None
        bridge._classes = None
        bridge._model_type = None

        bad_model = MagicMock(spec=["predict", "classes_"])   # no predict_proba
        bad_model.classes_ = np.array(["A", "B"])

        with patch("joblib.load", return_value=bad_model):
            with patch("os.path.exists", return_value=True):
                with pytest.raises(RuntimeError) as exc:
                    bridge.load_model()
        assert "predict_proba" in str(exc.value)
