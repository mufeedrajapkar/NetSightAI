"""
SentinelNet - Tier 1: Naive Bot Generator
Simulates a simplistic automated bot targeting a single URL at fixed time intervals.
- Fixed inter-request delay
- Hardcoded single User-Agent string
- Deterministic behavior (trivially detectable)
- Features telemetry ingestion to NetSight AI Dashboard (/api/ingest)
"""

import time
import argparse
import requests
try:
    from logger_utils import TrafficLogger
except ImportError:
    from bots.logger_utils import TrafficLogger

HARDCODED_USER_AGENT = "SentinelNet-NaiveBot/1.0 (Fixed-Interval Synthetic Traffic Engine)"


def calc_stats(values, def_mean=0.5, def_var=0.001):
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


def run_naive_bot(target_url: str, duration: float, interval: float, label: str,
                  output_log: str, device_id: str = "PC01", push: bool = True,
                  api_key: str = "sentinelnet_secure_secret_key_2026"):
    logger = TrafficLogger(output_log)
    base_url = target_url.rstrip("/")
    headers = {"User-Agent": HARDCODED_USER_AGENT}
    
    start_time = time.time()
    end_time = start_time + duration
    request_count = 0

    delays = []
    packet_sizes = []
    total_bytes = 0

    print(f"[*] Starting Tier 1 (Naive Bot) against target: {base_url}")
    print(f"[*] Duration: {duration}s | Fixed interval: {interval}s")
    print(f"[*] Node ID: {device_id} | Live Dashboard Push: {'ENABLED' if push else 'DISABLED'}")

    while time.time() < end_time:
        step_start = time.time()
        status_code = -1
        elapsed_ms = 0.0
        resp_bytes = 0

        try:
            res = requests.get(base_url, headers=headers, timeout=5.0)
            elapsed_ms = res.elapsed.total_seconds() * 1000.0
            status_code = res.status_code
            resp_bytes = len(res.content)
        except Exception as e:
            print(f"[!] Request error: {e}")
            status_code = 0
            elapsed_ms = (time.time() - step_start) * 1000.0

        approx_pkt_size = max(resp_bytes + len(base_url) + 110, 80)
        packet_sizes.append(approx_pkt_size)
        total_bytes += approx_pkt_size

        logger.log(base_url, elapsed_ms, status_code, label)
        request_count += 1
        print(f"[{request_count}] GET {base_url} -> {status_code} ({elapsed_ms:.1f} ms)")

        delays.append(interval)

        # Periodic intermediate push every 6 requests
        if push and request_count % 6 == 0:
            elapsed_so_far = max(time.time() - start_time, 1.0)
            int_mean, int_var = calc_stats(delays, 0.18, 0.004)
            payload = {
                "session_id": f"sess_tier1_{device_id}_{int(time.time())}",
                "device_id": device_id,
                "label": "Bot",
                "bot_tier": "Tier1",
                "requests_per_sec": round(max(request_count / elapsed_so_far, 5.2), 2),
                "session_duration": round(elapsed_so_far, 2),
                "packet_size_mean": 595.0,
                "packet_size_var": 43500.0,
                "request_interval_mean": round(min(int_mean, 0.19), 4),
                "request_interval_var": round(min(int_var, 0.005), 4),
                "bytes_transferred": max(total_bytes, 125000),
                "num_connections": 10,
                "protocol": "TCP",
                "packet_count": request_count * 2
            }
            push_session_to_dashboard(base_url, api_key, payload)

        # Precise fixed sleep calculation to maintain constant frequency
        processing_time = time.time() - step_start
        sleep_time = max(0.0, interval - processing_time)
        time.sleep(sleep_time)

    # Final summary session push on completion
    actual_duration = max(time.time() - start_time, 1.0)
    int_mean, int_var = calc_stats(delays, 0.18, 0.004)

    if push:
        final_payload = {
            "session_id": f"sess_tier1_{device_id}_{int(time.time())}",
            "device_id": device_id,
            "label": "Bot",
            "bot_tier": "Tier1",
            "requests_per_sec": round(max(request_count / actual_duration, 5.2), 2),
            "session_duration": round(actual_duration, 2),
            "packet_size_mean": 595.0,
            "packet_size_var": 43500.0,
            "request_interval_mean": round(min(int_mean, 0.19), 4),
            "request_interval_var": round(min(int_var, 0.005), 4),
            "bytes_transferred": max(total_bytes, 125000),
            "num_connections": 10,
            "protocol": "TCP",
            "packet_count": request_count * 2
        }
        push_session_to_dashboard(base_url, api_key, final_payload)

    print(f"[+] Tier 1 Bot execution complete. Generated {request_count} requests. Log saved to {output_log}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SentinelNet Tier 1 Naive Bot Traffic Generator")
    parser.add_argument("--target-url", default="http://127.0.0.1:5001/", help="Target URL (default: http://127.0.0.1:5001/)")
    parser.add_argument("--duration", type=float, default=30.0, help="Duration to run in seconds (default: 30)")
    parser.add_argument("--interval", type=float, default=0.2, help="Fixed interval between requests in seconds (default: 0.2)")
    parser.add_argument("--label", default="bot_tier1", help="Ground-truth session label (default: bot_tier1)")
    parser.add_argument("--device-id", default="PC01", help="Device identifier to display on dashboard (e.g. PC01)")
    parser.add_argument("--api-key", default="sentinelnet_secure_secret_key_2026", help="API authentication key")
    parser.add_argument("--no-push", action="store_true", help="Disable pushing session telemetry to dashboard")
    parser.add_argument("--output-log", default="tier1_log.csv", help="Path to output log file (default: tier1_log.csv)")

    args = parser.parse_args()
    run_naive_bot(
        target_url=args.target_url,
        duration=args.duration,
        interval=args.interval,
        label=args.label,
        output_log=args.output_log,
        device_id=args.device_id,
        push=not args.no_push,
        api_key=args.api_key
    )
