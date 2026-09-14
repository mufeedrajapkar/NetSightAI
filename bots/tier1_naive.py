"""
SentinelNet - Tier 1: Naive Bot Generator
Simulates a simplistic automated bot targeting a single URL at fixed time intervals.
- Fixed inter-request delay
- Hardcoded single User-Agent string
- Deterministic behavior (trivially detectable)
"""

import time
import argparse
import requests
from logger_utils import TrafficLogger

HARDCODED_USER_AGENT = "SentinelNet-NaiveBot/1.0 (Fixed-Interval Synthetic Traffic Engine)"

def run_naive_bot(target_url: str, duration: float, interval: float, label: str, output_log: str):
    logger = TrafficLogger(output_log)
    headers = {"User-Agent": HARDCODED_USER_AGENT}
    
    start_time = time.time()
    end_time = start_time + duration
    request_count = 0

    print(f"[*] Starting Tier 1 (Naive Bot) against target: {target_url}")
    print(f"[*] Running for {duration}s with fixed interval {interval}s...")

    while time.time() < end_time:
        step_start = time.time()
        status_code = -1
        elapsed_ms = 0.0

        try:
            res = requests.get(target_url, headers=headers, timeout=5.0)
            elapsed_ms = res.elapsed.total_seconds() * 1000.0
            status_code = res.status_code
        except Exception as e:
            print(f"[!] Request error: {e}")
            status_code = 0
            elapsed_ms = (time.time() - step_start) * 1000.0

        logger.log(target_url, elapsed_ms, status_code, label)
        request_count += 1
        print(f"[{request_count}] GET {target_url} -> {status_code} ({elapsed_ms:.1f} ms)")

        # Precise fixed sleep calculation to maintain constant frequency
        processing_time = time.time() - step_start
        sleep_time = max(0.0, interval - processing_time)
        time.sleep(sleep_time)

    print(f"[+] Tier 1 Bot execution complete. Generated {request_count} requests. Log saved to {output_log}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SentinelNet Tier 1 Naive Bot Traffic Generator")
    parser.add_argument("--target-url", default="http://127.0.0.1:5000/", help="Target URL (default: http://127.0.0.1:5000/)")
    parser.add_argument("--duration", type=float, default=30.0, help="Duration to run in seconds (default: 30)")
    parser.add_argument("--interval", type=float, default=0.5, help="Fixed interval between requests in seconds (default: 0.5)")
    parser.add_argument("--label", default="bot_tier1", help="Ground-truth session label (default: bot_tier1)")
    parser.add_argument("--output-log", default="tier1_log.csv", help="Path to output log file (default: tier1_log.csv)")

    args = parser.parse_args()
    run_naive_bot(args.target_url, args.duration, args.interval, args.label, args.output_log)
