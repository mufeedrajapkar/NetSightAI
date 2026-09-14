from CN.agent.features import extract_features


session = {
    "session_id": 1,
    "first_seen": 1000.0,
    "last_seen": 1004.0,
    "packet_count": 4,
    "total_bytes": 2400,
    "packet_sizes": [500, 600, 700, 600],
    "timestamps": [1000.0, 1001.0, 1002.5, 1004.0],
    "protocol": "TCP"
}


features = extract_features(session)


print("Feature Extraction Test")
print("-----------------------")

for key, value in features.items():
    print(f"{key}: {value}")