from CN.agent.flow.flow_tracker import FlowTracker


tracker = FlowTracker()


packet_1 = {
    "time": 1000.0,
    "src_ip": "192.168.1.10",
    "dst_ip": "142.250.183.14",
    "src_port": 52143,
    "dst_port": 443,
    "protocol": "TCP",
    "packet_size": 500
}

packet_2 = {
    "time": 1001.0,
    "src_ip": "142.250.183.14",
    "dst_ip": "192.168.1.10",
    "src_port": 443,
    "dst_port": 52143,
    "protocol": "TCP",
    "packet_size": 800
}


tracker.add_packet(packet_1)
tracker.add_packet(packet_2)


print("Number of flows:", len(tracker.flows))

for flow in tracker.flows.values():
    print("Packets:", flow["packet_count"])
    print("Bytes:", flow["total_bytes"])
    print("Packet sizes:", flow["packet_sizes"])