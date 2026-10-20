"""
generate_sample_pcap.py
-----------------------
Utility to generate reference PCAP files with Scapy for testing, offline replay,
and environments where live Npcap capture is not yet configured.

Creates realistic TCP/IP packet captures for:
- Tier 1: Naive bot (fixed 0.5s intervals)
- Tier 2: Jittered bot (variable intervals, search endpoint)
- Tier 3: Mimicking bot (multi-endpoint browsing sequence)
"""

import os
import time
import random
from scapy.all import IP, TCP, Raw, wrpcap

def build_tcp_handshake(src_ip, src_port, dst_ip, dst_port, t_start=0.0):
    """Generate 3-way TCP handshake packets."""
    syn = IP(src=src_ip, dst=dst_ip) / TCP(sport=src_port, dport=dst_port, flags="S", seq=1000)
    syn.time = t_start

    syn_ack = IP(src=dst_ip, dst=src_ip) / TCP(sport=dst_port, dport=src_port, flags="SA", seq=5000, ack=1001)
    syn_ack.time = t_start + 0.001

    ack = IP(src=src_ip, dst=dst_ip) / TCP(sport=src_port, dport=dst_port, flags="A", seq=1001, ack=5001)
    ack.time = t_start + 0.002

    return [syn, syn_ack, ack], 1001, 5001, t_start + 0.005


def build_http_exchange(src_ip, src_port, dst_ip, dst_port, http_req, http_resp, seq_c, seq_s, t_req):
    """Generate HTTP request and response packets over TCP."""
    req_payload = http_req.encode("utf-8")
    resp_payload = http_resp.encode("utf-8")

    # Client HTTP request
    req_pkt = IP(src=src_ip, dst=dst_ip) / TCP(sport=src_port, dport=dst_port, flags="PA", seq=seq_c, ack=seq_s) / Raw(load=req_payload)
    req_pkt.time = t_req

    seq_c += len(req_payload)
    t_resp = t_req + 0.008

    # Server HTTP response
    resp_pkt = IP(src=dst_ip, dst=src_ip) / TCP(sport=dst_port, dport=src_port, flags="PA", seq=seq_s, ack=seq_c) / Raw(load=resp_payload)
    resp_pkt.time = t_resp

    seq_s += len(resp_payload)
    t_ack = t_resp + 0.002

    # Client ACK for response
    ack_pkt = IP(src=src_ip, dst=dst_ip) / TCP(sport=src_port, dport=dst_port, flags="A", seq=seq_c, ack=seq_s)
    ack_pkt.time = t_ack

    return [req_pkt, resp_pkt, ack_pkt], seq_c, seq_s, t_ack + 0.001


def build_tcp_teardown(src_ip, src_port, dst_ip, dst_port, seq_c, seq_s, t_fin):
    """Generate TCP connection teardown packets."""
    fin_c = IP(src=src_ip, dst=dst_ip) / TCP(sport=src_port, dport=dst_port, flags="FA", seq=seq_c, ack=seq_s)
    fin_c.time = t_fin

    ack_s = IP(src=dst_ip, dst=src_ip) / TCP(sport=dst_port, dport=src_port, flags="A", seq=seq_s, ack=seq_c + 1)
    ack_s.time = t_fin + 0.001

    fin_s = IP(src=dst_ip, dst=src_ip) / TCP(sport=dst_port, dport=src_port, flags="FA", seq=seq_s, ack=seq_c + 1)
    fin_s.time = t_fin + 0.002

    ack_c = IP(src=src_ip, dst=dst_ip) / TCP(sport=src_port, dport=dst_port, flags="A", seq=seq_c + 1, ack=seq_s + 1)
    ack_c.time = t_fin + 0.003

    return [fin_c, ack_s, fin_s, ack_c]


def generate_tier1_pcap(filepath: str, n_requests: int = 10, interval: float = 0.5):
    """Generate Tier 1 (Naive bot) PCAP file."""
    src_ip, src_port = "127.0.0.1", 50001
    dst_ip, dst_port = "127.0.0.1", 5000
    base_time = time.time() - (n_requests * interval + 5)

    packets, seq_c, seq_s, t_cur = build_tcp_handshake(src_ip, src_port, dst_ip, dst_port, base_time)

    req_str = "GET / HTTP/1.1\r\nHost: 127.0.0.1:5000\r\nUser-Agent: SentinelNet-NaiveBot/1.0\r\n\r\n"
    resp_str = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 140\r\n\r\n<html><body><h1>SentinelNet Test Server</h1></body></html>"

    for _ in range(n_requests):
        exchange, seq_c, seq_s, _ = build_http_exchange(
            src_ip, src_port, dst_ip, dst_port, req_str, resp_str, seq_c, seq_s, t_cur
        )
        packets.extend(exchange)
        t_cur += interval

    packets.extend(build_tcp_teardown(src_ip, src_port, dst_ip, dst_port, seq_c, seq_s, t_cur))
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    wrpcap(filepath, packets)
    return filepath


def generate_tier2_pcap(filepath: str, n_requests: int = 10):
    """Generate Tier 2 (Jittered bot) PCAP file."""
    src_ip, src_port = "127.0.0.1", 50002
    dst_ip, dst_port = "127.0.0.1", 5000
    base_time = time.time() - 30.0
    rng = random.Random(42)

    packets, seq_c, seq_s, t_cur = build_tcp_handshake(src_ip, src_port, dst_ip, dst_port, base_time)

    for i in range(n_requests):
        query = rng.choice(["security", "threat", "firewall", "ids"])
        req_str = f"GET /search?q={query} HTTP/1.1\r\nHost: 127.0.0.1:5000\r\nUser-Agent: SentinelNet-JitterBot/2.0\r\n\r\n"
        resp_str = f'{{"status": "ok", "query": "{query}", "results_count": 3}}'
        resp_http = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(resp_str)}\r\n\r\n{resp_str}"

        exchange, seq_c, seq_s, _ = build_http_exchange(
            src_ip, src_port, dst_ip, dst_port, req_str, resp_http, seq_c, seq_s, t_cur
        )
        packets.extend(exchange)
        t_cur += rng.uniform(0.3, 2.5)

    packets.extend(build_tcp_teardown(src_ip, src_port, dst_ip, dst_port, seq_c, seq_s, t_cur))
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    wrpcap(filepath, packets)
    return filepath


def generate_tier3_pcap(filepath: str, n_cycles: int = 3):
    """Generate Tier 3 (Mimicking bot) PCAP file."""
    src_ip, src_port = "127.0.0.1", 50003
    dst_ip, dst_port = "127.0.0.1", 5000
    base_time = time.time() - 60.0
    rng = random.Random(123)

    packets, seq_c, seq_s, t_cur = build_tcp_handshake(src_ip, src_port, dst_ip, dst_port, base_time)

    endpoints = [
        ("/", "GET", "<html><head><title>Test</title></head></html>"),
        ("/search?q=packet", "GET", '{"query": "packet", "results_count": 3}'),
        ("/product/101", "GET", '{"product_id": 101, "price": 20.99}'),
        ("/login", "POST", '{"status": "authenticated", "token": "xyz123"}'),
    ]

    for _ in range(n_cycles):
        for path, method, resp_body in endpoints:
            if method == "GET":
                req_str = f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1:5000\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n\r\n"
            else:
                body = '{"username": "admin"}'
                req_str = f"POST {path} HTTP/1.1\r\nHost: 127.0.0.1:5000\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\n\r\n{body}"

            resp_http = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(resp_body)}\r\n\r\n{resp_body}"

            exchange, seq_c, seq_s, _ = build_http_exchange(
                src_ip, src_port, dst_ip, dst_port, req_str, resp_http, seq_c, seq_s, t_cur
            )
            packets.extend(exchange)
            t_cur += rng.uniform(0.5, 3.0)

    packets.extend(build_tcp_teardown(src_ip, src_port, dst_ip, dst_port, seq_c, seq_s, t_cur))
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    wrpcap(filepath, packets)
    return filepath


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")

    p1 = os.path.join(data_dir, "tier1_sample.pcap")
    p2 = os.path.join(data_dir, "tier2_sample.pcap")
    p3 = os.path.join(data_dir, "tier3_sample.pcap")

    generate_tier1_pcap(p1)
    generate_tier2_pcap(p2)
    generate_tier3_pcap(p3)

    print(f"[+] Generated sample PCAPs in {data_dir}:")
    print(f"    - {p1}")
    print(f"    - {p2}")
    print(f"    - {p3}")
