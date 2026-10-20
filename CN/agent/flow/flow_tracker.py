from .flow_key import create_flow_key


class FlowTracker:

    def __init__(self, udp_idle_timeout=5.0, tcp_idle_timeout=30.0):
        self.flows = {}
        self.udp_idle_timeout = udp_idle_timeout
        self.tcp_idle_timeout = tcp_idle_timeout

    def add_packet(self, packet_data):

        flow_key = create_flow_key(packet_data)
        protocol = packet_data.get("protocol", "OTHER")
        pkt_time = packet_data["time"]
        is_syn = packet_data.get("is_syn", False)
        is_ack = packet_data.get("is_ack", False)
        is_fin = packet_data.get("is_fin", False)
        is_rst = packet_data.get("is_rst", False)
        seq = packet_data.get("seq", None)

        if flow_key not in self.flows:
            # Initialize TCP connection state
            if protocol == "TCP":
                if is_syn and not is_ack:
                    tcp_state = "SYN_SENT"
                    active_isn = seq
                else:
                    # Mid-capture start (e.g. data or ACK packet observed first)
                    tcp_state = "ESTABLISHED"
                    active_isn = seq
            else:
                tcp_state = None
                active_isn = None

            self.flows[flow_key] = {
                "flow_key": flow_key,
                "first_seen": pkt_time,
                "last_seen": pkt_time,
                "packet_count": 0,
                "total_bytes": 0,
                "packet_sizes": [],
                "timestamps": [],
                "protocol": protocol,
                "num_connections": 1,
                "tcp_state": tcp_state,
                "active_isn": active_isn,
            }

        flow = self.flows[flow_key]

        # Connection lifecycle logic for subsequent packets
        if flow["packet_count"] > 0:
            if protocol == "TCP":
                if is_fin or is_rst:
                    flow["tcp_state"] = "CLOSING"
                elif is_syn and not is_ack:
                    # A SYN packet on an existing flow:
                    # Check if it is a retransmission of the active SYN (same ISN during SYN_SENT / ESTABLISHED)
                    if flow["tcp_state"] in ("SYN_SENT", "ESTABLISHED") and seq is not None and flow["active_isn"] == seq:
                        # SYN Retransmission: deduplicate (do not increment num_connections)
                        pass
                    elif flow["tcp_state"] in ("CLOSING", "CLOSED"):
                        # 5-Tuple Reuse after connection teardown: new connection attempt
                        flow["num_connections"] += 1
                        flow["tcp_state"] = "SYN_SENT"
                        flow["active_isn"] = seq
                    elif (pkt_time - flow["last_seen"]) > self.tcp_idle_timeout:
                        # 5-Tuple Reuse after prolonged idle timeout
                        flow["num_connections"] += 1
                        flow["tcp_state"] = "SYN_SENT"
                        flow["active_isn"] = seq
                    elif seq is not None and flow["active_isn"] is not None and seq != flow["active_isn"]:
                        # New connection attempt with new sequence number
                        flow["num_connections"] += 1
                        flow["tcp_state"] = "SYN_SENT"
                        flow["active_isn"] = seq
                elif is_ack and not is_syn:
                    if flow["tcp_state"] == "SYN_SENT":
                        flow["tcp_state"] = "ESTABLISHED"

            elif protocol == "UDP":
                # UDP pseudo-connection: count new transaction if idle gap exceeds timeout
                idle_gap = pkt_time - flow["last_seen"]
                if idle_gap > self.udp_idle_timeout:
                    flow["num_connections"] += 1

        # Accumulate flow statistics
        flow["last_seen"] = pkt_time
        flow["packet_count"] += 1
        flow["total_bytes"] += packet_data["packet_size"]
        flow["packet_sizes"].append(packet_data["packet_size"])
        flow["timestamps"].append(pkt_time)

        return flow