"""
SentinelNet - Human Traffic & Inter-Arrival Timing Recorder
Interactive utility that allows a real human operator to perform manual web actions against the test server.
Measures inter-arrival times between manual requests and exports timing data for Tier 3 sampling.
"""

import time
import argparse
import random
import requests
from logger_utils import TrafficLogger

ENDPOINTS = [
    ("/", "GET", None),
    ("/search?q=network", "GET", None),
    ("/search?q=security", "GET", None),
    ("/product/101", "GET", None),
    ("/product/102", "GET", None),
    ("/api/data", "GET", None),
    ("/login", "POST", {"username": "human_operator"})
]

def run_human_recorder(target_url: str, output_intervals: str, output_log: str, label: str):
    base_url = target_url.rstrip("/")
    logger = TrafficLogger(output_log)
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RealHumanOperator/1.0"
    headers = {"User-Agent": user_agent}

    print("==========================================================")
    print("       SentinelNet Human Traffic Recorder                 ")
    print("==========================================================")
    print(f"[*] Target Server: {base_url}")
    print(f"[*] Output Intervals CSV: {output_intervals}")
    print(f"[*] Output Traffic Log: {output_log}")
    print("----------------------------------------------------------")
    print("Instructions:")
    print("  - Press [ENTER] to trigger a manual request step.")
    print("  - Type 'q' and press [ENTER] to stop recording.")
    print("----------------------------------------------------------")

    last_request_time = None
    recorded_intervals = []
    request_count = 0

    input("\nPress [ENTER] to start human session recording...")
    session_start = time.time()
    last_request_time = session_start

    while True:
        prompt = input(f"\n[Req #{request_count + 1}] Press [ENTER] for next manual request (or 'q' to quit): ")
        if prompt.strip().lower() == 'q':
            break

        now = time.time()
        inter_arrival_sec = round(now - last_request_time, 3)
        last_request_time = now

        if request_count > 0:
            recorded_intervals.append(inter_arrival_sec)
            print(f"    [+] Recorded Inter-Arrival Delay: {inter_arrival_sec} seconds")

        # Select endpoint to hit
        endpoint_idx = request_count % len(ENDPOINTS)
        path, method, payload = ENDPOINTS[endpoint_idx]
        full_url = f"{base_url}{path}"

        step_start = time.time()
        status_code = -1
        elapsed_ms = 0.0

        try:
            if method == "POST":
                res = requests.post(full_url, json=payload, headers=headers, timeout=5.0)
            else:
                res = requests.get(full_url, headers=headers, timeout=5.0)

            elapsed_ms = res.elapsed.total_seconds() * 1000.0
            status_code = res.status_code
        except Exception as e:
            print(f"    [!] Error sending request: {e}")
            status_code = 0
            elapsed_ms = (time.time() - step_start) * 1000.0

        logger.log(full_url, elapsed_ms, status_code, label)
        request_count += 1
        print(f"    [>] Sent {method} {full_url} -> Status {status_code} ({elapsed_ms:.1f} ms)")

    # Save recorded inter-arrival float values to CSV
    if recorded_intervals:
        with open(output_intervals, "a", encoding="utf-8") as f:
            for delay in recorded_intervals:
                f.write(f"{delay}\n")

        print("\n==========================================================")
        print(f"[+] Recording complete! Saved {len(recorded_intervals)} human intervals to {output_intervals}")
        print(f"[+] Ground-truth traffic log saved to {output_log}")
        print("==========================================================")
    else:
        print("[!] No inter-arrival intervals recorded (at least 2 requests needed).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SentinelNet Human Traffic & Inter-Arrival Recorder")
    parser.add_argument("--target-url", default="http://127.0.0.1:5000", help="Target base URL (default: http://127.0.0.1:5000)")
    parser.add_argument("--output-intervals", default="human_intervals.csv", help="CSV path to append recorded inter-arrival delays (default: human_intervals.csv)")
    parser.add_argument("--output-log", default="human_log.csv", help="Traffic log path (default: human_log.csv)")
    parser.add_argument("--label", default="human", help="Ground-truth session label (default: human)")

    args = parser.parse_args()
    run_human_recorder(args.target_url, args.output_intervals, args.output_log, args.label)
