# pingsweep — Ping Sweeper / Host Discovery (CLI)

**pingsweep** is a simple command-line host discovery tool for educational and authorized network testing.  
It probes a range of IP addresses to discover which hosts are *alive* using multiple methods: ICMP (ping), TCP probe (connect to a port), and ARP (local network). Results can be printed to console and/or exported to CSV.

> ⚠️ Only run pingsweep on networks and hosts you own or have explicit permission to test. Unauthorized scanning may be illegal or disruptive.

---

## Features

- Host discovery via:
  - **ICMP Echo** (ping)
  - **TCP probe** (connect to a chosen port, e.g., 80 or 443)
  - **ARP sweep** (local LAN only; reliable for devices on same Ethernet segment)
- Accepts CIDR notation (e.g., `192.168.1.0/24`) or explicit ranges (`192.168.1.1-192.168.1.50`) and single IPs.
- Parallel scanning with configurable thread pool for speed.
- Configurable timeout and thread count.
- Optional CSV export of discovered hosts and metadata (RTT, MAC, method).
- Lightweight and easy to extend for additional techniques.

---

## Prerequisites

- **Python 3.8+** installed and available as `python` in PATH.
- Standard library used for ICMP (via system `ping`) and TCP connect.  
- For ARP mode (recommended in LAN):
  - **scapy** library and root/Administrator privileges:
    ```bash
    pip install scapy
    ```
  - On Windows, run terminal as Administrator; on Linux/macOS, run as root or use `sudo`.

Notes:
- ICMP raw sockets require admin/root if you implement raw ICMP in Python; the recommended implementation uses the system `ping` command to avoid privilege issues.
- ARP mode only works on the same local segment (does not traverse routers).

---

## Files

Place these files in the same folder (e.g., `C:\Users\you\tools\pingsweep\`):

- `pingsweep.py` — the Python script
- `pingsweep.bat` — optional Windows launcher

**`pingsweep.bat` example content:**

```bat
@echo off
set script=%~n0.py
python "%~dp0%script%" %*
```
- `%~dp0` runs the script from the `.bat` folder.
- `%*` forwards all CLI arguments.

---

## Usage / Syntax

`pingsweep <targets> --method <icmp|tcp|arp> [--port P] [--timeout S] [--threads N] [--csv out.csv]`

- `<targets>` — CIDR (e.g. `192.168.1.0/24`), range (`192.168.1.1-192.168.1.50`) or single IP.
- `--method` — discovery method (`icmp`, `tcp`, or `arp`). ARP requires local LAN and scapy/root.
- `--port P` — (TCP mode) port to probe (default: 80).
- `--timeout S` — timeout in seconds for each probe (default: 1.0).
- `--threads N` — number of parallel workers (default: 50).
- `--csv out.csv` — optional: save results to CSV.

### Examples

ICMP sweep of a /24 network:
`pingsweep 192.168.1.0/24 --method icmp --timeout 1 --threads 100 --csv alive.csv`

TCP probe (port 80) for a small range:
`pingsweep 10.0.0.1-10 --method tcp --port 80 --timeout 0.8 --threads 40`

ARP sweep (LAN only):
`# On Linux/macOS run with sudo; on Windows run as Administrator pingsweep 192.168.1.0/24 --method arp --threads 100 --csv arp_results.csv`

---

## How It Works

### ICMP

- Uses the system `ping` command (`ping -n 1 -w` on Windows, `ping -c 1 -W` on Unix) to send a single echo request and determine reachability and RTT.
- Recommended because it avoids raw socket privileges; however, many networks block ICMP → false negatives possible.

### TCP probe

- Attempts a `socket.connect()` to the specified port. Successful connect indicates the host is reachable and the port is open.
- Works where ICMP is blocked but services are running.
- Less stealthy than ICMP; may trigger security alerts.

### ARP sweep

- Sends ARP who-has requests on the local Ethernet segment and listens for ARP replies (provides MAC address).
- Most reliable for LAN host discovery; does not work across routers.
- Requires scapy and root/Administrator privileges.

---

## Output

- Default console output lists discovered hosts and basic metadata:
    - IP address
    - Method used (ICMP/TCP/ARP)
    - RTT for ICMP/TCP probes (if applicable)
    - MAC address for ARP mode
        
- CSV columns when using `--csv`: `ip,method,rtt_ms,mac,notes`
    

---

## Troubleshooting

- **'python' is not recognized**
    - Add Python to PATH or use full path in `.bat`.
        
- **ICMP shows no hosts but you know devices exist**
    - Many devices/firewalls block ICMP. Try `--method tcp` with a commonly open port (80, 443) or run an ARP sweep on the LAN.
        
- **ARP mode shows nothing**
    - Ensure you are on the same subnet and running with root/Administrator. Check scapy installation.
        
- **Permission errors**
    - ARP or raw socket modes require privileges; run with appropriate elevation. Avoid running with unnecessary root privileges.
        
- **Too slow/too fast**
    - Adjust `--threads` and `--timeout`. High parallelism can flood networks or cause false negatives due to transient packet loss.

---

## Optional Enhancements

- Add ICMP via raw sockets (requires admin) for more control and timing info.
- Add exponential backoff and retries for transient packet loss.
- Implement asynchronous (asyncio) probing for higher scalability.
- Combine methods automatically: ARP → ICMP → TCP fallbacks for robust discovery.
- Add vendor lookup (OUI) for MAC addresses in ARP results.
- GUI or simple web report for results visualization.

---

## Security & Ethics

- Only scan networks and hosts you own or have explicit permission to test.
- Scanning public networks aggressively may trigger IDS/IPS or violate policies.
- Keep scanning rates reasonable and document tests when performing authorized assessments.

---

## Quick Start Checklist

1. Place `pingsweep.py` (and `pingsweep.bat` if desired) in a folder.
2. Ensure Python 3.8+ is installed.
3. (For ARP mode) install scapy and run with root/Administrator:
	`pip install scapy`

4. Open a new terminal (important after PATH changes).
5. Test locally:
	`pingsweep 127.0.0.1 --method tcp --port 80`

6. Run a network sweep (example):
	`pingsweep 192.168.1.0/24 --method icmp --threads 100 --timeout 1 --csv alive.csv`