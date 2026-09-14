from CN.agent.flow.flow_key import create_flow_key


packet_1 = {
    "src_ip": "192.168.1.10",
    "dst_ip": "142.250.183.14",
    "src_port": 52143,
    "dst_port": 443,
    "protocol": "TCP"
}

packet_2 = {
    "src_ip": "142.250.183.14",
    "dst_ip": "192.168.1.10",
    "src_port": 443,
    "dst_port": 52143,
    "protocol": "TCP"
}


key_1 = create_flow_key(packet_1)
key_2 = create_flow_key(packet_2)

print("Flow 1:", key_1)
print("Flow 2:", key_2)
print("Same flow:", key_1 == key_2)