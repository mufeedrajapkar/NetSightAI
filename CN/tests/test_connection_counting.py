"""
test_connection_counting.py
---------------------------
Unit tests for TCP connection lifecycle, SYN deduplication,
UDP pseudo-connections, and feature extraction edge cases.
"""

import pytest
from CN.agent.flow.flow_tracker import FlowTracker
from CN.agent.session.session_tracker import SessionTracker
from CN.agent.features import extract_features


# -----------------------------------------------------------------------------
# TCP TESTS
# -----------------------------------------------------------------------------

def test_tcp_normal_handshake_and_close():
    """
    TC-01: A normal TCP handshake (SYN -> SYN-ACK -> ACK) followed by data and FIN.
    Expected: num_connections == 1, packet_count == 5.
    """
    tracker = FlowTracker()

    packets = [
        # 1. Client SYN (seq 1000)
        {"time": 100.0, "src_ip": "192.168.1.10", "dst_ip": "1.2.3.4", "src_port": 50000, "dst_port": 80, "protocol": "TCP", "packet_size": 60, "is_syn": True, "is_ack": False, "is_fin": False, "is_rst": False, "seq": 1000},
        # 2. Server SYN-ACK (seq 5000, ack 1001)
        {"time": 100.05, "src_ip": "1.2.3.4", "dst_ip": "192.168.1.10", "src_port": 80, "dst_port": 50000, "protocol": "TCP", "packet_size": 60, "is_syn": True, "is_ack": True, "is_fin": False, "is_rst": False, "seq": 5000},
        # 3. Client ACK (seq 1001, ack 5001)
        {"time": 100.06, "src_ip": "192.168.1.10", "dst_ip": "1.2.3.4", "src_port": 50000, "dst_port": 80, "protocol": "TCP", "packet_size": 54, "is_syn": False, "is_ack": True, "is_fin": False, "is_rst": False, "seq": 1001},
        # 4. Data packet (500B)
        {"time": 100.10, "src_ip": "192.168.1.10", "dst_ip": "1.2.3.4", "src_port": 50000, "dst_port": 80, "protocol": "TCP", "packet_size": 500, "is_syn": False, "is_ack": True, "is_fin": False, "is_rst": False, "seq": 1001},
        # 5. Client FIN-ACK
        {"time": 100.50, "src_ip": "192.168.1.10", "dst_ip": "1.2.3.4", "src_port": 50000, "dst_port": 80, "protocol": "TCP", "packet_size": 54, "is_syn": False, "is_ack": True, "is_fin": True, "is_rst": False, "seq": 1501},
    ]

    for p in packets:
        flow = tracker.add_packet(p)

    assert flow["num_connections"] == 1
    assert flow["packet_count"] == 5
    assert flow["total_bytes"] == 60 + 60 + 54 + 500 + 54


def test_tcp_syn_retransmission_deduplication():
    """
    TC-02: Client sends a SYN, re-sends identical SYN (retransmission due to drop), then completes handshake.
    Expected: num_connections == 1 (retransmitted SYN is deduplicated).
    """
    tracker = FlowTracker()

    packets = [
        # 1. Client SYN (seq 2000) at t=10.0
        {"time": 10.0, "src_ip": "10.0.0.1", "dst_ip": "10.0.0.2", "src_port": 40001, "dst_port": 443, "protocol": "TCP", "packet_size": 60, "is_syn": True, "is_ack": False, "is_fin": False, "is_rst": False, "seq": 2000},
        # 2. Retransmitted SYN (same seq 2000) at t=11.0
        {"time": 11.0, "src_ip": "10.0.0.1", "dst_ip": "10.0.0.2", "src_port": 40001, "dst_port": 443, "protocol": "TCP", "packet_size": 60, "is_syn": True, "is_ack": False, "is_fin": False, "is_rst": False, "seq": 2000},
        # 3. Server SYN-ACK at t=11.05
        {"time": 11.05, "src_ip": "10.0.0.2", "dst_ip": "10.0.0.1", "src_port": 443, "dst_port": 40001, "protocol": "TCP", "packet_size": 60, "is_syn": True, "is_ack": True, "is_fin": False, "is_rst": False, "seq": 8000},
        # 4. Client ACK at t=11.06
        {"time": 11.06, "src_ip": "10.0.0.1", "dst_ip": "10.0.0.2", "src_port": 40001, "dst_port": 443, "protocol": "TCP", "packet_size": 54, "is_syn": False, "is_ack": True, "is_fin": False, "is_rst": False, "seq": 2001},
    ]

    for p in packets:
        flow = tracker.add_packet(p)

    assert flow["num_connections"] == 1
    assert flow["packet_count"] == 4


def test_tcp_5tuple_reuse_after_close():
    """
    TC-03: Connection 1 closes with FIN. Later, a new SYN with different sequence number arrives on same 5-tuple.
    Expected: num_connections == 2.
    """
    tracker = FlowTracker()

    packets_conn1 = [
        {"time": 1.0, "src_ip": "192.168.1.5", "dst_ip": "93.184.216.34", "src_port": 55555, "dst_port": 80, "protocol": "TCP", "packet_size": 60, "is_syn": True, "is_ack": False, "is_fin": False, "is_rst": False, "seq": 100},
        {"time": 1.1, "src_ip": "192.168.1.5", "dst_ip": "93.184.216.34", "src_port": 55555, "dst_port": 80, "protocol": "TCP", "packet_size": 500, "is_syn": False, "is_ack": True, "is_fin": False, "is_rst": False, "seq": 101},
        {"time": 1.5, "src_ip": "192.168.1.5", "dst_ip": "93.184.216.34", "src_port": 55555, "dst_port": 80, "protocol": "TCP", "packet_size": 54, "is_syn": False, "is_ack": True, "is_fin": True, "is_rst": False, "seq": 601},
    ]
    for p in packets_conn1:
        flow = tracker.add_packet(p)
    assert flow["num_connections"] == 1

    # Connection 2 on same 5-tuple at t=10.0 (new SYN with seq 9000)
    packets_conn2 = [
        {"time": 10.0, "src_ip": "192.168.1.5", "dst_ip": "93.184.216.34", "src_port": 55555, "dst_port": 80, "protocol": "TCP", "packet_size": 60, "is_syn": True, "is_ack": False, "is_fin": False, "is_rst": False, "seq": 9000},
        {"time": 10.1, "src_ip": "192.168.1.5", "dst_ip": "93.184.216.34", "src_port": 55555, "dst_port": 80, "protocol": "TCP", "packet_size": 800, "is_syn": False, "is_ack": True, "is_fin": False, "is_rst": False, "seq": 9001},
    ]
    for p in packets_conn2:
        flow = tracker.add_packet(p)

    assert flow["num_connections"] == 2
    assert flow["packet_count"] == 5


def test_tcp_mid_capture_flow():
    """
    TC-04: Flow begins mid-capture (first seen packet is data/ACK, no SYN).
    Expected: num_connections == 1, state gracefully established.
    """
    tracker = FlowTracker()

    packets = [
        {"time": 50.0, "src_ip": "10.1.1.1", "dst_ip": "10.2.2.2", "src_port": 60000, "dst_port": 443, "protocol": "TCP", "packet_size": 1400, "is_syn": False, "is_ack": True, "is_fin": False, "is_rst": False, "seq": 50000},
        {"time": 50.1, "src_ip": "10.1.1.1", "dst_ip": "10.2.2.2", "src_port": 60000, "dst_port": 443, "protocol": "TCP", "packet_size": 1400, "is_syn": False, "is_ack": True, "is_fin": False, "is_rst": False, "seq": 51400},
        {"time": 50.2, "src_ip": "10.1.1.1", "dst_ip": "10.2.2.2", "src_port": 60000, "dst_port": 443, "protocol": "TCP", "packet_size": 54, "is_syn": False, "is_ack": True, "is_fin": True, "is_rst": False, "seq": 52800},
    ]
    for p in packets:
        flow = tracker.add_packet(p)

    assert flow["num_connections"] == 1
    assert flow["packet_count"] == 3


# -----------------------------------------------------------------------------
# UDP TESTS
# -----------------------------------------------------------------------------

def test_udp_within_idle_timeout():
    """
    TC-05: UDP datagram stream with inter-arrival intervals <= 5.0s.
    Expected: num_connections == 1.
    """
    tracker = FlowTracker(udp_idle_timeout=5.0)

    packets = [
        {"time": 1.0, "src_ip": "192.168.1.10", "dst_ip": "8.8.8.8", "src_port": 53535, "dst_port": 53, "protocol": "UDP", "packet_size": 120},
        {"time": 3.0, "src_ip": "192.168.1.10", "dst_ip": "8.8.8.8", "src_port": 53535, "dst_port": 53, "protocol": "UDP", "packet_size": 120},
        {"time": 6.5, "src_ip": "192.168.1.10", "dst_ip": "8.8.8.8", "src_port": 53535, "dst_port": 53, "protocol": "UDP", "packet_size": 120},
    ]
    for p in packets:
        flow = tracker.add_packet(p)

    assert flow["num_connections"] == 1
    assert flow["packet_count"] == 3


def test_udp_exceeding_idle_timeout():
    """
    TC-06: UDP datagram stream with an idle gap > 5.0s between packet 2 and packet 3.
    Expected: num_connections == 2.
    """
    tracker = FlowTracker(udp_idle_timeout=5.0)

    packets = [
        {"time": 1.0, "src_ip": "192.168.1.10", "dst_ip": "8.8.8.8", "src_port": 53535, "dst_port": 53, "protocol": "UDP", "packet_size": 120},
        {"time": 2.5, "src_ip": "192.168.1.10", "dst_ip": "8.8.8.8", "src_port": 53535, "dst_port": 53, "protocol": "UDP", "packet_size": 120},
        # 8.0s gap (> 5.0s)
        {"time": 10.5, "src_ip": "192.168.1.10", "dst_ip": "8.8.8.8", "src_port": 53535, "dst_port": 53, "protocol": "UDP", "packet_size": 120},
    ]
    for p in packets:
        flow = tracker.add_packet(p)

    assert flow["num_connections"] == 2
    assert flow["packet_count"] == 3


# -----------------------------------------------------------------------------
# DISTINCT COUNTS & FEATURE SCHEMA TESTS
# -----------------------------------------------------------------------------

def test_packet_count_distinct_from_num_connections():
    """
    TC-08: A high-packet-count TCP flow (100 packets) must NOT substitute packet_count for num_connections.
    Expected: packet_count == 100, num_connections == 1.
    """
    tracker = FlowTracker()

    # Initial SYN
    tracker.add_packet({"time": 0.0, "src_ip": "10.0.0.1", "dst_ip": "10.0.0.2", "src_port": 12345, "dst_port": 80, "protocol": "TCP", "packet_size": 60, "is_syn": True, "is_ack": False, "seq": 1})
    # 99 data packets
    for i in range(1, 100):
        flow = tracker.add_packet({"time": i * 0.1, "src_ip": "10.0.0.1", "dst_ip": "10.0.0.2", "src_port": 12345, "dst_port": 80, "protocol": "TCP", "packet_size": 1000, "is_syn": False, "is_ack": True, "seq": i * 1000})

    assert flow["packet_count"] == 100
    assert flow["num_connections"] == 1
    assert flow["packet_count"] != flow["num_connections"]

    # Extract features and verify both fields
    session_tracker = SessionTracker()
    session = session_tracker.add_flow(flow)
    features = extract_features(session)

    assert features["packet_count"] == 100
    assert features["num_connections"] == 1
    assert features["requests_per_sec"] == pytest.approx(100 / 9.9, rel=1e-3)
    assert features["session_duration"] == pytest.approx(9.9, rel=1e-3)


def test_feature_extraction_edge_cases():
    """
    Validates feature extraction on edge cases:
    - Single packet (duration = 0)
    - Empty packet sizes / timestamps
    - Exact 9 contract fields presence
    """
    # Edge case 1: Single packet flow
    single_pkt_session = {
        "session_id": "PC01_S1",
        "first_seen": 100.0,
        "last_seen": 100.0,
        "packet_count": 1,
        "total_bytes": 500,
        "packet_sizes": [500],
        "timestamps": [100.0],
        "protocol": "TCP",
        "num_connections": 1,
    }
    feats1 = extract_features(single_pkt_session)
    assert feats1["session_duration"] == 0.0
    assert feats1["requests_per_sec"] == 0.0
    assert feats1["packet_size_mean"] == 500.0
    assert feats1["packet_size_var"] == 0.0
    assert feats1["request_interval_mean"] == 0.0
    assert feats1["request_interval_var"] == 0.0
    assert feats1["num_connections"] == 1
    assert feats1["protocol"] == "TCP"

    # Edge case 2: Empty session
    empty_session = {
        "session_id": "PC01_S2",
        "first_seen": 0.0,
        "last_seen": 0.0,
        "packet_count": 0,
        "total_bytes": 0,
        "packet_sizes": [],
        "timestamps": [],
        "protocol": "UDP",
        "num_connections": 1,
    }
    feats2 = extract_features(empty_session)
    assert feats2["session_duration"] == 0.0
    assert feats2["requests_per_sec"] == 0.0
    assert feats2["packet_size_mean"] == 0.0
    assert feats2["packet_size_var"] == 0.0
    assert feats2["request_interval_mean"] == 0.0
    assert feats2["request_interval_var"] == 0.0
    assert feats2["num_connections"] == 1
    assert feats2["protocol"] == "UDP"

    # Verify all 9 required AI Contract fields exist
    required_contract_fields = [
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
    for field in required_contract_fields:
        assert field in feats1, f"Missing required contract field: {field}"
        assert field in feats2, f"Missing required contract field: {field}"


if __name__ == "__main__":
    test_tcp_normal_handshake_and_close()
    test_tcp_syn_retransmission_deduplication()
    test_tcp_5tuple_reuse_after_close()
    test_tcp_mid_capture_flow()
    test_udp_within_idle_timeout()
    test_udp_exceeding_idle_timeout()
    test_packet_count_distinct_from_num_connections()
    test_feature_extraction_edge_cases()
    print("ALL CONNECTION COUNTING & FEATURE TESTS PASSED SUCCESSFULLY!")
