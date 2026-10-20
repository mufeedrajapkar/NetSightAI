import os
import pytest
from CN.agent.csv_writer import save_to_csv, FIELDS
from CN.agent.features import extract_features
from CN.agent.label_manager import LabelManager


def test_save_to_csv_legacy_dict(tmp_path):
    legacy_features = {
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
    csv_file = str(tmp_path / "legacy.csv")
    save_to_csv(legacy_features, filename=csv_file)
    assert os.path.exists(csv_file)


def test_save_to_csv_real_extracted_features(tmp_path):
    session = {
        "session_id": "sess_real_01",
        "timestamps": [100.0, 100.2, 100.5, 101.0],
        "packet_sizes": [64, 128, 256, 512],
        "first_seen": 100.0,
        "last_seen": 101.0,
        "packet_count": 4,
        "total_bytes": 960,
        "protocol": "TCP",
        "num_connections": 2,
    }
    raw_features = extract_features(session)
    lm = LabelManager(device_id="PC01", label="Human", bot_tier="None")
    labeled_features = lm.add_labels(raw_features)

    csv_file = str(tmp_path / "real_output.csv")
    save_to_csv(labeled_features, filename=csv_file)

    assert os.path.exists(csv_file)
    with open(csv_file, "r") as f:
        lines = f.readlines()
    assert len(lines) == 2
    assert "num_connections" in lines[0]
    assert "requests_per_sec" in lines[0]
    assert "sess_real_01" in lines[1]