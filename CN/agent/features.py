import statistics


def extract_features(session):
    """
    Extract flow/session level behavioural statistical features.

    Returns a dictionary containing:
      - The 9 features expected by the AI classification contract:
        (requests_per_sec, session_duration, packet_size_mean, packet_size_var,
         request_interval_mean, request_interval_var, bytes_transferred,
         num_connections, protocol)
      - CN module metadata and backward-compatible aliases:
        (session_id, packet_count, packets_per_sec, packet_interval_mean,
         packet_interval_var)
    """
    timestamps = session.get("timestamps", [])
    packet_sizes = session.get("packet_sizes", [])
    first_seen = session.get("first_seen", 0.0)
    last_seen = session.get("last_seen", first_seen)
    packet_count = session.get("packet_count", len(timestamps))
    total_bytes = session.get("total_bytes", sum(packet_sizes) if packet_sizes else 0)
    protocol = session.get("protocol", "OTHER")
    num_connections = session.get("num_connections", 1)

    # Session duration
    duration = float(last_seen - first_seen) if (last_seen is not None and first_seen is not None) else 0.0
    if duration < 0.0:
        duration = 0.0

    # Packet transmission rate (packets/sec)
    # Note: In the AI contract this is labeled requests_per_sec (packet-level transmission rate).
    if duration > 0.0:
        packets_per_sec = float(packet_count / duration)
    else:
        packets_per_sec = 0.0

    # Packet size statistics
    if not packet_sizes:
        packet_size_mean = 0.0
        packet_size_var = 0.0
    elif len(packet_sizes) == 1:
        packet_size_mean = float(packet_sizes[0])
        packet_size_var = 0.0
    else:
        packet_size_mean = float(statistics.mean(packet_sizes))
        packet_size_var = float(statistics.pvariance(packet_sizes))

    # Packet interval statistics (inter-packet arrival timing)
    # Note: In the AI contract this is labeled request_interval_mean / request_interval_var.
    if len(timestamps) > 1:
        intervals = [
            float(timestamps[i] - timestamps[i - 1])
            for i in range(1, len(timestamps))
        ]
        if len(intervals) == 1:
            packet_interval_mean = float(intervals[0])
            packet_interval_var = 0.0
        else:
            packet_interval_mean = float(statistics.mean(intervals))
            packet_interval_var = float(statistics.pvariance(intervals))
    else:
        packet_interval_mean = 0.0
        packet_interval_var = 0.0

    return {
        # AI Contract standard 9 features
        "requests_per_sec": packets_per_sec,
        "session_duration": duration,
        "packet_size_mean": packet_size_mean,
        "packet_size_var": packet_size_var,
        "request_interval_mean": packet_interval_mean,
        "request_interval_var": packet_interval_var,
        "bytes_transferred": total_bytes,
        "num_connections": num_connections,
        "protocol": protocol,

        # CN Module metadata and backward-compatible aliases
        "session_id": session.get("session_id", "UNKNOWN"),
        "packet_count": packet_count,
        "packets_per_sec": packets_per_sec,
        "packet_interval_mean": packet_interval_mean,
        "packet_interval_var": packet_interval_var,
    }