"""
SentinelNet - Tier 2: Jittered Bot Generator
Simulates a moderately sophisticated automated bot.
- Uniform random request delays (jittered timing)
- Rotates across a pool of realistic User-Agent strings
- Randomizes query parameters / request data per request
"""

import time
import random
import argparse
import requests
from logger_utils import TrafficLogger

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 14; Mobile; rv:128.0) Gecko/128.0 Firefox/128.0"
]

SEARCH_QUERIES = ["network", "packet", "security", "ai", "classifier", "sentinel", "firewall", "router", "protocol"]

def run_jittered_bot(target_url: str, duration: float, min_interval: float, max_interval: float, label: str, output_log: str):
    logger = TrafficLogger(output_log)
    base_url = target_url.rstrip("/")

    start_time = time.time()
    end_time = start_time + duration
    request_count = 0

    print(f"[*] Starting Tier 2 (Jittered Bot) against base target: {base_url}")
    print(f"[*] Running for {duration}s with uniform random interval [{min_interval}s - {max_interval}s]...")

    while time.time() < end_time:
        step_start = time.time()
        user_agent = random.choice(USER_AGENTS)
        headers = {"User-Agent": user_agent}

        # Randomize endpoint query parameters
        query_param = random.choice(SEARCH_QUERIES)
        random_id = random.randint(1, 500)
        req_url = f"{base_url}/search?q={query_param}&ref={random_id}"

        status_code = -1
        elapsed_ms = 0.0

        try:
            res = requests.get(req_url, headers=headers, timeout=5.0)
            elapsed_ms = res.elapsed.total_seconds() * 1000.0
            status_code = res.status_code
        except Exception as e:
            print(f"[!] Request error: {e}")
            status_code = 0
            elapsed_ms = (time.time() - step_start) * 1000.0

        logger.log(req_url, elapsed_ms, status_code, label)
        request_count += 1
        print(f"[{request_count}] GET {req_url} -> {status_code} ({elapsed_ms:.1f} ms)")

        # Sample next delay from uniform distribution
        delay = random.uniform(min_interval, max_interval)
        time.sleep(delay)

    print(f"[+] Tier 2 Bot execution complete. Generated {request_count} requests. Log saved to {output_log}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SentinelNet Tier 2 Jittered Bot Traffic Generator")
    parser.add_argument("--target-url", default="http://127.0.0.1:5000", help="Target base URL (default: http://127.0.0.1:5000)")
    parser.add_argument("--duration", type=float, default=30.0, help="Duration to run in seconds (default: 30)")
    parser.add_argument("--min-interval", type=float, default=0.2, help="Minimum interval in seconds (default: 0.2)")
    parser.add_argument("--max-interval", type=float, default=2.0, help="Maximum interval in seconds (default: 2.0)")
    parser.add_argument("--label", default="bot_tier2", help="Ground-truth session label (default: bot_tier2)")
    parser.add_argument("--output-log", default="tier2_log.csv", help="Path to output log file (default: tier2_log.csv)")

    args = parser.parse_args()
    run_jittered_bot(args.target_url, args.duration, args.min_interval, args.max_interval, args.label, args.output_log)
