"""
SentinelNet - Tier 4: Adversarial Delay & Feature Mimicking Bot
================================================================
Simulates an adversarial bot specifically crafted to evade machine learning
traffic classifiers by mimicking statistical properties of human traffic:

1. Delay Mimicking:
   Samples inter-request arrival intervals directly from the empirical Human
   distribution (mean ~0.81s, std ~0.51s, positive truncated).
2. Packet Size Shaping:
   Varies query string lengths and POST payload padding to generate packet
   sizes centered around the Human distribution (mean ~698B, std ~217B).
3. Session Dispersion:
   Distributes requests across diverse realistic web endpoints with realistic
   browser headers.

This demonstrates feature-space adversarial evasion where network timing
and volume statistics blend into the benign class.
"""

import os
import time
import random
import argparse
import string
import requests
import numpy as np

# Path resolution for logger_utils
try:
    from logger_utils import TrafficLogger
except ImportError:
    from bots.logger_utils import TrafficLogger

# Human baseline statistics from dataset (ai/CONTRACT.md & data/raw/sentinelnet_sample_500.csv)
HUMAN_INTERVAL_MEAN = 0.807
HUMAN_INTERVAL_STD = 0.513
HUMAN_PACKET_SIZE_MEAN = 698.0
HUMAN_PACKET_SIZE_STD = 217.0

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]

SEARCH_TOPICS = [
    "network-security", "deep-learning", "routing-protocols", "firewall-rules",
    "packet-inspection", "tls-fingerprint", "anomaly-detection", "flow-analysis"
]


def sample_human_delay(mean: float = HUMAN_INTERVAL_MEAN, std: float = HUMAN_INTERVAL_STD) -> float:
    """Sample inter-request delay from a log-normal distribution matching human stats."""
    # Compute lognormal parameters mu, sigma from target mean and variance
    var = std ** 2
    mu = np.log((mean ** 2) / np.sqrt(var + mean ** 2))
    sigma = np.sqrt(np.log(1.0 + (var / (mean ** 2))))
    val = float(np.random.lognormal(mu, sigma))
    return max(0.15, min(val, 6.0))


def generate_padded_query(target_size_mean: float = HUMAN_PACKET_SIZE_MEAN) -> str:
    """Generates query parameter with dynamic padding to shape request size."""
    topic = random.choice(SEARCH_TOPICS)
    # Estimate baseline HTTP overhead (~350 bytes), add padding
    padding_len = max(10, int(np.random.normal(target_size_mean - 350, 80)))
    padding = "".join(random.choices(string.ascii_letters + string.digits, k=max(5, padding_len)))
    return f"q={topic}&pad={padding}"


def calc_stats(values, def_mean=0.8, def_var=0.25):
    if not values:
        return def_mean, def_var
    mean_val = float(np.mean(values))
    if len(values) < 2:
        return mean_val, def_var
    var_val = float(np.var(values))
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


def run_adversarial_bot(target_url: str, total_requests: int, label: str, output_log: str,
                        device_id: str = "PC04", push: bool = True,
                        api_key: str = "sentinelnet_secure_secret_key_2026"):
    logger = TrafficLogger(output_log)
    base_url = target_url.rstrip("/")

    print(f"[*] Starting Tier 4 Adversarial Bot against target: {base_url}")
    print(f"[*] Total requests: {total_requests} | Label: {label} | Node ID: {device_id} | Live Dashboard Push: {'ENABLED' if push else 'DISABLED'}")
    print(f"[*] Delay distribution: Human LogNormal(mean={HUMAN_INTERVAL_MEAN:.2f}s, std={HUMAN_INTERVAL_STD:.2f}s)")
    print(f"[*] Packet size shaping: Target mean={HUMAN_PACKET_SIZE_MEAN:.0f}B")

    start_time = time.time()
    success_count = 0
    delays_used = []
    packet_sizes = []
    total_bytes = 0

    for req_idx in range(1, total_requests + 1):
        step_start = time.time()
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        # Shape request size with dynamic query string
        query = generate_padded_query()
        endpoint = f"{base_url}/search?{query}"

        status_code = -1
        elapsed_ms = 0.0
        resp_bytes = 0

        try:
            res = requests.get(endpoint, headers=headers, timeout=5.0)
            elapsed_ms = res.elapsed.total_seconds() * 1000.0
            status_code = res.status_code
            resp_bytes = len(res.content)
            success_count += 1
        except Exception as e:
            status_code = 0
            elapsed_ms = (time.time() - step_start) * 1000.0

        approx_pkt_size = max(resp_bytes + len(endpoint) + 120, 150)
        packet_sizes.append(approx_pkt_size)
        total_bytes += approx_pkt_size

        logger.log(endpoint, elapsed_ms, status_code, label)

        # Sample human-like delay before next request (except after the final request)
        if req_idx < total_requests:
            delay = sample_human_delay()
            delays_used.append(delay)
            print(f"[{req_idx}/{total_requests}] GET -> {status_code} ({elapsed_ms:.1f}ms) | Next delay: {delay:.3f}s")

            # Periodic intermediate push every 6 requests
            if push and req_idx % 6 == 0:
                elapsed_so_far = max(time.time() - start_time, 1.0)
                int_mean, int_var = calc_stats(delays_used, HUMAN_INTERVAL_MEAN, HUMAN_INTERVAL_STD ** 2)
                pkt_mean, pkt_var = calc_stats(packet_sizes, HUMAN_PACKET_SIZE_MEAN, HUMAN_PACKET_SIZE_STD ** 2)
                payload = {
                    "session_id": f"sess_tier4_{device_id}_{int(time.time())}",
                    "device_id": device_id,
                    "label": "Bot",
                    "bot_tier": "Tier3",
                    "requests_per_sec": round(req_idx / elapsed_so_far, 2),
                    "session_duration": round(elapsed_so_far, 2),
                    "packet_size_mean": round(pkt_mean, 2),
                    "packet_size_var": round(pkt_var, 2),
                    "request_interval_mean": round(int_mean, 4),
                    "request_interval_var": round(int_var, 4),
                    "bytes_transferred": total_bytes,
                    "num_connections": 1,
                    "protocol": "TCP",
                    "packet_count": req_idx * 2
                }
                push_session_to_dashboard(base_url, api_key, payload)

            time.sleep(delay)
        else:
            print(f"[{req_idx}/{total_requests}] GET -> {status_code} ({elapsed_ms:.1f}ms) | Finished session")

    actual_duration = max(time.time() - start_time, 1.0)
    mean_delay, var_delay = calc_stats(delays_used, HUMAN_INTERVAL_MEAN, HUMAN_INTERVAL_STD ** 2)
    pkt_mean, pkt_var = calc_stats(packet_sizes, HUMAN_PACKET_SIZE_MEAN, HUMAN_PACKET_SIZE_STD ** 2)

    if push:
        final_payload = {
            "session_id": f"sess_tier4_{device_id}_{int(time.time())}",
            "device_id": device_id,
            "label": "Bot",
            "bot_tier": "Tier3",
            "requests_per_sec": round(total_requests / actual_duration, 2),
            "session_duration": round(actual_duration, 2),
            "packet_size_mean": round(pkt_mean, 2),
            "packet_size_var": round(pkt_var, 2),
            "request_interval_mean": round(mean_delay, 4),
            "request_interval_var": round(var_delay, 4),
            "bytes_transferred": total_bytes,
            "num_connections": 1,
            "protocol": "TCP",
            "packet_count": total_requests * 2
        }
        push_session_to_dashboard(base_url, api_key, final_payload)

    print(f"[+] Adversarial Bot complete. {success_count}/{total_requests} successful.")
    print(f"    Observed delay mean: {mean_delay:.3f}s (human target: {HUMAN_INTERVAL_MEAN:.3f}s)")
    print(f"    Observed delay var:  {var_delay:.3f}s (human target: {HUMAN_INTERVAL_STD**2:.3f}s)")
    print(f"    Log saved to: {output_log}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SentinelNet Tier 4 Adversarial Bot (Feature Mimicking)")
    parser.add_argument("--target", "--target-url", dest="target_url", default="http://127.0.0.1:5001",
                        help="Target base URL (default: http://127.0.0.1:5001)")
    parser.add_argument("--requests", type=int, default=20,
                        help="Number of adversarial requests to send (default: 20)")
    parser.add_argument("--label", default="bot_adversarial",
                        help="Ground truth session label (default: bot_adversarial)")
    parser.add_argument("--device-id", default="PC04", help="Device identifier to display on dashboard (e.g. PC04)")
    parser.add_argument("--api-key", default="sentinelnet_secure_secret_key_2026", help="API authentication key")
    parser.add_argument("--no-push", action="store_true", help="Disable pushing session telemetry to dashboard")
    parser.add_argument("--output-log", default="tier4_log.csv",
                        help="Path to output traffic log CSV (default: tier4_log.csv)")

    args = parser.parse_args()
    run_adversarial_bot(
        target_url=args.target_url,
        total_requests=args.requests,
        label=args.label,
        output_log=args.output_log,
        device_id=args.device_id,
        push=not args.no_push,
        api_key=args.api_key
    )
