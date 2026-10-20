"""
test_phase5b_capture.py
-----------------------
CN_AI Phase 5B - Real Traffic Capture & Scapy Packet Processing Test Suite.

Tests:
1. Scapy Packet Parsing (TCP flags, sequence numbers, ports, UDP, non-IP, edge cases).
2. PacketCapture environment detection & Windows Npcap diagnostics.
3. Mocked Sniffing & Background Worker Thread safety (CI-safe, no Npcap required).
4. Scapy PCAP write, read, replay, FlowProcessor integration, and AIBridge classification.
5. End-to-end pipeline verification across Tier 1, Tier 2, and Tier 3 Scapy packet flows.
"""

import os
import sys
import tempfile
import threading
from unittest.mock import patch, MagicMock

import pytest
from scapy.all import IP, TCP, UDP, Ether, Raw, wrpcap

# Ensure repo root is on sys.path
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from CN.agent.capture.packet_parser import parse_packet
from CN.agent.capture.packet_capture import (
    PacketCapture,
    check_environment,
    get_loopback_interface,
    is_windows,
    is_admin,
    DEFAULT_BPF_FILTER,
)
from CN.agent.flow.flow_processor import FlowProcessor
from CN.agent.ai_bridge import AIBridge, REQUIRED_FEATURES
from CN.demos.generate_sample_pcap import (
    generate_tier1_pcap,
    generate_tier2_pcap,
    generate_tier3_pcap,
)


# ===========================================================================
# 1. Scapy Packet Parser Unit Tests
# ===========================================================================

class TestPacketParser:
    """Unit tests for CN/agent/capture/packet_parser.py."""

    def test_parse_tcp_syn_packet(self):
        """TC-P5B-01: Correctly parse IPv4 TCP SYN packet."""
        pkt = IP(src="192.168.1.10", dst="192.168.1.1") / TCP(sport=54321, dport=5000, flags="S", seq=1000)
        parsed = parse_packet(pkt)

        assert parsed is not None
        assert parsed["src_ip"] == "192.168.1.10"
        assert parsed["dst_ip"] == "192.168.1.1"
        assert parsed["src_port"] == 54321
        assert parsed["dst_port"] == 5000
        assert parsed["protocol"] == "TCP"
        assert parsed["is_syn"] is True
        assert parsed["is_ack"] is False
        assert parsed["is_fin"] is False
        assert parsed["is_rst"] is False
        assert parsed["seq"] == 1000
        assert parsed["packet_size"] == len(pkt)
        assert isinstance(parsed["time"], float)

    def test_parse_tcp_syn_ack_packet(self):
        """TC-P5B-02: Correctly parse IPv4 TCP SYN-ACK packet."""
        pkt = IP(src="127.0.0.1", dst="127.0.0.1") / TCP(sport=5000, dport=54321, flags="SA", seq=5000)
        parsed = parse_packet(pkt)

        assert parsed is not None
        assert parsed["is_syn"] is True
        assert parsed["is_ack"] is True
        assert parsed["is_fin"] is False
        assert parsed["is_rst"] is False
        assert parsed["seq"] == 5000

    def test_parse_tcp_fin_ack_packet(self):
        """TC-P5B-03: Correctly parse IPv4 TCP FIN-ACK packet."""
        pkt = IP(src="127.0.0.1", dst="127.0.0.1") / TCP(sport=54321, dport=5000, flags="FA", seq=2000)
        parsed = parse_packet(pkt)

        assert parsed is not None
        assert parsed["is_fin"] is True
        assert parsed["is_ack"] is True
        assert parsed["is_syn"] is False

    def test_parse_tcp_rst_packet(self):
        """TC-P5B-04: Correctly parse IPv4 TCP RST packet."""
        pkt = IP(src="127.0.0.1", dst="127.0.0.1") / TCP(sport=5000, dport=54321, flags="R", seq=9999)
        parsed = parse_packet(pkt)

        assert parsed is not None
        assert parsed["is_rst"] is True
        assert parsed["is_syn"] is False

    def test_parse_udp_packet(self):
        """TC-P5B-05: Correctly parse IPv4 UDP packet."""
        pkt = IP(src="10.0.0.2", dst="10.0.0.1") / UDP(sport=1234, dport=53)
        parsed = parse_packet(pkt)

        assert parsed is not None
        assert parsed["protocol"] == "UDP"
        assert parsed["src_port"] == 1234
        assert parsed["dst_port"] == 53
        assert parsed["is_syn"] is False
        assert parsed["seq"] is None

    def test_parse_non_ip_packet_returns_none(self):
        """TC-P5B-06: Non-IPv4 packet (e.g. raw Ethernet) returns None."""
        pkt = Ether()
        assert parse_packet(pkt) is None

    def test_parse_packet_with_payload(self):
        """TC-P5B-07: TCP packet with HTTP payload calculates full packet size."""
        payload = b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
        pkt = IP(src="127.0.0.1", dst="127.0.0.1") / TCP(sport=50000, dport=5000, flags="PA", seq=100) / Raw(load=payload)
        parsed = parse_packet(pkt)

        assert parsed is not None
        assert parsed["packet_size"] == len(pkt)
        assert parsed["packet_size"] >= len(payload) + 40


# ===========================================================================
# 2. Environment Diagnostics & Windows Checks
# ===========================================================================

class TestCaptureEnvironment:
    """Tests for environment diagnostic checks."""

    def test_check_environment_keys(self):
        """TC-P5B-08: check_environment returns complete diagnostic dictionary."""
        env = check_environment()
        assert isinstance(env, dict)
        required_keys = {
            "pcap_available", "is_admin", "loopback_iface",
            "can_capture_live", "message", "setup_guide"
        }
        for key in required_keys:
            assert key in env

    def test_default_bpf_filter_safety(self):
        """TC-P5B-09: Default BPF filter restricts to target port (no broad capture)."""
        assert "port 5000" in DEFAULT_BPF_FILTER
        assert "tcp" in DEFAULT_BPF_FILTER


# ===========================================================================
# 3. PacketCapture Unit Tests with Mocked Sniffer
# ===========================================================================

class TestPacketCaptureUnitMocked:
    """Unit tests for PacketCapture using mocked Scapy sniffing and mock packets."""

    def test_packet_handler_updates_processor(self):
        """TC-P5B-10: _packet_handler correctly updates FlowProcessor and stores features."""
        capture = PacketCapture(label="Bot", bot_tier="Tier1")

        pkt1 = IP(src="127.0.0.1", dst="127.0.0.1") / TCP(sport=50001, dport=5000, flags="S", seq=100)
        pkt2 = IP(src="127.0.0.1", dst="127.0.0.1") / TCP(sport=5000, dport=50001, flags="SA", seq=500)
        pkt3 = IP(src="127.0.0.1", dst="127.0.0.1") / TCP(sport=50001, dport=5000, flags="A", seq=101)

        capture._packet_handler(pkt1)
        capture._packet_handler(pkt2)
        capture._packet_handler(pkt3)

        assert len(capture.raw_packets) == 3
        assert len(capture.parsed_packets) == 3
        assert len(capture.extracted_features) == 3

        latest = capture.get_latest_features()
        assert latest is not None
        assert latest["packet_count"] == 3
        assert latest["num_connections"] == 1
        assert latest["protocol"] == "TCP"

    def test_mocked_sniff_thread_lifecycle(self):
        """TC-P5B-11: Start and stop background sniffing thread safely."""
        capture = PacketCapture()

        def fake_sniff(**kwargs):
            prn = kwargs.get("prn")
            stop_filter = kwargs.get("stop_filter")

            # Emit 2 packets then check stop filter
            p1 = IP(src="127.0.0.1", dst="127.0.0.1") / TCP(sport=50001, dport=5000, flags="S")
            p2 = IP(src="127.0.0.1", dst="127.0.0.1") / TCP(sport=5000, dport=50001, flags="SA")
            if prn:
                prn(p1)
                prn(p2)

        with patch("CN.agent.capture.packet_capture.sniff", side_effect=fake_sniff):
            capture.start()
            # Give worker thread a moment to run
            capture.stop()

            assert len(capture.parsed_packets) == 2
            assert capture.is_capturing is False

    def test_save_and_replay_pcap(self):
        """TC-P5B-12: Save captured Scapy packets to PCAP and replay into FlowProcessor."""
        capture = PacketCapture(label="Bot", bot_tier="Tier1")

        pkts = [
            IP(src="127.0.0.1", dst="127.0.0.1") / TCP(sport=50001, dport=5000, flags="S", seq=100),
            IP(src="127.0.0.1", dst="127.0.0.1") / TCP(sport=5000, dport=50001, flags="SA", seq=500),
            IP(src="127.0.0.1", dst="127.0.0.1") / TCP(sport=50001, dport=5000, flags="A", seq=101),
        ]
        for p in pkts:
            capture._packet_handler(p)

        with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as tf:
            temp_pcap = tf.name

        try:
            capture.save_pcap(temp_pcap)
            assert os.path.exists(temp_pcap)
            assert os.path.getsize(temp_pcap) > 0

            # Replay into fresh capture instance
            replay_cap = PacketCapture(label="Bot", bot_tier="Tier1")
            replayed_features = replay_cap.replay_pcap(temp_pcap)

            assert len(replayed_features) == 3
            assert len(replay_cap.parsed_packets) == 3
            assert replay_cap.get_latest_features()["packet_count"] == 3

            # Classify replayed flow
            result = replay_cap.classify()
            assert "prediction" in result
            assert "probability_estimates" in result
            assert len(result["features_used"]) == 9

        finally:
            if os.path.exists(temp_pcap):
                os.remove(temp_pcap)


# ===========================================================================
# 4. End-to-End Scapy Packet PCAP to AI Classification
# ===========================================================================

class TestPhase5BEndToEndPipeline:
    """End-to-end verification of Scapy packet replay through FlowProcessor and AIBridge."""

    def test_tier1_scapy_pcap_pipeline(self):
        """TC-P5B-13: Tier 1 Scapy PCAP produces valid classification and 9 contract features."""
        with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as tf:
            pcap_path = tf.name

        try:
            generate_tier1_pcap(pcap_path, n_requests=6, interval=0.5)

            capture = PacketCapture(label="Bot", bot_tier="Tier1")
            features_list = capture.replay_pcap(pcap_path)

            assert len(features_list) > 0
            latest = capture.get_latest_features()
            assert latest is not None

            # Verify 9 contract features
            for feat in REQUIRED_FEATURES:
                assert feat in latest, f"Missing required feature: {feat}"

            bridge = AIBridge()
            result = bridge.predict(latest)

            assert result["prediction"] in {"Bot", "Human", "Suspicious"}
            assert isinstance(result["probability_estimates"], dict)
            assert abs(sum(result["probability_estimates"].values()) - 1.0) < 1e-4
            assert len(result["features_used"]) == 9

        finally:
            if os.path.exists(pcap_path):
                os.remove(pcap_path)

    def test_tier2_scapy_pcap_pipeline(self):
        """TC-P5B-14: Tier 2 Scapy PCAP produces valid classification."""
        with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as tf:
            pcap_path = tf.name

        try:
            generate_tier2_pcap(pcap_path, n_requests=6)

            capture = PacketCapture(label="Bot", bot_tier="Tier2")
            capture.replay_pcap(pcap_path)
            latest = capture.get_latest_features()

            bridge = AIBridge()
            result = bridge.predict(latest)

            assert result["prediction"] in {"Bot", "Human", "Suspicious"}
            assert abs(sum(result["probability_estimates"].values()) - 1.0) < 1e-4

        finally:
            if os.path.exists(pcap_path):
                os.remove(pcap_path)

    def test_tier3_scapy_pcap_pipeline(self):
        """TC-P5B-15: Tier 3 Scapy PCAP produces valid classification."""
        with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as tf:
            pcap_path = tf.name

        try:
            generate_tier3_pcap(pcap_path, n_cycles=2)

            capture = PacketCapture(label="Bot", bot_tier="Tier3")
            capture.replay_pcap(pcap_path)
            latest = capture.get_latest_features()

            bridge = AIBridge()
            result = bridge.predict(latest)

            assert result["prediction"] in {"Bot", "Human", "Suspicious"}
            assert latest["packet_count"] >= 15
            assert latest["session_duration"] > 0.0

        finally:
            if os.path.exists(pcap_path):
                os.remove(pcap_path)
