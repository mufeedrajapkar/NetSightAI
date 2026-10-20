import argparse

from scapy.all import sniff

from CN.agent.capture.packet_parser import parse_packet
from CN.agent.flow.flow_processor import FlowProcessor


# -----------------------------
# Command-line arguments
# -----------------------------

parser = argparse.ArgumentParser(
    description="SentinelNet Network Traffic Capture Agent"
)

parser.add_argument(
    "--device-id",
    default="PC01",
    help="Device identifier"
)

parser.add_argument(
    "--duration",
    type=int,
    default=30,
    help="Capture duration in seconds"
)

parser.add_argument(
    "--label",
    default="Human",
    choices=["Human", "Bot"],
    help="Traffic label"
)

parser.add_argument(
    "--bot-tier",
    default="None",
    choices=["None", "Tier1", "Tier2", "Tier3"],
    help="Bot difficulty tier"
)

parser.add_argument(
    "--output",
    default="sentinelnet_dataset.csv",
    help="CSV output file"
)

parser.add_argument(
    "--server-url",
    default=None,
    help="Central backend server URL (e.g. http://192.168.1.100:5001 or http://127.0.0.1:5001)"
)

parser.add_argument(
    "--api-key",
    default=None,
    help="Shared secret API key (X-API-Key header) for central ingest endpoint"
)

parser.add_argument(
    "--push",
    action="store_true",
    default=False,
    help="Push completed session features to the central server"
)

parser.add_argument(
    "--no-local-csv",
    action="store_true",
    default=False,
    help="Skip local CSV write on successful server push (fallback still active on network error)"
)


args = parser.parse_args()


# -----------------------------
# Initialize Flow Processor
# -----------------------------

processor = FlowProcessor(
    device_id=args.device_id,
    label=args.label,
    bot_tier=args.bot_tier,
    csv_file=args.output,
    server_url=args.server_url,
    api_key=args.api_key,
    push_to_server=args.push or bool(args.server_url),
    write_local_csv=not args.no_local_csv,
)


# -----------------------------
# Packet Callback
# -----------------------------

def packet_callback(packet):

    data = parse_packet(packet)

    if data is None:
        return

    features = processor.process_packet(data)

    print(
        "Session:",
        features["session_id"],
        "| Device:",
        features["device_id"],
        "| Label:",
        features["label"],
        "| Tier:",
        features["bot_tier"],
        "| Packets:",
        features["packet_count"],
        "| Bytes:",
        features["bytes_transferred"]
    )


# -----------------------------
# Start Capture
# -----------------------------

print("===================================")
print(" SentinelNet Network Capture Agent")
print("===================================")
print("Device     :", args.device_id)
print("Label      :", args.label)
print("Bot Tier   :", args.bot_tier)
print("Output CSV :", args.output)
print("Duration   :", args.duration, "seconds")
print("Push Server:", processor.server_url if processor.push_to_server else "Disabled (Local only)")
print("-----------------------------------")
print("Generate traffic to collect data.")
print("Capture will stop automatically.")
print()


# -----------------------------
# Capture Packets
# -----------------------------

try:

    sniff(
        prn=packet_callback,
        store=False,
        timeout=args.duration
    )

finally:

    print("\nCapture finished.")

    processor.save_all_sessions()

    print("Session processing and saving complete.")