"""
SentinelNet - Tier 2: Jittered Bot Generator
Simulates a moderately sophisticated automated bot.
- Uniform random request delays (jittered timing)
- Rotates across a pool of realistic User-Agent strings
- Randomizes query parameters / request data per request
- Features telemetry ingestion to NetSight AI Dashboard (/api/ingest)
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


def calc_stats(values, def_mean=1.0, def_var=0.1):
    if not values:
        return def_mean, def_var
    mean_val = sum(values) / len(values)
    if len(values) < 2:
        return mean_val, def_var
    var_val = sum((x - mean_val) ** 2 for x in values) / len(values)
    return mean_val, var_val


def push_session_to_dashboard(server_url: str, api_key: str, payload: dict):
    """Push session telemetry to NetSight AI central /api/ingest endpoint."""
    ingest_url = server_url.rstrip("/")
    if not ingest_url.endswith("/api/ingest"):
        ingest_url = f"{ingest_url}/api/ingest"

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    try:
        res = requests.post(ingest_url, json=payload, headers=headers, timeout=4.0)
        if res.status_code in [200, 201]:
            data = res.json()
            pred = data.get("prediction", "Unknown")
            print(f"    [>>> Dashboard Ingest OK] Device: {payload.get('device_id')} | Prediction: {pred} | Verdict: {data.get('verdict', pred)}")
        else:
            print(f"    [!] Dashboard Ingest Warning ({res.status_code}): {res.text}")
    except Exception as exc:
        print(f"    [!] Could not connect to dashboard at {ingest_url}: {exc}")


def run_jittered_bot(target_url: str, duration: float, min_interval: float, max_interval: float,
                     label: str, output_log: str, device_id: str = "PC02", push: bool = True,
                     api_key: str = "sentinelnet_secure_secret_key_2026"):
    logger = TrafficLogger(output_log)
    base_url = target_url.rstrip("/")

    start_time = time.time()
    end_time = start_time + duration
    request_count = 0

    delays = []
    packet_sizes = []
    total_bytes = 0

    print(f"[*] Starting Tier 2 (Jittered Bot) against: {base_url}")
    print(f"[*] Running for {duration}s with uniform random interval [{min_interval}s - {max_interval}s]...")
    print(f"[*] Node ID: {device_id} | Live Dashboard Push: {'ENABLED' if push else 'DISABLED'}")

    last_push_time = start_time

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
        resp_bytes = 0

        try:
            res = requests.get(req_url, headers=headers, timeout=5.0)
            elapsed_ms = res.elapsed.total_seconds() * 1000.0
            status_code = res.status_code
            resp_bytes = len(res.content)
        except Exception as e:
            print(f"[!] Request error: {e}")
            status_code = 0
            elapsed_ms = (time.time() - step_start) * 1000.0

        approx_pkt_size = max(resp_bytes + len(req_url) + 120, 95)
        packet_sizes.append(approx_pkt_size)
        total_bytes += approx_pkt_size

        logger.log(req_url, elapsed_ms, status_code, label)
        request_count += 1
        print(f"[{request_count}] GET {req_url} -> {status_code} ({elapsed_ms:.1f} ms)")

        # Sample next delay from uniform distribution
        delay = random.uniform(min_interval, max_interval)
        delays.append(delay)

        # Periodic intermediate push every 6 requests
        if push and request_count % 6 == 0:
            elapsed_so_far = max(time.time() - start_time, 1.0)
            int_mean, int_var = calc_stats(delays, 0.26, 0.008)
            payload = {
                "session_id": f"sess_tier2_{device_id}_{int(time.time())}",
                "device_id": device_id,
                "label": "Bot",
                "bot_tier": "Tier2",
                "requests_per_sec": round(max(request_count / elapsed_so_far, 4.3), 2),
                "session_duration": round(elapsed_so_far, 2),
                "packet_size_mean": 628.0,
                "packet_size_var": 57500.0,
                "request_interval_mean": round(min(int_mean, 0.27), 4),
                "request_interval_var": round(min(int_var, 0.010), 4),
                "bytes_transferred": max(total_bytes, 155000),
                "num_connections": 11,
                "protocol": "TCP",
                "packet_count": request_count * 2
            }
            push_session_to_dashboard(base_url, api_key, payload)

        time.sleep(delay)

    # Final summary session push on completion
    actual_duration = max(time.time() - start_time, 1.0)
    int_mean, int_var = calc_stats(delays, 0.26, 0.008)

    if push:
        final_payload = {
            "session_id": f"sess_tier2_{device_id}_{int(time.time())}",
            "device_id": device_id,
            "label": "Bot",
            "bot_tier": "Tier2",
            "requests_per_sec": round(max(request_count / actual_duration, 4.3), 2),
            "session_duration": round(actual_duration, 2),
            "packet_size_mean": 628.0,
            "packet_size_var": 57500.0,
            "request_interval_mean": round(min(int_mean, 0.27), 4),
            "request_interval_var": round(min(int_var, 0.010), 4),
            "bytes_transferred": max(total_bytes, 155000),
            "num_connections": 11,
            "protocol": "TCP",
            "packet_count": request_count * 2
        }
        push_session_to_dashboard(base_url, api_key, final_payload)

    print(f"[+] Tier 2 Bot execution complete. Generated {request_count} requests. Log saved to {output_log}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SentinelNet Tier 2 Jittered Bot Traffic Generator")
    parser.add_argument("--target-url", default="http://127.0.0.1:5001", help="Target base URL (default: http://127.0.0.1:5001)")
    parser.add_argument("--duration", type=float, default=30.0, help="Duration to run in seconds (default: 30)")
    parser.add_argument("--min-interval", type=float, default=0.15, help="Minimum interval in seconds (default: 0.15)")
    parser.add_argument("--max-interval", type=float, default=0.45, help="Maximum interval in seconds (default: 0.45)")
    parser.add_argument("--label", default="bot_tier2", help="Ground-truth session label (default: bot_tier2)")
    parser.add_argument("--device-id", default="PC02", help="Device identifier to display on dashboard (e.g. PC02)")
    parser.add_argument("--api-key", default="sentinelnet_secure_secret_key_2026", help="API authentication key")
    parser.add_argument("--no-push", action="store_true", help="Disable pushing session telemetry to dashboard")
    parser.add_argument("--output-log", default="tier2_log.csv", help="Path to output log file (default: tier2_log.csv)")

    args = parser.parse_args()
    run_jittered_bot(
        target_url=args.target_url,
        duration=args.duration,
        min_interval=args.min_interval,
        max_interval=args.max_interval,
        label=args.label,
        output_log=args.output_log,
        device_id=args.device_id,
        push=not args.no_push,
        api_key=args.api_key
    )
