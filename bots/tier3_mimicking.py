"""
SentinelNet - Tier 3: Human-Mimicking Bot Generator
Simulates advanced bot behavior designed to mimic human browsing behavior:
- Samples inter-arrival delays directly from an empirical human dataset (resampling with replacement)
- Periodically inserts human "reading/thinking" pauses (e.g., 5% chance of 5-15s delay)
- Simulates realistic multi-step browsing session flows (Home -> Search -> Product -> Login)
- Rotates realistic User-Agent headers across session flows
"""

import os
import time
import random
import argparse
import csv
import json
import requests
from logger_utils import TrafficLogger

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
]

def load_empirical_intervals(filepath: str) -> list[float]:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Empirical human intervals file '{filepath}' does not exist.")

    intervals = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                continue
            try:
                # Handle single floats or CSV row values
                val = float(line_str.split(",")[0])
                if val > 0:
                    intervals.append(val)
            except ValueError:
                print(f"[!] Warning: Skipping invalid float on line {line_num} in '{filepath}': '{line_str}'")
                continue

    if not intervals:
        raise ValueError(f"Empirical human intervals file '{filepath}' contains no valid positive float values.")

    return intervals

def get_next_session_action(base_url: str, session_step: int) -> tuple[str, str, dict]:
    """
    Generates plausible browsing step sequence:
    0: Home page GET /
    1: Search GET /search?q=...
    2: Product GET /product/<id>
    3: API GET /api/data
    4: Login POST /login
    """
    step = session_step % 5
    method = "GET"
    payload = None

    if step == 0:
        url = f"{base_url}/"
    elif step == 1:
        query = random.choice(["security", "analysis", "sentinel", "firewall", "logs"])
        url = f"{base_url}/search?q={query}"
    elif step == 2:
        prod_id = random.choice([101, 102, 103, 201, 205])
        url = f"{base_url}/product/{prod_id}"
    elif step == 3:
        url = f"{base_url}/api/data"
    else:
        url = f"{base_url}/login"
        method = "POST"
        payload = {"username": "researcher_user", "client_version": "1.0"}

    return method, url, payload

def run_mimicking_bot(
    target_url: str,
    duration: float,
    intervals_file: str,
    pause_chance: float,
    pause_min: float,
    pause_max: float,
    label: str,
    output_log: str
):
    logger = TrafficLogger(output_log)
    base_url = target_url.rstrip("/")
    empirical_intervals = load_empirical_intervals(intervals_file)

    session_user_agent = random.choice(USER_AGENTS)
    headers = {
        "User-Agent": session_user_agent,
        "Accept": "text/html,application/json,*/*",
        "Accept-Language": "en-US,en;q=0.9"
    }

    start_time = time.time()
    end_time = start_time + duration
    request_count = 0
    session_step = 0

    print(f"[*] Starting Tier 3 (Human-Mimicking Bot) against target base: {base_url}")
    print(f"[*] Loaded {len(empirical_intervals)} empirical human inter-arrival intervals from {intervals_file}")
    print(f"[*] Pause probability: {pause_chance*100:.1f}% ({pause_min}s - {pause_max}s)")
    print(f"[*] Session User-Agent: {session_user_agent[:45]}...")

    while time.time() < end_time:
        step_start = time.time()
        method, req_url, payload = get_next_session_action(base_url, session_step)

        status_code = -1
        elapsed_ms = 0.0

        try:
            if method == "POST":
                res = requests.post(req_url, json=payload, headers=headers, timeout=5.0)
            else:
                res = requests.get(req_url, headers=headers, timeout=5.0)

            elapsed_ms = res.elapsed.total_seconds() * 1000.0
            status_code = res.status_code
        except Exception as e:
            print(f"[!] Request error: {e}")
            status_code = 0
            elapsed_ms = (time.time() - step_start) * 1000.0

        logger.log(req_url, elapsed_ms, status_code, label)
        request_count += 1
        session_step += 1
        print(f"[{request_count}] {method} {req_url} -> {status_code} ({elapsed_ms:.1f} ms)")

        # Decide delay: check for human think time pause vs empirical sampling
        if random.random() < pause_chance:
            delay = random.uniform(pause_min, pause_max)
            print(f"    [~] Simulated Human Thinking/Reading Pause: {delay:.2f}s")
        else:
            delay = random.choice(empirical_intervals)

        time.sleep(delay)

        # Periodically reset session context (simulate new session every ~10 requests)
        if session_step % 10 == 0:
            session_user_agent = random.choice(USER_AGENTS)
            headers["User-Agent"] = session_user_agent

    print(f"[+] Tier 3 Bot execution complete. Generated {request_count} requests. Log saved to {output_log}")

import sys

DEFAULT_INTERVALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "human_intervals.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SentinelNet Tier 3 Human-Mimicking Bot Traffic Generator")
    parser.add_argument("--target-url", default="http://127.0.0.1:5000", help="Target base URL (default: http://127.0.0.1:5000)")
    parser.add_argument("--duration", type=float, default=60.0, help="Duration to run in seconds (default: 60)")
    parser.add_argument("--intervals-file", default=DEFAULT_INTERVALS_FILE, help=f"Path to empirical human inter-arrival CSV (default: {DEFAULT_INTERVALS_FILE})")
    parser.add_argument("--pause-chance", type=float, default=0.05, help="Probability of long think pause (default: 0.05)")
    parser.add_argument("--pause-min", type=float, default=5.0, help="Min long pause duration in seconds (default: 5.0)")
    parser.add_argument("--pause-max", type=float, default=15.0, help="Max long pause duration in seconds (default: 15.0)")
    parser.add_argument("--label", default="bot_tier3", help="Ground-truth session label (default: bot_tier3)")
    parser.add_argument("--output-log", default="tier3_log.csv", help="Path to output log file (default: tier3_log.csv)")

    args = parser.parse_args()
    try:
        run_mimicking_bot(
            args.target_url,
            args.duration,
            args.intervals_file,
            args.pause_chance,
            args.pause_min,
            args.pause_max,
            args.label,
            args.output_log
        )
    except (FileNotFoundError, ValueError) as err:
        print(f"[!] ERROR: {err}", file=sys.stderr)
        sys.exit(1)

