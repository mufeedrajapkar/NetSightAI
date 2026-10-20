"""
demo_phase5b_live_capture.py
----------------------------
CN_AI Phase 5B — Controlled Local Traffic Capture Demo.

Captures actual TCP network packets from local bot traffic generated against
`bots/test_server.py`, parses them with Scapy, processes them through the CN
pipeline (FlowProcessor -> extract_features), and classifies them with AIBridge.

Features & Design:
------------------
1. Targeted Capture:
   - Uses Scapy with strict BPF filter (e.g., 'tcp and port 5000').
   - No ARP spoofing, MITM, or payload inspection.
2. Windows Npcap & Loopback Diagnostics:
   - Checks for Npcap library and Administrator privilege.
   - If Npcap is missing or loopback capture is unprivileged on Windows,
     clearly reports the missing requirements and falls back automatically
     to PCAP replay mode using verified reference captures.
3. Full Pipeline:
   - Scapy Packets -> parse_packet -> FlowProcessor -> AIBridge -> Prediction & Probabilities.
4. Clean Resource Management:
   - Starts and stops test server subprocess cleanly.
   - Thread-safe packet capture and teardown.

Usage:
------
Live Capture (requires Npcap + Administrator):
    python CN/demos/demo_phase5b_live_capture.py --mode live --tier tier1

PCAP Replay Mode (works everywhere, no Npcap required):
    python CN/demos/demo_phase5b_live_capture.py --mode pcap --tier tier1

Auto Mode (detects environment, runs live if available or falls back to PCAP):
    python CN/demos/demo_phase5b_live_capture.py --mode auto --tier tier1
"""

import os
import sys
import time
import argparse
import subprocess
import threading
from typing import Dict, Any, Optional

# Ensure repository root is on sys.path
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from CN.agent.capture.packet_capture import (
    PacketCapture,
    check_environment,
    DEFAULT_BPF_FILTER,
    get_loopback_interface,
)
from CN.agent.flow.flow_processor import FlowProcessor
from CN.agent.ai_bridge import AIBridge


def start_test_server(host: str = "127.0.0.1", port: int = 5000) -> subprocess.Popen:
    """Start the test server as a background subprocess."""
    server_path = os.path.join(_REPO_ROOT, "bots", "test_server.py")
    python_exe = sys.executable

    proc = subprocess.Popen(
        [python_exe, server_path, "--host", host, "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Wait briefly for server startup
    time.sleep(1.0)
    return proc


def run_bot_client(tier: str, host: str = "127.0.0.1", port: int = 5000, n_requests: int = 8, duration: float = 5.0):
    """
    Execute requests matching the specified bot tier behavior against the test server.
    Uses requests library over real TCP socket.
    """
    import requests
    base_url = f"http://{host}:{port}"

    if tier == "tier1":
        headers = {"User-Agent": "SentinelNet-NaiveBot/1.0 (Fixed-Interval)"}
        interval = max(0.1, duration / n_requests)
        for _ in range(n_requests):
            try:
                requests.get(f"{base_url}/", headers=headers, timeout=2.0)
            except Exception:
                pass
            time.sleep(interval)

    elif tier == "tier2":
        import random
        headers = {"User-Agent": "SentinelNet-JitterBot/2.0"}
        queries = ["security", "packet", "ai", "model", "traffic"]
        for _ in range(n_requests):
            q = random.choice(queries)
            try:
                requests.get(f"{base_url}/search?q={q}", headers=headers, timeout=2.0)
            except Exception:
                pass
            time.sleep(random.uniform(0.2, 0.8))

    elif tier == "tier3":
        import random
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        endpoints = ["/", "/search?q=demo", "/product/101", "/api/data"]
        for path in endpoints:
            try:
                requests.get(f"{base_url}{path}", headers=headers, timeout=2.0)
            except Exception:
                pass
            time.sleep(random.uniform(0.3, 1.0))


def print_banner(title: str):
    print("=" * 68)
    print(f"  {title}")
    print("=" * 68)


def print_results(
    mode: str,
    tier: str,
    expected_label: str,
    prediction_result: Dict[str, Any],
    packet_count: int,
    raw_packet_count: int,
):
    """Format and print classification and pipeline metrics."""
    pred = prediction_result.get("prediction", "Unknown")
    probs = prediction_result.get("probability_estimates", {})
    features = prediction_result.get("features_used", {})
    metadata = prediction_result.get("metadata", {})
    model_type = prediction_result.get("model_type", "Unknown")

    match_indicator = "[MATCH]" if pred.lower() == expected_label.lower() or (expected_label.startswith("bot") and pred == "Bot") else "[MISMATCH / UNCERTAINTY]"

    print()
    print_banner("Phase 5B - Packet Capture & AI Classification Results")
    print(f" Execution Mode       : {mode}")
    print(f" Bot Tier Evaluated   : {tier}")
    print(f" Expected Label       : {expected_label}")
    print(f" Model Prediction     : {pred}  {match_indicator}")
    print(f" Model Algorithm      : {model_type}")
    print(f" Raw Packets Sniffed  : {raw_packet_count}")
    print(f" Packets Processed    : {packet_count}")
    print(f" Session Duration     : {features.get('session_duration', 0.0):.4f}s")
    print(f" Total Bytes Counted  : {features.get('bytes_transferred', 0)} bytes")
    print("-" * 68)
    print(" Class Probability Estimates:")
    for cls_name, prob in sorted(probs.items(), key=lambda x: -x[1]):
        bar = "#" * int(prob * 25)
        print(f"   {cls_name:<14} : {prob:.6f}  [{bar:<25}]")

    print("-" * 68)
    print(" Features Extracted (9 Model Contract Inputs):")
    for k, v in features.items():
        if isinstance(v, float):
            print(f"   {k:<24} : {v:.6f}")
        else:
            print(f"   {k:<24} : {v}")

    print("-" * 68)
    print(" Session Metadata:")
    for k, v in metadata.items():
        print(f"   {k:<24} : {v}")
    print("=" * 68)


def run_live_mode(
    tier: str,
    host: str = "127.0.0.1",
    port: int = 5000,
    duration: float = 5.0,
    n_requests: int = 8,
    save_pcap_path: Optional[str] = None,
) -> int:
    """Execute live packet capture against local test server."""
    env = check_environment()
    if not env["can_capture_live"]:
        print("\n[!] Live capture cannot proceed in current environment:")
        print(f"    {env['message']}")
        print("\n" + env["setup_guide"])
        print("\n[+] To test the full Scapy packet-processing pipeline immediately, use --mode pcap")
        return 1

    print(f"[*] Starting local test server on {host}:{port}...")
    server_proc = start_test_server(host, port)

    expected_label = f"bot_{tier}"
    bpf_filter = f"tcp and (src port {port} or dst port {port})"
    loopback_iface = get_loopback_interface()

    print(f"[*] Initializing Scapy packet capture...")
    print(f"    - Interface : {loopback_iface or 'Default'}")
    print(f"    - BPF Filter: {bpf_filter}")

    capture = PacketCapture(
        bpf_filter=bpf_filter,
        interface=loopback_iface,
        device_id="PC01",
        label="Bot",
        bot_tier=tier,
    )

    try:
        print("[*] Starting packet capture thread...")
        capture.start()

        print(f"[*] Executing {tier} bot traffic generator against http://{host}:{port}/...")
        bot_thread = threading.Thread(
            target=run_bot_client,
            args=(tier, host, port, n_requests, duration),
            daemon=True,
        )
        bot_thread.start()
        bot_thread.join(timeout=duration + 3.0)

        # Allow final packets to be captured
        time.sleep(1.0)
        capture.stop()
        print(f"[+] Capture stopped. Total raw packets captured: {len(capture.raw_packets)}")

        if save_pcap_path:
            capture.save_pcap(save_pcap_path)
            print(f"[+] Saved captured packets to: {save_pcap_path}")

        latest_features = capture.get_latest_features()
        if not latest_features:
            print("[!] Warning: No packets matching the filter were captured.")
            return 1

        bridge = AIBridge()
        result = bridge.predict(latest_features)

        print_results(
            mode="Live Scapy Sniffing (Npcap Loopback)",
            tier=tier,
            expected_label=expected_label,
            prediction_result=result,
            packet_count=len(capture.parsed_packets),
            raw_packet_count=len(capture.raw_packets),
        )
        return 0

    finally:
        print("[*] Shutting down local test server...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=2.0)
        except Exception:
            server_proc.kill()


def run_pcap_mode(
    tier: str,
    custom_pcap: Optional[str] = None,
) -> int:
    """Execute Scapy PCAP replay mode (safe fallback, no Npcap/admin required)."""
    pcap_path = custom_pcap
    if not pcap_path:
        default_name = f"{tier}_sample.pcap"
        pcap_path = os.path.join(_REPO_ROOT, "CN", "data", default_name)

    if not os.path.exists(pcap_path):
        # Auto-generate if missing
        print(f"[*] Generating sample PCAP for {tier}...")
        from CN.demos.generate_sample_pcap import (
            generate_tier1_pcap,
            generate_tier2_pcap,
            generate_tier3_pcap,
        )
        generators = {
            "tier1": generate_tier1_pcap,
            "tier2": generate_tier2_pcap,
            "tier3": generate_tier3_pcap,
        }
        gen = generators.get(tier, generate_tier1_pcap)
        gen(pcap_path)

    print(f"[*] Reading and parsing Scapy packets from: {pcap_path}")
    expected_label = f"bot_{tier}"

    capture = PacketCapture(
        device_id="PC01",
        label="Bot",
        bot_tier=tier,
    )

    feature_steps = capture.replay_pcap(pcap_path)
    latest_features = capture.get_latest_features()

    if not latest_features:
        print(f"[!] Error: No valid IP/TCP packets parsed from {pcap_path}")
        return 1

    bridge = AIBridge()
    result = bridge.predict(latest_features)

    print_results(
        mode=f"Scapy PCAP Replay Fallback ({os.path.basename(pcap_path)})",
        tier=tier,
        expected_label=expected_label,
        prediction_result=result,
        packet_count=len(capture.parsed_packets),
        raw_packet_count=len(capture.raw_packets),
    )
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="SentinelNet Phase 5B - Real Local Traffic Capture Demo"
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "live", "pcap"],
        default="auto",
        help="Capture mode: 'live' (real-time Scapy sniffing), 'pcap' (PCAP replay), or 'auto' (detect readiness)",
    )
    parser.add_argument(
        "--tier",
        choices=["tier1", "tier2", "tier3"],
        default="tier1",
        help="Bot tier traffic to generate/replay (default: tier1)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Test server host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Test server port (default: 5000)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Duration for traffic generation in seconds (default: 5.0)",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=8,
        help="Number of bot requests to issue (default: 8)",
    )
    parser.add_argument(
        "--pcap-file",
        default=None,
        help="Path to custom PCAP file for replay mode",
    )
    parser.add_argument(
        "--save-pcap",
        default=None,
        help="Path to save captured live packets as a PCAP file",
    )

    args = parser.parse_args()

    print_banner("SentinelNet Phase 5B - Real Local Traffic Capture Demo")
    env = check_environment()
    print(f" Environment Status : {env['message']}")
    print(f" Npcap Available    : {env['pcap_available']}")
    print(f" Admin Privileges   : {env['is_admin']}")
    print(f" Loopback Adapter   : {env['loopback_iface'] or 'None detected'}")
    print()

    if args.mode == "auto":
        if env["can_capture_live"] and env["loopback_iface"]:
            print("[+] Environment supports live capture. Starting live mode...")
            sys.exit(run_live_mode(
                tier=args.tier,
                host=args.host,
                port=args.port,
                duration=args.duration,
                n_requests=args.requests,
                save_pcap_path=args.save_pcap,
            ))
        else:
            print("[!] Npcap live loopback capture is unavailable in current process context.")
            print("[+] Using safe Scapy PCAP Replay mode for full pipeline verification...")
            sys.exit(run_pcap_mode(tier=args.tier, custom_pcap=args.pcap_file))

    elif args.mode == "live":
        sys.exit(run_live_mode(
            tier=args.tier,
            host=args.host,
            port=args.port,
            duration=args.duration,
            n_requests=args.requests,
            save_pcap_path=args.save_pcap,
        ))

    elif args.mode == "pcap":
        sys.exit(run_pcap_mode(tier=args.tier, custom_pcap=args.pcap_file))


if __name__ == "__main__":
    main()
