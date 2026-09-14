from scapy.all import IP, TCP, UDP
import time

def parse_packet(packet):
    """
    Extract useful network metadata from a packet.

    Returns:
        dict: Parsed packet metadata
        None: If the packet does not contain IPv4/TCP/UDP information
    """

    # We currently focus on IPv4 packets.
    if not packet.haslayer(IP):
        return None

    ip_layer = packet[IP]

    # Default values
    src_port = None
    dst_port = None
    protocol = "OTHER"

    # TCP packet
    if packet.haslayer(TCP):
        tcp_layer = packet[TCP]

        src_port = tcp_layer.sport
        dst_port = tcp_layer.dport
        protocol = "TCP"

    # UDP packet
    elif packet.haslayer(UDP):
        udp_layer = packet[UDP]

        src_port = udp_layer.sport
        dst_port = udp_layer.dport
        protocol = "UDP"

    else:
        return None

    return {
    "time": float(packet.time),
    "src_ip": ip_layer.src,
    "dst_ip": ip_layer.dst,
    "src_port": src_port,
    "dst_port": dst_port,
    "protocol": protocol,
    "packet_size": len(packet),
}