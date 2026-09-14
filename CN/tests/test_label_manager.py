from CN.agent.label_manager import LabelManager


features = {
    "session_id": 1,
    "session_duration": 4.0,
    "packets_per_sec": 1.0,
    "packet_size_mean": 600,
    "packet_size_var": 5000,
    "packet_interval_mean": 1.33,
    "packet_interval_var": 0.05,
    "bytes_transferred": 2400,
    "packet_count": 4,
    "protocol": "TCP"
}


label_manager = LabelManager(
    device_id="PC01",
    label="Bot",
    bot_tier="Tier2"
)


labeled_features = label_manager.add_labels(features)


print("Label Manager Test")
print("------------------")

for key, value in labeled_features.items():
    print(f"{key}: {value}")