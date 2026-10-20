"""
run_agent.py
------------
SentinelNet - Standalone Distributed Network Telemetry Capture Agent.

Runs on individual client machines (e.g. PC01, PC02, PC03) to:
1. Capture local TCP/IP traffic using Scapy and targeted BPF filtering.
2. Track transport-layer flows and aggregate conversational session windows.
3. Extract the 9 contract statistical features.
4. Stream completed session rows in real-time to the central backend (/api/ingest).
5. Fall back gracefully to local CSV logging if network push fails or central server is offline.
6. Handle Ctrl+C cleanly by flushing all active sessions before exit.
"""

import os
import sys
import time
import signal
import argparse
from typing import Optional

# Ensure repository root is on sys.path
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from CN.agent.capture.packet_capture import (
    PacketCapture,
    check_environment,
    build_bpf_filter,
    DEFAULT_BPF_FILTER,
    is_windows,
)
from CN.agent.flow.flow_processor import FlowProcessor


def parse_args():
    parser = argparse.ArgumentParser(
        description="SentinelNet Distributed Capture Agent",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--device-id", default="PC01", help="Unique identifier for this node (e.g. PC01, PC02)")
    parser.add_argument("--server-url", default=None, help="Central SentinelNet server URL (e.g. http://192.168.1.100:5001)")
    parser.add_argument("--api-key", default=None, help="Shared API key for server ingestion authentication")
    parser.add_argument("--interface", default=None, help="Network interface name or GUID for packet sniffing")
    parser.add_argument("--filter", dest="bpf_filter", default=None, help="Custom BPF filter expression")
    parser.add_argument("--port", type=int, default=None, help="Target TCP port for BPF filtering (e.g. 5000)")
    parser.add_argument("--all-ip", action="store_true", help="Capture all IPv4 traffic ('ip' BPF filter)")
    parser.add_argument("--label", default="Human", help="Ground-truth classification label (Human, Bot, Suspicious)")
    parser.add_argument("--bot-tier", default="None", help="Bot sophistication tier (None, Tier1, Tier2, Tier3)")
    parser.add_argument("--output-csv", default=None, help="Local CSV destination for sessions (fallback or primary)")
    parser.add_argument("--duration", type=float, default=None, help="Capture duration in seconds (None = run indefinitely)")
    return parser.parse_args()


def main():
    args = parse_args()

    # 1. Environment and prerequisite checks
    env = check_environment()
    print("=" * 65)
    print("  SentinelNet Distributed Telemetry Capture Agent")
    print("=" * 65)
    print(f"[*] Node Device ID  : {args.device_id}")
    print(f"[*] Ground-truth     : {args.label} (Tier: {args.bot_tier})")
    print(f"[*] Operating System : {sys.platform}")

    if not env["pcap_available"]:
        print("\n[!] FATAL ERROR: Npcap is missing or Scapy libpcap provider is unavailable.", file=sys.stderr)
        print("[!] Live packet sniffing cannot proceed without Npcap installed.", file=sys.stderr)
        print("\nSetup Guide:\n" + env["setup_guide"], file=sys.stderr)
        sys.exit(1)

    if is_windows() and not env["is_admin"]:
        print("\n[!] FATAL ERROR: Process is not running as Administrator.", file=sys.stderr)
        print("[!] On Windows, raw packet capture via Npcap requires an elevated Administrator prompt.", file=sys.stderr)
        print("[!] Please open PowerShell or Command Prompt as Administrator and re-run.", file=sys.stderr)
        sys.exit(1)

    # 2. Resolve Server Push & API Key configuration
    resolved_server = args.server_url or os.environ.get("SENTINELNET_SERVER_URL")
    resolved_key = args.api_key or os.environ.get("SENTINELNET_API_KEY")

    # Attempt to load from root .env if not explicitly passed
    if not resolved_key:
        env_file = os.path.join(_REPO_ROOT, ".env")
        if os.path.exists(env_file):
            try:
                with open(env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("SENTINELNET_API_KEY="):
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if val:
                                resolved_key = val
                        elif line.startswith("SENTINELNET_SERVER_URL=") and not resolved_server:
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if val:
                                resolved_server = val
            except Exception:
                pass

    if resolved_server:
        if not resolved_key:
            print("\n[!] ERROR: Central server URL specified, but no SENTINELNET_API_KEY was provided.", file=sys.stderr)
            print("[!] Central server will reject requests without an API key.", file=sys.stderr)
            print("[!] Pass --api-key <KEY> or set SENTINELNET_API_KEY in environment or .env file.", file=sys.stderr)
            sys.exit(1)
        print(f"[*] Live Streaming   : ENABLED -> {resolved_server}/api/ingest")
    else:
        print("[*] Live Streaming   : DISABLED (Local CSV mode only)")

    # 3. Resolve BPF filter and Interface
    chosen_filter = build_bpf_filter(filter_str=args.bpf_filter, port=args.port, all_ip=args.all_ip)
    chosen_iface = args.interface or env.get("loopback_iface")
    output_csv = args.output_csv or os.path.join(_REPO_ROOT, "CN", "data", "raw", f"{args.device_id}.csv")

    print(f"[*] Sniff Interface  : {chosen_iface or 'Default OS Interface'}")
    print(f"[*] BPF Filter       : {chosen_filter}")
    print(f"[*] Local CSV Target : {output_csv}")
    print("-" * 65)

    # 4. Initialize FlowProcessor and PacketCapture
    processor = FlowProcessor(
        device_id=args.device_id,
        label=args.label,
        bot_tier=args.bot_tier,
        csv_file=output_csv,
        server_url=resolved_server,
        api_key=resolved_key,
        push_to_server=bool(resolved_server),
        write_local_csv=True,
    )

    capture = PacketCapture(
        bpf_filter=chosen_filter,
        interface=chosen_iface,
        processor=processor,
        device_id=args.device_id,
        label=args.label,
        bot_tier=args.bot_tier,
    )

    # 5. Clean Exit and Signal Handling
    shutdown_requested = False

    def handle_shutdown(signum, frame):
        nonlocal shutdown_requested
        if shutdown_requested:
            return
        shutdown_requested = True
        print("\n\n[*] Interrupt received (Ctrl+C). Stopping capture and flushing remaining sessions...")
        capture.stop()
        processor.save_all_sessions()
        print(f"[+] Shutdown complete. Total packets observed: {len(capture.raw_packets)}")
        print(f"[+] Total sessions tracked: {len(processor.session_tracker.sessions)}")
        print(f"[+] Local data written to: {output_csv}")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_shutdown)

    # 6. Start Sniffer
    print("[*] Starting live packet sniffer...")
    capture.start(timeout=args.duration)
    print("[+] Packet capture active. Press Ctrl+C at any time to exit and flush sessions.\n")

    start_time = time.time()
    try:
        while capture.is_capturing:
            time.sleep(1.0)
            elapsed = time.time() - start_time
            pkts = len(capture.raw_packets)
            sessions = len(processor.session_tracker.sessions)
            print(f"\r[*] Active | Elapsed: {elapsed:5.1f}s | Packets: {pkts:5d} | Active Sessions: {sessions:3d}", end="", flush=True)

            if args.duration and elapsed >= args.duration:
                break
    except KeyboardInterrupt:
        handle_shutdown(None, None)

    print("\n[*] Duration reached. Stopping capture...")
    capture.stop()
    processor.save_all_sessions()
    print(f"[+] Final session flush complete. Total packets: {len(capture.raw_packets)}")


if __name__ == "__main__":
    main()
