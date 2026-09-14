def create_flow_key(packet_data):
    """
    Create a normalized bidirectional flow key.

    Packets travelling in both directions between the same
    endpoints will produce the same flow key.
    """

    src = (
        packet_data["src_ip"],
        packet_data["src_port"]
    )

    dst = (
        packet_data["dst_ip"],
        packet_data["dst_port"]
    )

    protocol = packet_data["protocol"]

    # Sort the two endpoints so that
    # A -> B and B -> A produce the same key.
    endpoints = tuple(sorted([src, dst]))

    return (
        endpoints[0],
        endpoints[1],
        protocol
    )