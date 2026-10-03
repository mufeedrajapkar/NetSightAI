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

    # Default flag and sequence values
    is_syn = False
    is_ack = False
    is_fin = False
    is_rst = False
    seq = None

    # TCP packet
    if packet.haslayer(TCP):
        tcp_layer = packet[TCP]

        src_port = tcp_layer.sport
        dst_port = tcp_layer.dport
        protocol = "TCP"

        # Safely extract TCP flags bitmask
        try:
            flags_int = int(tcp_layer.flags)
            is_fin = bool(flags_int & 0x01)
            is_syn = bool(flags_int & 0x02)
            is_rst = bool(flags_int & 0x04)
            is_ack = bool(flags_int & 0x10)
        except (ValueError, TypeError, AttributeError):
            pass

        try:
            seq = int(tcp_layer.seq)
        except (ValueError, TypeError, AttributeError):
            seq = None

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
        "is_syn": is_syn,
        "is_ack": is_ack,
        "is_fin": is_fin,
        "is_rst": is_rst,
        "seq": seq,
    }