"""
test_ingest_pipeline.py
-----------------------
Integration and unit tests for SentinelNet's live networked multi-device
data ingestion pipeline:
1. POST /api/ingest endpoint authentication (X-API-Key).
2. JSON payload validation and contract feature mapping.
3. Live flow classification via AIBridge and storage in _ANALYZED_FLOWS.
4. FlowProcessor agent push functionality and graceful network fallback.
"""

import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock

# Ensure repo root is on sys.path
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from CN.web.backend_server import app, _seed_initial_flows, _ANALYZED_FLOWS, _STORE_LOCK, get_configured_api_key
from CN.agent.flow.flow_processor import FlowProcessor


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SENTINELNET_API_KEY", "test-secret-key-12345")
    app.config["TESTING"] = True
    _seed_initial_flows()
    with app.test_client() as c:
        yield c


@pytest.fixture
def sample_payload():
    return {
        "session_id": "test_sess_dev02_101",
        "device_id": "PC02",
        "session_duration": 1.25,
        "packets_per_sec": 8.0,
        "packet_size_mean": 64.0,
        "packet_size_var": 0.0,
        "packet_interval_mean": 0.125,
        "packet_interval_var": 0.0001,
        "bytes_transferred": 512,
        "packet_count": 10,
        "protocol": "TCP",
        "label": "Bot",
        "bot_tier": "Tier1",
    }


class TestIngestEndpointAuth:
    """Test X-API-Key authentication behavior on /api/ingest."""

    def test_missing_api_key_rejected(self, client, sample_payload):
        """TC-INGEST-AUTH-01: Requests without X-API-Key return 401 Unauthorized."""
        res = client.post("/api/ingest", json=sample_payload)
        assert res.status_code == 401
        data = res.get_json()
        assert "error" in data
        assert "Unauthorized" in data["error"]

    def test_invalid_api_key_rejected(self, client, sample_payload):
        """TC-INGEST-AUTH-02: Requests with incorrect X-API-Key return 401 Unauthorized."""
        headers = {"X-API-Key": "wrong-secret-key-12345"}
        res = client.post("/api/ingest", json=sample_payload, headers=headers)
        assert res.status_code == 401
        data = res.get_json()
        assert "error" in data

    def test_valid_api_key_accepted(self, client, sample_payload):
        """TC-INGEST-AUTH-03: Requests with correct X-API-Key are processed and stored."""
        expected_key = get_configured_api_key()
        headers = {"X-API-Key": expected_key}
        res = client.post("/api/ingest", json=sample_payload, headers=headers)
        assert res.status_code == 201
        data = res.get_json()
        assert data["message"] == "Session successfully ingested and classified"
        assert data["device_id"] == "PC02"
        assert "prediction" in data
        assert "probability_estimates" in data
        assert "flow" in data
        assert data["flow"]["device_id"] == "PC02"

    def test_unconfigured_api_key_server_error(self, client, monkeypatch, sample_payload):
        """TC-INGEST-AUTH-04: If server has no API key configured, /api/ingest returns 500 error."""
        monkeypatch.delenv("SENTINELNET_API_KEY", raising=False)
        with patch("CN.web.backend_server.get_configured_api_key", return_value=None):
            res = client.post("/api/ingest", json=sample_payload, headers={"X-API-Key": "some-key"})
            assert res.status_code == 500
            assert "not configured" in res.get_json()["error"]



class TestIngestPayloadProcessing:
    """Test payload validation and integration with backend storage & AI."""

    def test_non_json_payload_rejected(self, client):
        """TC-INGEST-PAYLOAD-01: Non-JSON payload returns 400 Bad Request."""
        expected_key = get_configured_api_key()
        res = client.post(
            "/api/ingest",
            data="not-a-json-payload",
            headers={"X-API-Key": expected_key, "Content-Type": "text/plain"},
        )
        assert res.status_code == 400

    def test_ingested_flow_appears_in_flows_list(self, client, sample_payload):
        """TC-INGEST-FLOW-01: Ingested flow is added to in-memory store and returned by /api/flows."""
        expected_key = get_configured_api_key()
        headers = {"X-API-Key": expected_key}
        sample_payload["session_id"] = "unique_sess_9999"

        res = client.post("/api/ingest", json=sample_payload, headers=headers)
        assert res.status_code == 201

        flows_res = client.get("/api/flows")
        assert flows_res.status_code == 200
        flows = flows_res.get_json()["flows"]
        matching = [f for f in flows if f.get("session_id") == "unique_sess_9999"]
        assert len(matching) == 1
        assert matching[0]["device_id"] == "PC02"
        assert matching[0]["source_type"] == "Live Agent Ingest"


class TestFlowProcessorNetworkPush:
    """Test FlowProcessor push mechanism, URL configuration, and local fallback."""

    def test_push_success(self, tmp_path):
        """TC-AGENT-PUSH-01: Successful push sends JSON and logs success."""
        csv_path = str(tmp_path / "test_out.csv")
        processor = FlowProcessor(
            device_id="PC03",
            label="Human",
            csv_file=csv_path,
            server_url="http://mock-server:5001",
            api_key="mock-key",
            push_to_server=True,
            write_local_csv=True,
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 201

        with patch("requests.post", return_value=mock_resp) as mock_post:
            feature_data = {
                "session_id": "sess_pc03_1",
                "device_id": "PC03",
                "session_duration": 2.0,
                "packets_per_sec": 4.0,
                "packet_size_mean": 100.0,
                "packet_size_var": 0.0,
                "packet_interval_mean": 0.25,
                "packet_interval_var": 0.0,
                "bytes_transferred": 800,
                "packet_count": 8,
                "protocol": "TCP",
                "label": "Human",
                "bot_tier": "None",
            }
            processor.save_features(feature_data)

            assert mock_post.called
            call_url = mock_post.call_args[0][0]
            assert call_url == "http://mock-server:5001/api/ingest"
            call_headers = mock_post.call_args[1]["headers"]
            assert call_headers["X-API-Key"] == "mock-key"
            assert os.path.exists(csv_path)

    def test_push_failure_graceful_fallback(self, tmp_path):
        """TC-AGENT-PUSH-02: Network failure falls back to local CSV without raising exception."""
        csv_path = str(tmp_path / "fallback.csv")
        processor = FlowProcessor(
            device_id="PC04",
            label="Bot",
            csv_file=csv_path,
            server_url="http://unreachable-host:9999",
            api_key="mock-key",
            push_to_server=True,
            write_local_csv=False,  # only save locally as fallback when push fails
        )

        with patch("requests.post", side_effect=Exception("Connection refused")):
            feature_data = {
                "session_id": "sess_fallback_1",
                "device_id": "PC04",
                "session_duration": 1.0,
                "packets_per_sec": 10.0,
                "packet_size_mean": 50.0,
                "packet_size_var": 0.0,
                "packet_interval_mean": 0.1,
                "packet_interval_var": 0.0,
                "bytes_transferred": 500,
                "packet_count": 10,
                "protocol": "TCP",
                "label": "Bot",
                "bot_tier": "Tier1",
            }
            # Should not raise exception
            processor.save_features(feature_data)

            # Fallback CSV MUST exist and contain the row
            assert os.path.exists(csv_path)
            with open(csv_path, "r") as f:
                content = f.read()
                assert "sess_fallback_1" in content
                assert "PC04" in content

    def test_push_failure_graceful_fallback_real_extracted_features(self, tmp_path):
        """Regression test: push failure with real extract_features() output does not crash on local CSV save."""
        from CN.agent.features import extract_features
        from CN.agent.label_manager import LabelManager

        csv_path = str(tmp_path / "fallback_real.csv")
        processor = FlowProcessor(
            device_id="PC05",
            label="Bot",
            bot_tier="tier1",
            csv_file=csv_path,
            server_url="http://unreachable-host:9999",
            api_key="mock-key",
            push_to_server=True,
            write_local_csv=False,
        )

        session = {
            "session_id": "sess_real_fail_1",
            "timestamps": [10.0, 10.2, 10.5],
            "packet_sizes": [100, 200, 300],
            "first_seen": 10.0,
            "last_seen": 10.5,
            "packet_count": 3,
            "total_bytes": 600,
            "protocol": "TCP",
            "num_connections": 1,
        }
        features = extract_features(session)
        labeled = LabelManager(device_id="PC05", label="Bot", bot_tier="tier1").add_labels(features)

        with patch("requests.post", side_effect=Exception("Connection refused")):
            processor.save_features(labeled)

        assert os.path.exists(csv_path)
        with open(csv_path, "r") as f:
            content = f.read()
            assert "sess_real_fail_1" in content
            assert "PC05" in content
            assert "num_connections" in content

    def test_push_refused_without_api_key(self, monkeypatch):
        """TC-AGENT-PUSH-03: Agent refuses to push if api_key is not configured."""
        monkeypatch.delenv("SENTINELNET_API_KEY", raising=False)
        processor = FlowProcessor(
            device_id="PC01",
            server_url="http://mock-server:5001",
            api_key=None,
            push_to_server=True,
            write_local_csv=True,
        )
        with patch("requests.post") as mock_post:
            success = processor._push_to_server({"session_id": "sess_1"})
            assert success is False
            assert not mock_post.called


