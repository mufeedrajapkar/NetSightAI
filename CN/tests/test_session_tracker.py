from CN.agent.session.session_tracker import SessionTracker


tracker = SessionTracker(timeout=5)


flow = {
    "flow_key": (
        ("192.168.1.10", 52143),
        ("142.250.183.14", 443),
        "TCP"
    ),
    "first_seen": 1000.0,
    "last_seen": 1002.0,
    "packet_count": 10,
    "total_bytes": 5000,
    "packet_sizes": [500, 600, 400],
    "timestamps": [1000.0, 1001.0, 1002.0],
    "protocol": "TCP"
}


session = tracker.add_flow(flow)

print("Session Tracker Test")
print("--------------------")
print("Session ID:", session["session_id"])
print("Packets:", session["packet_count"])
print("Bytes:", session["total_bytes"])
print("Protocol:", session["protocol"])

active = tracker.get_active_sessions(current_time=1004.0)

print("Active sessions:", len(active))