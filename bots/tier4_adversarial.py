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


def run_adversarial_bot(target_url: str, total_requests: int, label: str, output_log: str):
    logger = TrafficLogger(output_log)
    base_url = target_url.rstrip("/")

    print(f"[*] Starting Tier 4 Adversarial Bot against target: {base_url}")
    print(f"[*] Total requests: {total_requests} | Label: {label}")
    print(f"[*] Delay distribution: Human LogNormal(mean={HUMAN_INTERVAL_MEAN:.2f}s, std={HUMAN_INTERVAL_STD:.2f}s)")
    print(f"[*] Packet size shaping: Target mean={HUMAN_PACKET_SIZE_MEAN:.0f}B")

    success_count = 0
    delays_used = []

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

        try:
            res = requests.get(endpoint, headers=headers, timeout=5.0)
            elapsed_ms = res.elapsed.total_seconds() * 1000.0
            status_code = res.status_code
            success_count += 1
        except Exception as e:
            status_code = 0
            elapsed_ms = (time.time() - step_start) * 1000.0

        logger.log(endpoint, elapsed_ms, status_code, label)

        # Sample human-like delay before next request (except after the final request)
        if req_idx < total_requests:
            delay = sample_human_delay()
            delays_used.append(delay)
            print(f"[{req_idx}/{total_requests}] GET -> {status_code} ({elapsed_ms:.1f}ms) | Next delay: {delay:.3f}s")
            time.sleep(delay)
        else:
            print(f"[{req_idx}/{total_requests}] GET -> {status_code} ({elapsed_ms:.1f}ms) | Finished session")

    mean_delay = float(np.mean(delays_used)) if delays_used else 0.0
    var_delay = float(np.var(delays_used)) if delays_used else 0.0
    print(f"[+] Adversarial Bot complete. {success_count}/{total_requests} successful.")
    print(f"    Observed delay mean: {mean_delay:.3f}s (human target: {HUMAN_INTERVAL_MEAN:.3f}s)")
    print(f"    Observed delay var:  {var_delay:.3f}s (human target: {HUMAN_INTERVAL_STD**2:.3f}s)")
    print(f"    Log saved to: {output_log}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SentinelNet Tier 4 Adversarial Bot (Feature Mimicking)")
    parser.add_argument("--target", "--target-url", dest="target_url", default="http://127.0.0.1:5000",
                        help="Target base URL (default: http://127.0.0.1:5000)")
    parser.add_argument("--requests", type=int, default=20,
                        help="Number of adversarial requests to send (default: 20)")
    parser.add_argument("--label", default="bot_adversarial",
                        help="Ground truth session label (default: bot_adversarial)")
    parser.add_argument("--output-log", default="tier4_log.csv",
                        help="Path to output traffic log CSV (default: tier4_log.csv)")

    args = parser.parse_args()
    run_adversarial_bot(args.target_url, args.requests, args.label, args.output_log)
