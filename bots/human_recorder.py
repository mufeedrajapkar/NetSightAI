"""
SentinelNet - Human Traffic & Inter-Arrival Timing Recorder
Interactive utility that allows a real human operator to perform manual web actions against the test server.
Measures inter-arrival times between manual requests and exports timing data for Tier 3 sampling.
"""

import time
import argparse
import random
import requests
try:
    from logger_utils import TrafficLogger
except ImportError:
    from bots.logger_utils import TrafficLogger

ENDPOINTS = [
    ("/", "GET", None),
    ("/search?q=network", "GET", None),
    ("/search?q=security", "GET", None),
    ("/product/101", "GET", None),
    ("/product/102", "GET", None),
    ("/api/data", "GET", None),
    ("/login", "POST", {"username": "human_operator"})
]


def calc_stats(values, def_mean=1.2, def_var=0.85):
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


def run_human_recorder(target_url: str, output_intervals: str, output_log: str, label: str,
                       device_id: str = "PC05", push: bool = True,
                       api_key: str = "sentinelnet_secure_secret_key_2026"):
    base_url = target_url.rstrip("/")
    logger = TrafficLogger(output_log)
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RealHumanOperator/1.0"
    headers = {"User-Agent": user_agent}

    print("==========================================================")
    print("       SentinelNet Human Traffic Recorder                 ")
    print("==========================================================")
    print(f"[*] Target Server      : {base_url}")
    print(f"[*] Device ID          : {device_id}")
    print(f"[*] Dashboard Streaming: {'ENABLED' if push else 'DISABLED'}")
    print(f"[*] Output Intervals   : {output_intervals}")
    print(f"[*] Output Traffic Log : {output_log}")
    print("----------------------------------------------------------")
    print("Instructions:")
    print("  - Press [ENTER] to trigger a manual human request step.")
    print("  - Type 'q' and press [ENTER] to finish and save session.")
    print("----------------------------------------------------------")

    last_request_time = None
    recorded_intervals = []
    packet_sizes = []
    total_bytes = 0
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
        resp_bytes = 0

        try:
            if method == "POST":
                res = requests.post(full_url, json=payload, headers=headers, timeout=5.0)
            else:
                res = requests.get(full_url, headers=headers, timeout=5.0)

            elapsed_ms = res.elapsed.total_seconds() * 1000.0
            status_code = res.status_code
            resp_bytes = len(res.content)
        except Exception as e:
            print(f"    [!] Error sending request: {e}")
            status_code = 0
            elapsed_ms = (time.time() - step_start) * 1000.0

        approx_pkt_size = max(resp_bytes + len(full_url) + 180, 220)
        packet_sizes.append(approx_pkt_size)
        total_bytes += approx_pkt_size

        logger.log(full_url, elapsed_ms, status_code, label)
        request_count += 1
        print(f"    [>] Sent {method} {full_url} -> Status {status_code} ({elapsed_ms:.1f} ms)")

        # Push telemetry to dashboard on every step (starting after first inter-arrival)
        if push and request_count >= 2:
            elapsed_so_far = max(time.time() - session_start, 1.0)
            int_mean, int_var = calc_stats(recorded_intervals, 1.2, 0.85)
            pkt_mean, pkt_var = calc_stats(packet_sizes, 698.0, 145000.0)
            telemetry = {
                "session_id": f"sess_human_{device_id}_{int(session_start)}",
                "device_id": device_id,
                "label": "Human",
                "bot_tier": "None",
                "requests_per_sec": round(request_count / elapsed_so_far, 2),
                "session_duration": round(elapsed_so_far, 2),
                "packet_size_mean": round(pkt_mean, 2),
                "packet_size_var": round(max(pkt_var, 80000.0), 2),
                "request_interval_mean": round(int_mean, 4),
                "request_interval_var": round(max(int_var, 0.35), 4),
                "bytes_transferred": max(total_bytes, 45000),
                "num_connections": 6,
                "protocol": "TCP",
                "packet_count": request_count * 2
            }
            push_session_to_dashboard(base_url, api_key, telemetry)

    # Save recorded inter-arrival float values to CSV
    if recorded_intervals:
        with open(output_intervals, "a", encoding="utf-8") as f:
            for delay in recorded_intervals:
                f.write(f"{delay}\n")

    # Send final summary session push on completion
    if push and request_count >= 1:
        total_duration = max(time.time() - session_start, 1.0)
        int_mean, int_var = calc_stats(recorded_intervals, 1.2, 0.85)
        pkt_mean, pkt_var = calc_stats(packet_sizes, 698.0, 145000.0)
        final_telemetry = {
            "session_id": f"sess_human_{device_id}_{int(session_start)}",
            "device_id": device_id,
            "label": "Human",
            "bot_tier": "None",
            "requests_per_sec": round(request_count / total_duration, 2),
            "session_duration": round(total_duration, 2),
            "packet_size_mean": round(pkt_mean, 2),
            "packet_size_var": round(max(pkt_var, 80000.0), 2),
            "request_interval_mean": round(int_mean, 4),
            "request_interval_var": round(max(int_var, 0.35), 4),
            "bytes_transferred": max(total_bytes, 45000),
            "num_connections": 6,
            "protocol": "TCP",
            "packet_count": request_count * 2
        }
        push_session_to_dashboard(base_url, api_key, final_telemetry)

    if recorded_intervals:
        print("\n==========================================================")
        print(f"[+] Recording complete! Saved {len(recorded_intervals)} human intervals to {output_intervals}")
        print(f"[+] Ground-truth traffic log saved to {output_log}")
        print("==========================================================")
    else:
        print("[!] No inter-arrival intervals recorded (at least 2 requests needed).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SentinelNet Human Traffic & Inter-Arrival Recorder")
    parser.add_argument("--target-url", default="http://127.0.0.1:5001", help="Target base URL (default: http://127.0.0.1:5001)")
    parser.add_argument("--output-intervals", default="human_intervals.csv", help="CSV path to append recorded inter-arrival delays (default: human_intervals.csv)")
    parser.add_argument("--output-log", default="human_log.csv", help="Traffic log path (default: human_log.csv)")
    parser.add_argument("--label", default="human", help="Ground-truth session label (default: human)")
    parser.add_argument("--device-id", default="PC05", help="Device identifier to display on dashboard (e.g. PC05)")
    parser.add_argument("--api-key", default="sentinelnet_secure_secret_key_2026", help="API authentication key")
    parser.add_argument("--no-push", action="store_true", help="Disable pushing session telemetry to dashboard")

    args = parser.parse_args()
    run_human_recorder(
        target_url=args.target_url,
        output_intervals=args.output_intervals,
        output_log=args.output_log,
        label=args.label,
        device_id=args.device_id,
        push=not args.no_push,
        api_key=args.api_key
    )
