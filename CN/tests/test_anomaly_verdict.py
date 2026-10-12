"""
test_anomaly_verdict.py
-----------------------
Unit tests for the runtime "Suspicious" hybrid verdict logic in CN/agent/ai_bridge.py
verifying all decision branches:
  Branch (a): Classifier predicts Human but Isolation Forest flags anomaly -> Suspicious
  Branch (b): Classifier confidence below threshold (default 0.6) -> Suspicious
  Branch (c): Classifier predicts Human with high confidence and normal anomaly score -> Human
  Branch (d): Classifier predicts Bot with high confidence -> Bot
  Branch (e): Missing Isolation Forest model artifact handled gracefully (returns None, does not crash)
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from CN.agent.ai_bridge import AIBridge, REQUIRED_FEATURES


def _sample_feature_dict():
    """Return a valid minimal feature dict matching the contract."""
    return {
        "requests_per_sec": 3.5,
        "session_duration": 15.0,
        "packet_size_mean": 600.0,
        "packet_size_var": 30000.0,
        "request_interval_mean": 0.28,
        "request_interval_var": 0.02,
        "bytes_transferred": 50000,
        "num_connections": 1,
        "protocol": "TCP",
    }


class TestSuspiciousVerdictBranches:
    """Test suite covering all branches of the runtime Suspicious verdict determination."""

    def test_branch_a_human_with_anomaly_detector_disagreement(self):
        """
        Branch (a): Classifier predicts 'Human' with high confidence (0.85),
        but Isolation Forest flags the session as an anomaly (predict == -1).
        Verdict must escalate to 'Suspicious' with disagreement=True.
        """
        mock_classifier = MagicMock()
        mock_classifier.classes_ = np.array(["Bot", "Human", "Suspicious"])
        mock_classifier.predict.return_value = np.array(["Human"])
        mock_classifier.predict_proba.return_value = np.array([[0.10, 0.85, 0.05]])

        mock_if = MagicMock()
        # predict -1 means outlier/anomaly
        mock_if.predict.return_value = np.array([-1])
        # negative decision function means anomaly
        mock_if.decision_function.return_value = np.array([-0.15])

        bridge = AIBridge()
        bridge._model = mock_classifier
        bridge._classes = list(mock_classifier.classes_)
        bridge._model_type = "MockClassifier"
        bridge._if_model = mock_if
        bridge._if_loaded = True

        result = bridge.predict(_sample_feature_dict())

        assert result["raw_prediction"] == "Human"
        assert result["verdict"] == "Suspicious"
        assert result["prediction"] == "Suspicious"
        assert result["disagreement"] is True
        assert result["is_anomaly"] is True
        assert result["anomaly_score"] == 0.15  # -(-0.15)
        assert result["verdict_reason"] == "anomaly_detector_disagreement"

    def test_branch_b_low_classification_confidence(self):
        """
        Branch (b): Classifier top probability is below threshold (0.50 < 0.60).
        Even if not flagged by anomaly detector, verdict must be 'Suspicious'.
        """
        mock_classifier = MagicMock()
        mock_classifier.classes_ = np.array(["Bot", "Human", "Suspicious"])
        mock_classifier.predict.return_value = np.array(["Bot"])
        # Top prob is 0.48 < 0.60 threshold
        mock_classifier.predict_proba.return_value = np.array([[0.48, 0.40, 0.12]])

        mock_if = MagicMock()
        mock_if.predict.return_value = np.array([1])  # Normal
        mock_if.decision_function.return_value = np.array([0.20])

        bridge = AIBridge(confidence_threshold=0.60)
        bridge._model = mock_classifier
        bridge._classes = list(mock_classifier.classes_)
        bridge._model_type = "MockClassifier"
        bridge._if_model = mock_if
        bridge._if_loaded = True

        result = bridge.predict(_sample_feature_dict())

        assert result["raw_prediction"] == "Bot"
        assert result["verdict"] == "Suspicious"
        assert result["prediction"] == "Suspicious"
        assert result["disagreement"] is True
        assert "low_confidence" in result["verdict_reason"]
        assert result["is_anomaly"] is False

    def test_branch_c_human_consensus_high_confidence(self):
        """
        Branch (c): Classifier predicts 'Human' with high confidence (0.92)
        and Isolation Forest confirms normal behavior (predict == 1).
        Verdict must remain 'Human' with disagreement=False.
        """
        mock_classifier = MagicMock()
        mock_classifier.classes_ = np.array(["Bot", "Human", "Suspicious"])
        mock_classifier.predict.return_value = np.array(["Human"])
        mock_classifier.predict_proba.return_value = np.array([[0.05, 0.92, 0.03]])

        mock_if = MagicMock()
        mock_if.predict.return_value = np.array([1])
        mock_if.decision_function.return_value = np.array([0.25])

        bridge = AIBridge()
        bridge._model = mock_classifier
        bridge._classes = list(mock_classifier.classes_)
        bridge._model_type = "MockClassifier"
        bridge._if_model = mock_if
        bridge._if_loaded = True

        result = bridge.predict(_sample_feature_dict())

        assert result["raw_prediction"] == "Human"
        assert result["verdict"] == "Human"
        assert result["prediction"] == "Human"
        assert result["disagreement"] is False
        assert result["is_anomaly"] is False
        assert result["verdict_reason"] == "classifier_consensus"

    def test_branch_d_bot_consensus_high_confidence(self):
        """
        Branch (d): Classifier predicts 'Bot' with high confidence (0.95).
        Verdict remains 'Bot'.
        """
        mock_classifier = MagicMock()
        mock_classifier.classes_ = np.array(["Bot", "Human", "Suspicious"])
        mock_classifier.predict.return_value = np.array(["Bot"])
        mock_classifier.predict_proba.return_value = np.array([[0.95, 0.03, 0.02]])

        mock_if = MagicMock()
        mock_if.predict.return_value = np.array([-1])
        mock_if.decision_function.return_value = np.array([-0.30])

        bridge = AIBridge()
        bridge._model = mock_classifier
        bridge._classes = list(mock_classifier.classes_)
        bridge._model_type = "MockClassifier"
        bridge._if_model = mock_if
        bridge._if_loaded = True

        result = bridge.predict(_sample_feature_dict())

        assert result["raw_prediction"] == "Bot"
        assert result["verdict"] == "Bot"
        assert result["prediction"] == "Bot"
        assert result["disagreement"] is False
        assert result["verdict_reason"] == "classifier_consensus"

    def test_branch_e_graceful_handling_missing_isolation_forest(self):
        """
        Branch (e): Isolation Forest file does not exist.
        Bridge must lazily load without crashing, returning anomaly_score=None
        and is_anomaly=None, and computing verdict from classifier confidence.
        """
        mock_classifier = MagicMock()
        mock_classifier.classes_ = np.array(["Bot", "Human", "Suspicious"])
        mock_classifier.predict.return_value = np.array(["Human"])
        mock_classifier.predict_proba.return_value = np.array([[0.10, 0.85, 0.05]])

        # Non-existent path
        bridge = AIBridge(if_path="non_existent_model_file_12345.joblib")
        bridge._model = mock_classifier
        bridge._classes = list(mock_classifier.classes_)
        bridge._model_type = "MockClassifier"

        result = bridge.predict(_sample_feature_dict())

        assert result["anomaly_score"] is None
        assert result["is_anomaly"] is None
        assert result["verdict"] == "Human"
        assert result["disagreement"] is False
        assert result["verdict_reason"] == "classifier_consensus"
