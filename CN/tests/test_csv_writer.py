from CN.agent.csv_writer import save_to_csv


features = {
    "session_id": 1,
    "device_id": "PC01",
    "session_duration": 4.0,
    "packets_per_sec": 1.0,
    "packet_size_mean": 600,
    "packet_size_var": 5000,
    "packet_interval_mean": 1.33,
    "packet_interval_var": 0.05,
    "bytes_transferred": 2400,
    "packet_count": 4,
    "protocol": "TCP",
    "label": "Bot",
    "bot_tier": "Tier2"
}


save_to_csv(
    features,
    "test_dataset.csv"
)