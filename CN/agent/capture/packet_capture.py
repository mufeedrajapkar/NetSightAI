"""
packet_capture.py
-----------------
SentinelNet - Real Local Packet Capture Engine using Scapy.

Provides controlled, safe packet capture for local testing:
- Targeted BPF filtering (e.g. 'tcp and port 5000') to avoid broad/unrestricted capture.
- Strictly no ARP spoofing, MITM, or payload inspection.
- Converts captured Scapy packets into CN-compatible packet metadata dictionaries.
- Integrates with FlowProcessor and AIBridge for real-time and post-capture classification.
- Handles Windows Npcap detection, privilege checks, loopback interface discovery,
  and provides safe PCAP save/replay fallback.
"""

import os
import sys
import time
import ctypes
import threading
from typing import Optional, Dict, Any, List, Tuple

from scapy.all import sniff, conf, wrpcap, rdpcap, Packet
from scapy.arch.windows import get_windows_if_list

from CN.agent.capture.packet_parser import parse_packet
from CN.agent.flow.flow_processor import FlowProcessor
from CN.agent.ai_bridge import AIBridge, classify_flow


# Default safe BPF filter for local test server traffic
DEFAULT_BPF_FILTER = "tcp and (src port 5000 or dst port 5000)"


def is_windows() -> bool:
    """Return True if running on Windows OS."""
    return sys.platform.startswith("win")


def is_admin() -> bool:
    """Return True if current process has Administrator privileges on Windows."""
    if not is_windows():
        return os.geteuid() == 0 if hasattr(os, "geteuid") else False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def get_loopback_interface() -> Optional[str]:
    """
    Search for Npcap loopback adapter on Windows.
    Returns interface name or GUID if found, None otherwise.
    """
    if not is_windows():
        return "lo"

    try:
        if_list = get_windows_if_list()
        for iface in if_list:
            desc = str(iface.get("description", "")).lower()
            name = str(iface.get("name", "")).lower()
            guid = str(iface.get("guid", ""))

            if "npcap loopback" in desc or "npcap loopback" in name or "loopback" in desc or "loopback" in name:
                # Scapy on Windows prefers the NPF name or GUID
                return f"\\Device\\NPF_{guid}" if guid and not guid.startswith("\\") else (iface.get("name") or guid)
    except Exception:
        pass
    return None


def check_environment() -> Dict[str, Any]:
    """
    Check the current OS and Scapy environment for live capture readiness.

    Returns:
        dict: Diagnostic details containing:
            - pcap_available (bool): True if libpcap/Npcap provider is active.
            - is_admin (bool): True if running with admin rights.
            - loopback_iface (str or None): Name of loopback adapter if found.
            - can_capture_live (bool): True if live capture can proceed.
            - message (str): Human-readable diagnosis.
            - setup_guide (str): Instructions to fix missing requirements.
    """
    pcap_available = bool(getattr(conf, "use_pcap", False))
    admin_status = is_admin()
    loopback_iface = get_loopback_interface()

    can_capture_live = pcap_available

    message_parts = []
    if not pcap_available:
        message_parts.append(
            "Npcap/WinPcap is not installed or libpcap provider is unavailable in Scapy."
        )
    if is_windows() and not admin_status:
        message_parts.append(
            "Process is not running as Administrator (required for raw packet capture on Windows)."
        )
    if not loopback_iface:
        message_parts.append(
            "Npcap Loopback Adapter was not detected. Loopback (127.0.0.1) traffic requires Npcap with loopback support."
        )

    setup_guide = (
        "Windows Setup Requirements for Real Live Traffic Capture:\n"
        "1. Download and install Npcap from https://npcap.com/\n"
        "2. During installation, select:\n"
        "   [x] 'Install Npcap in WinPcap API-compatible Mode'\n"
        "   [x] 'Support loopback traffic (Npcap Loopback Adapter)'\n"
        "3. Run your shell (PowerShell / Command Prompt) as Administrator.\n"
        "4. If loopback capture is unavailable, use a physical interface or PCAP replay mode."
    )

    if can_capture_live:
        diagnosis = "Environment is ready for live packet capture."
    else:
        diagnosis = "Live capture prerequisites missing. Fallback to PCAP replay mode recommended."

    return {
        "pcap_available": pcap_available,
        "is_admin": admin_status,
        "loopback_iface": loopback_iface,
        "can_capture_live": can_capture_live,
        "message": diagnosis + (" Details: " + " ".join(message_parts) if message_parts else ""),
        "setup_guide": setup_guide,
    }


class PacketCapture:
    """
    Manages controlled packet capture, Scapy packet parsing, flow processing,
    and AI classification.
    """

    def __init__(
        self,
        bpf_filter: str = DEFAULT_BPF_FILTER,
        interface: Optional[str] = None,
        processor: Optional[FlowProcessor] = None,
        device_id: str = "PC01",
        label: str = "Bot",
        bot_tier: str = "Tier1",
    ):
        self.bpf_filter = bpf_filter
        self.interface = interface
        self.processor = processor or FlowProcessor(
            device_id=device_id,
            label=label,
            bot_tier=bot_tier,
            csv_file=os.devnull,
        )
        self.raw_packets: List[Packet] = []
        self.parsed_packets: List[Dict[str, Any]] = []
        self.extracted_features: List[Dict[str, Any]] = []

        self._sniffer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_capturing = False
        self._lock = threading.Lock()

    def _packet_handler(self, packet: Packet):
        """Callback invoked by Scapy for each captured packet."""
        parsed = parse_packet(packet)
        if parsed is None:
            return

        with self._lock:
            self.raw_packets.append(packet)
            self.parsed_packets.append(parsed)

            if self.processor:
                try:
                    features = self.processor.process_packet(parsed)
                    self.extracted_features.append(features)
                except Exception as exc:
                    pass

    def start(self, timeout: Optional[float] = None):
        """
        Start packet capture in a background thread.

        Args:
            timeout (float, optional): Maximum duration to sniff in seconds.
        """
        if self._is_capturing:
            raise RuntimeError("Capture is already running.")

        self._stop_event.clear()
        self._is_capturing = True

        def _sniff_worker():
            try:
                sniff_kwargs = {
                    "prn": self._packet_handler,
                    "filter": self.bpf_filter,
                    "store": False,
                    "stop_filter": lambda p: self._stop_event.is_set(),
                }
                if self.interface:
                    sniff_kwargs["iface"] = self.interface
                if timeout:
                    sniff_kwargs["timeout"] = timeout

                sniff(**sniff_kwargs)
            finally:
                self._is_capturing = False

        self._sniffer_thread = threading.Thread(target=_sniff_worker, daemon=True)
        self._sniffer_thread.start()

    def stop(self, join_timeout: float = 2.0):
        """
        Stop packet capture and wait for worker thread to exit.
        """
        self._stop_event.set()
        if self._sniffer_thread and self._sniffer_thread.is_alive():
            self._sniffer_thread.join(timeout=join_timeout)
        self._is_capturing = False

    @property
    def is_capturing(self) -> bool:
        """Return True if background capture is active."""
        return self._is_capturing

    def get_latest_features(self) -> Optional[Dict[str, Any]]:
        """Return the most recent feature extraction dictionary."""
        with self._lock:
            return self.extracted_features[-1] if self.extracted_features else None

    def save_pcap(self, filepath: str):
        """
        Save all captured raw packets to a PCAP file.

        Args:
            filepath (str): Target .pcap destination path.
        """
        with self._lock:
            if not self.raw_packets:
                raise ValueError("No packets captured to save.")
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            wrpcap(filepath, self.raw_packets)

    def replay_pcap(
        self,
        filepath: str,
        processor: Optional[FlowProcessor] = None,
    ) -> List[Dict[str, Any]]:
        """
        Read packets from a saved PCAP file and feed them through the pipeline.

        Args:
            filepath (str): Path to .pcap file.
            processor (FlowProcessor, optional): Processor to use.

        Returns:
            list: All extracted feature dicts produced during replay.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"PCAP file not found: {filepath}")

        proc = processor or self.processor
        packets = rdpcap(filepath)
        results = []

        with self._lock:
            self.raw_packets.clear()
            self.parsed_packets.clear()
            self.extracted_features.clear()

            for pkt in packets:
                parsed = parse_packet(pkt)
                if parsed is None:
                    continue

                self.raw_packets.append(pkt)
                self.parsed_packets.append(parsed)

                feat = proc.process_packet(parsed)
                self.extracted_features.append(feat)
                results.append(feat)

        return results

    def classify(self, bridge: Optional[AIBridge] = None) -> Dict[str, Any]:
        """
        Classify the flow using AIBridge.

        Returns:
            dict: AIBridge prediction output.
        """
        latest_features = self.get_latest_features()
        if latest_features is None:
            raise RuntimeError("No flow features available to classify. Process packets first.")

        ai_bridge = bridge or AIBridge()
        return ai_bridge.predict(latest_features)
