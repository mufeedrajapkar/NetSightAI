import csv
import os


FIELDS = [
    "session_id",
    "device_id",
    "session_duration",
    "packets_per_sec",
    "packet_size_mean",
    "packet_size_var",
    "packet_interval_mean",
    "packet_interval_var",
    "bytes_transferred",
    "packet_count",
    "protocol",
    "label",
    "bot_tier"
]


def save_to_csv(features, filename="sentinelnet_dataset.csv"):

    file_exists = os.path.exists(filename)

    with open(filename, "a", newline="") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDS
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(features)

    print(f"Saved session to {filename}")