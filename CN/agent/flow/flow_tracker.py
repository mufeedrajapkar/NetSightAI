from .flow_key import create_flow_key


class FlowTracker:

    def __init__(self):
        self.flows = {}

    def add_packet(self, packet_data):

        flow_key = create_flow_key(packet_data)

        if flow_key not in self.flows:
            self.flows[flow_key] = {
                "flow_key": flow_key,
                "first_seen": packet_data["time"],
                "last_seen": packet_data["time"],
                "packet_count": 0,
                "total_bytes": 0,
                "packet_sizes": [],
                "timestamps": [],
                "protocol": packet_data["protocol"]
            }

        flow = self.flows[flow_key]

        flow["last_seen"] = packet_data["time"]
        flow["packet_count"] += 1
        flow["total_bytes"] += packet_data["packet_size"]
        flow["packet_sizes"].append(packet_data["packet_size"])
        flow["timestamps"].append(packet_data["time"])

        return flow