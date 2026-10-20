"""
test_live_capture_endpoints.py
------------------------------
Unit tests for the live packet capture endpoints in CN/web/backend_server.py
and filter builder in CN/agent/capture/packet_capture.py.
All live capture hardware/permission dependencies are mocked so tests
run deterministically in any unprivileged CI/test environment without admin rights.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from CN.web.backend_server import app, _ACTIVE_CAPTURE
from CN.agent.capture.packet_capture import build_bpf_filter


@pytest.fixture(autouse=True)
def clean_capture_session():
    """Ensure capture session state is cleanly stopped before and after every test."""
    _ACTIVE_CAPTURE["is_capturing"] = False
    _ACTIVE_CAPTURE["capture_instance"] = None
    _ACTIVE_CAPTURE["processor"] = None
    _ACTIVE_CAPTURE["start_time"] = None
    _ACTIVE_CAPTURE["interface"] = None
    _ACTIVE_CAPTURE["filter"] = None
    yield
    if _ACTIVE_CAPTURE.get("capture_instance"):
        try:
            _ACTIVE_CAPTURE["capture_instance"].stop()
        except Exception:
            pass
    _ACTIVE_CAPTURE["is_capturing"] = False
    _ACTIVE_CAPTURE["capture_instance"] = None
    _ACTIVE_CAPTURE["processor"] = None


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestLiveCaptureEndpoints:
    """Test suite for live packet capture endpoints."""

    def test_capture_status_initially_stopped(self, client):
        """TC-CAP-01: Status endpoint reports stopped when no sniffer is active."""
        res = client.get("/api/capture/status")
        assert res.status_code == 200
        data = res.get_json()
        assert data["is_capturing"] is False
        assert data["status"] == "stopped"
        assert data["packets_seen"] == 0

    def test_capture_start_fails_when_unsupported_environment(self, client):
        """TC-CAP-02: Start endpoint returns 400 when Npcap is missing or not admin."""
        with patch("CN.web.backend_server.check_environment") as mock_env:
            mock_env.return_value = {
                "pcap_available": False,
                "is_admin": False,
                "can_capture_live": False,
                "message": "Npcap packet driver is not installed on Windows",
                "setup_guide": "Install Npcap",
            }
            res = client.post("/api/capture/start", json={"port": 5000})
            assert res.status_code == 400
            data = res.get_json()
            assert "error" in data
            assert "Npcap" in data["error"] or "administrator" in data["error"].lower()

    def test_capture_start_success_with_mocked_sniffer(self, client):
        """TC-CAP-03: Start endpoint starts thread and reports running with mocked PacketCapture."""
        mock_capture = MagicMock()
        mock_capture.raw_packets = [1, 2, 3]
        mock_capture.parsed_packets = [1, 2]

        with patch("CN.web.backend_server.check_environment") as mock_env, \
             patch("CN.web.backend_server.is_windows", return_value=True), \
             patch("CN.web.backend_server.PacketCapture", return_value=mock_capture):
            mock_env.return_value = {
                "pcap_available": True,
                "is_admin": True,
                "can_capture_live": True,
                "loopback_iface": "Npcap Loopback Adapter",
                "message": "Ready",
                "setup_guide": "",
            }

            res = client.post("/api/capture/start", json={"port": 5000})
            assert res.status_code == 200
            data = res.get_json()
            assert data["status"] == "running"
            assert "filter" in data
            assert "port 5000" in data["filter"]

            # Verify status now reports running
            st_res = client.get("/api/capture/status")
            assert st_res.status_code == 200
            st_data = st_res.get_json()
            assert st_data["is_capturing"] is True
            assert st_data["status"] == "running"

    def test_capture_start_already_running(self, client):
        """TC-CAP-04: Starting while already capturing returns 409 conflict."""
        _ACTIVE_CAPTURE["is_capturing"] = True
        mock_cap = MagicMock()
        mock_cap.raw_packets = [1]
        _ACTIVE_CAPTURE["capture_instance"] = mock_cap

        with patch("CN.web.backend_server.check_environment") as mock_env, \
             patch("CN.web.backend_server.is_windows", return_value=True):
            mock_env.return_value = {
                "pcap_available": True,
                "is_admin": True,
                "can_capture_live": True,
                "loopback_iface": "Npcap Loopback Adapter",
                "message": "Ready",
                "setup_guide": "",
            }

            res = client.post("/api/capture/start", json={"port": 5000})
            assert res.status_code == 409
            data = res.get_json()
            assert "already active" in data["error"].lower()

    def test_capture_stop_when_running(self, client):
        """TC-CAP-05: Stopping active capture cleanly shuts down sniffer and returns packet count."""
        mock_capture = MagicMock()
        mock_capture.raw_packets = [1] * 42
        mock_capture.parsed_packets = [1] * 12

        mock_processor = MagicMock()

        _ACTIVE_CAPTURE["is_capturing"] = True
        _ACTIVE_CAPTURE["capture_instance"] = mock_capture
        _ACTIVE_CAPTURE["processor"] = mock_processor

        res = client.post("/api/capture/stop")
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "stopped"
        assert data["packets_captured"] == 42
        assert data["packets_parsed"] == 12
        assert mock_capture.stop.called

        # Session state is now stopped
        assert _ACTIVE_CAPTURE["is_capturing"] is False

    def test_capture_stop_when_not_running(self, client):
        """TC-CAP-06: Stopping when not active returns 200 with notice message."""
        _ACTIVE_CAPTURE["is_capturing"] = False
        res = client.post("/api/capture/stop")
        assert res.status_code == 200
        data = res.get_json()
        assert "no active" in data["message"].lower()


class TestBPFFilterBuilder:
    """Test suite for build_bpf_filter helper."""

    def test_default_filter(self):
        """Default filter targets port 5000 TCP traffic."""
        f = build_bpf_filter()
        assert f == "tcp and (src port 5000 or dst port 5000)"

    def test_custom_port(self):
        """Custom port creates matching TCP BPF filter."""
        f = build_bpf_filter(port=8080)
        assert f == "tcp and (src port 8080 or dst port 8080)"

    def test_all_ip(self):
        """All IP mode returns 'ip' filter."""
        f = build_bpf_filter(all_ip=True)
        assert f == "ip"

    def test_custom_bpf_string(self):
        """Explicit custom BPF filter takes precedence."""
        f = build_bpf_filter(custom_filter="udp and port 53")
        assert f == "udp and port 53"
