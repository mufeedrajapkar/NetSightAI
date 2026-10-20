"""
test_web_backend.py
-------------------
Tests for SentinelNet Flask Web Intelligence API Server (CN/web/backend_server.py).
"""

import os
import sys
import pytest

# Ensure repository root is on sys.path
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from CN.web.backend_server import app, _seed_initial_flows


@pytest.fixture(scope="module")
def client():
    app.config["TESTING"] = True
    _seed_initial_flows()
    with app.test_client() as c:
        yield c


class TestWebBackendAPI:
    """Test suite for web intelligence API endpoints."""

    def test_get_status(self, client):
        """TC-WEB-01: Status endpoint returns online status and AI model readiness."""
        res = client.get("/api/status")
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "online"
        assert "environment" in data
        assert "model" in data
        assert data["model"]["is_loaded"] is True
        assert "operating_mode" in data

    def test_get_overview(self, client):
        """TC-WEB-02: Overview endpoint returns summary metrics and prediction distribution."""
        res = client.get("/api/overview")
        assert res.status_code == 200
        data = res.get_json()
        assert "total_flows" in data
        assert "counts" in data
        assert "distribution" in data
        assert "recent_flows" in data
        assert data["total_flows"] >= 3

    def test_get_flows_and_detail(self, client):
        """TC-WEB-03: Flows endpoint returns list and detail endpoint returns complete flow."""
        res = client.get("/api/flows")
        assert res.status_code == 200
        data = res.get_json()
        assert "flows" in data
        assert len(data["flows"]) > 0

        first_flow = data["flows"][0]
        flow_id = first_flow["flow_id"]

        # Detail endpoint
        res_detail = client.get(f"/api/flows/{flow_id}")
        assert res_detail.status_code == 200
        detail = res_detail.get_json()
        assert detail["flow_id"] == flow_id
        assert "features" in detail
        assert len(detail["features"]) == 9
        assert "probability_estimates" in detail

    def test_replay_tier_endpoints(self, client):
        """TC-WEB-04: Replaying PCAP tiers produces valid classifications."""
        for tier in ["tier1", "tier2", "tier3"]:
            res = client.post(f"/api/replay/{tier}")
            assert res.status_code == 200
            data = res.get_json()
            assert "flow" in data
            flow = data["flow"]
            assert flow["tier"] == tier
            assert flow["predicted_label"] in {"Human", "Bot", "Suspicious"}
            assert "probability_estimates" in flow
            assert len(flow["features"]) == 9

    def test_replay_invalid_tier(self, client):
        """TC-WEB-05: Replaying an invalid tier returns 400 Bad Request."""
        res = client.post("/api/replay/invalid_tier_999")
        assert res.status_code == 400
        data = res.get_json()
        assert "error" in data

    def test_get_bot_tiers(self, client):
        """TC-WEB-06: Bot tiers endpoint returns 3 tiers and evaluation matrix."""
        res = client.get("/api/bot-tiers")
        assert res.status_code == 200
        data = res.get_json()
        assert "tiers" in data
        assert len(data["tiers"]) == 3
        assert "evaluation_summary" in data

    def test_get_architecture(self, client):
        """TC-WEB-07: Architecture endpoint returns pipeline stages and domain specs."""
        res = client.get("/api/architecture")
        assert res.status_code == 200
        data = res.get_json()
        assert "stages" in data
        assert len(data["stages"]) >= 5
        assert "domains" in data

    def test_capture_endpoints_safety(self, client):
        """TC-WEB-08: Capture start gracefully reports error when Npcap is unavailable."""
        res = client.post("/api/capture/start")
        # On windows without Npcap, returns 400 with clear guidance
        assert res.status_code in {200, 400}
