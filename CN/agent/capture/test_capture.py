import argparse

from scapy.all import sniff
from CN.agent.capture.packet_parser import parse_packet
from CN.agent.flow.flow_processor import FlowProcessor


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


args = parser.parse_args()


processor = FlowProcessor(
    device_id=args.device_id,
    label=args.label,
    bot_tier=args.bot_tier,
    csv_file=args.output
)


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


print("===================================")
print(" SentinelNet Network Capture Agent")
print("===================================")
print("Device  :", args.device_id)
print("Label   :", args.label)
print("Bot Tier:", args.bot_tier)
print("Output  :", args.output)
print("Duration:", args.duration, "seconds")
print("-----------------------------------")
print("Generate traffic to collect data.")
print("Capture will stop automatically.")
print()


try:

    sniff(
        prn=packet_callback,
        store=False,
        timeout=args.duration
    )

finally:

    print("\nCapture finished.")

    processor.save_all_sessions()

    print("Sessions saved to CSV.")
