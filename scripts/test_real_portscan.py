"""
Real Port Scan Generator for Cortex NIDS Testing.
Executes an actual TCP socket connection sweep across real local ports
to trigger and verify the PortScan intrusion detection classifier in real time.

Usage:
    python scripts/test_real_portscan.py
"""
import socket
import time
import sys

TARGET_HOST = "127.0.0.1"
SCAN_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445,
    993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 8080, 8443
]

def main():
    print("=" * 65)
    print("  CORTEX NIDS - REAL PORT SCAN GENERATOR")
    print("=" * 65)
    print(f"  Target Host : {TARGET_HOST}")
    print(f"  Total Ports : {len(SCAN_PORTS)}")
    print("  Initiating real TCP handshake sweep across ports...")
    print("=" * 65 + "\n")

    start_t = time.time()
    for port in SCAN_PORTS:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.05)
        try:
            res = s.connect_ex((TARGET_HOST, port))
            status = "OPEN" if res == 0 else "CLOSED / FILTERED"
            print(f"  [REAL PROBE] {TARGET_HOST}:{port:<5} -> Status: {status}")
        except Exception as e:
            print(f"  [ERROR] Port {port}: {e}")
        finally:
            s.close()
        time.sleep(0.03)

    elapsed = (time.time() - start_t) * 1000
    print("\n" + "=" * 65)
    print(f"  SCAN FINISHED: Completed in {elapsed:.2f} ms")
    print("  Check your Live Threat Stream dashboard at http://localhost:3000")
    print("=" * 65)

if __name__ == "__main__":
    main()

