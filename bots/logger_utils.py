"""
SentinelNet Traffic Logger Helper
Provides unified logging capabilities for CSV and JSON outputs.
"""

import os
import csv
import json
from datetime import datetime, timezone

class TrafficLogger:
    def __init__(self, log_filepath: str):
        self.log_filepath = log_filepath
        self.is_json = log_filepath.endswith(".json")
        
        # Ensure target directory exists
        os.makedirs(os.path.dirname(os.path.abspath(log_filepath)), exist_ok=True)
        
        if not self.is_json:
            # Initialize CSV header if file does not exist or is empty
            file_exists = os.path.exists(self.log_filepath) and os.path.getsize(self.log_filepath) > 0
            if not file_exists:
                with open(self.log_filepath, mode="w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["timestamp", "url", "response_time_ms", "status_code", "label"])

    def log(self, url: str, response_time_ms: float, status_code: int, label: str):
        iso_timestamp = datetime.now(timezone.utc).isoformat()
        
        if self.is_json:
            entry = {
                "timestamp": iso_timestamp,
                "url": url,
                "response_time_ms": round(response_time_ms, 2),
                "status_code": status_code,
                "label": label
            }
            logs = []
            if os.path.exists(self.log_filepath) and os.path.getsize(self.log_filepath) > 0:
                try:
                    with open(self.log_filepath, mode="r", encoding="utf-8") as f:
                        logs = json.load(f)
                except Exception:
                    logs = []
            logs.append(entry)
            with open(self.log_filepath, mode="w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2)
        else:
            with open(self.log_filepath, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([iso_timestamp, url, round(response_time_ms, 2), status_code, label])
