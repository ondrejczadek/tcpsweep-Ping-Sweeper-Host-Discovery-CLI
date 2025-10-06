#!/usr/bin/env python3
"""
tcp_sweep.py - simple TCP probe sweeper (connect scan)
Usage:
    tcpsweep <targets> <port|ports> [--timeout S] [--threads N]
Examples:
    tcpsweep 192.168.1.0/24 22 --threads 100
    tcpsweep 10.0.0.1-10 80,443 --timeout 1.5 --threads 50
"""

import socket
import sys
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# --------------------------
# helper: parse ip range (CIDR or start-end or single IP)
# --------------------------
def generate_ips(range_str):
    if '/' in range_str:
        net = ipaddress.ip_network(range_str, strict=False)
        return [str(ip) for ip in net.hosts()]
    elif '-' in range_str:
        start_str, end_str = range_str.split('-', 1)
        start = ipaddress.IPv4Address(start_str.strip())
        end = ipaddress.IPv4Address(end_str.strip())
        return [str(ipaddress.IPv4Address(i)) for i in range(int(start), int(end)+1)]
    else:
        return [range_str]

# --------------------------
# helper: parse ports string (e.g., "22" or "22,80,443" or "20-25")
# --------------------------
def parse_ports(ports_str):
    parts = ports_str.split(',')
    ports = set()
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if '-' in p:
            a,b = p.split('-',1)
            a = int(a); b = int(b)
            if a > b: a,b = b,a
            ports.update(range(a, b+1))
        else:
            ports.add(int(p))
    return sorted([pt for pt in ports if 1 <= pt <= 65535])

# --------------------------
# single TCP probe (connect)
# --------------------------
def probe_tcp(ip, port, timeout=1.0):
    """
    Try to connect to ip:port. Returns (ip, port, True/False, error_or_rtt)
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    start = time.time()
    try:
        s.connect((ip, port))
        elapsed = (time.time() - start) * 1000.0  # ms
        s.close()
        return (ip, port, True, elapsed)
    except (socket.timeout, ConnectionRefusedError) as e:
        # timeout or refused: not open
        return (ip, port, False, str(e))
    except Exception as e:
        return (ip, port, False, str(e))

# --------------------------
# main: run sweep
# --------------------------
def tcp_sweep(targets_str, ports_str, timeout=1.0, threads=100):
    ips = generate_ips(targets_str)
    ports = parse_ports(ports_str)
    print(f"[+] TCP sweep targets: {len(ips)} IPs, ports: {ports}, threads: {threads}, timeout: {timeout}s")
    open_results = []  # tuples (ip, port, rtt_ms)
    start_all = time.time()

    # we will probe every (ip,port) pair concurrently up to threads * workers
    tasks = []
    with ThreadPoolExecutor(max_workers=threads) as ex:
        future_to_pair = {}
        for ip in ips:
            for port in ports:
                fut = ex.submit(probe_tcp, ip, port, timeout)
                future_to_pair[fut] = (ip, port)
        for fut in as_completed(future_to_pair):
            try:
                ip, port, is_open, info = fut.result()
            except Exception as e:
                continue
            if is_open:
                open_results.append((ip, port, info))
                print(f"[OPEN] {ip}:{port}  rtt={info:.1f}ms")
            # optional: print closed results if debugging
            # else:
            #     print(f"[closed] {ip}:{port}  reason={info}")

    total_time = time.time() - start_all
    print(f"[+] Sweep finished in {total_time:.2f}s. Open: {len(open_results)}")
    return open_results

# --------------------------
# CLI
# --------------------------
def usage():
    print("Usage: tcpsweep <targets> <port|ports> [--timeout S] [--threads N]")
    print("Examples:")
    print("  tcpsweep 192.168.1.0/24 22 --threads 200")
    print("  tcpsweep 10.0.0.1-10 80,443 --timeout 1.5 --threads 50")
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        usage()

    targets = sys.argv[1]
    ports_arg = sys.argv[2]
    timeout = 1.0
    threads = 100

    if "--timeout" in sys.argv:
        i = sys.argv.index("--timeout"); timeout = float(sys.argv[i+1])
    if "--threads" in sys.argv:
        i = sys.argv.index("--threads"); threads = int(sys.argv[i+1])

    tcp_sweep(targets, ports_arg, timeout=timeout, threads=threads)
