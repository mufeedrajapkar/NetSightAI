import statistics


def extract_features(session):

    timestamps = session["timestamps"]
    packet_sizes = session["packet_sizes"]

    # Session duration
    duration = session["last_seen"] - session["first_seen"]

    # Avoid division by zero
    if duration > 0:
        packets_per_sec = session["packet_count"] / duration
    else:
        packets_per_sec = 0

    # Packet size statistics
    if packet_sizes:
        packet_size_mean = statistics.mean(packet_sizes)
        packet_size_var = statistics.pvariance(packet_sizes)
    else:
        packet_size_mean = 0
        packet_size_var = 0

    # Packet interval statistics
    if len(timestamps) > 1:
        intervals = [
            timestamps[i] - timestamps[i - 1]
            for i in range(1, len(timestamps))
        ]

        packet_interval_mean = statistics.mean(intervals)
        packet_interval_var = statistics.pvariance(intervals)

    else:
        packet_interval_mean = 0
        packet_interval_var = 0

    return {
        "session_id": session["session_id"],
        "session_duration": duration,
        "packets_per_sec": packets_per_sec,
        "packet_size_mean": packet_size_mean,
        "packet_size_var": packet_size_var,
        "packet_interval_mean": packet_interval_mean,
        "packet_interval_var": packet_interval_var,
        "bytes_transferred": session["total_bytes"],
        "packet_count": session["packet_count"],
        "protocol": session["protocol"]
    }