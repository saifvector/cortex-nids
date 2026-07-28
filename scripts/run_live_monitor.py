"""
Runner script for Module 11: Real-Time Packet Capture & Live Intrusion Detection.
Starts live packet capture, aggregates flow features, executes ML inference, stores alerts,
and broadcasts threat telemetry.

Usage:
    python scripts/run_live_monitor.py --list-ifaces
    python scripts/run_live_monitor.py --interface default --duration 60
"""
import argparse
import logging
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.packet_capture import list_network_interfaces
from src.live_monitor import LiveMonitor
import logging
from src.utils.utils import get_absolute_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_live_monitor")


def main():
    parser = argparse.ArgumentParser(description="NIDS Real-Time Packet Capture & Live Intrusion Detection Engine")
    parser.add_argument("--interface", "-i", type=str, default=None, help="Network interface name/ID to sniff")
    parser.add_argument("--list-ifaces", action="store_true", help="List available network interfaces and exit")
    parser.add_argument("--duration", "-d", type=float, default=30.0, help="Monitoring duration in seconds (0 for continuous)")
    parser.add_argument("--filter", "-f", type=str, default="ip", help="BPF packet filter (default: 'ip')")

    args = parser.parse_args()

    if args.list_ifaces:
        ifaces = list_network_interfaces()
        print("\n==========================================")
        print("AVAILABLE NETWORK INTERFACES")
        print("==========================================")
        for ifc in ifaces:
            print(f" - Interface ID: {ifc.get('id')} | Name: {ifc.get('name')}")
        print("==========================================\n")
        return

    logger.info("Starting Module 11: Real-Time Packet Capture & Live Intrusion Detection Engine...")

    monitor = LiveMonitor(
        interface=args.interface,
        bpf_filter=args.filter
    )

    try:
        monitor.start_monitoring()
        logger.info("Live Monitoring active. Running for %s seconds (Press Ctrl+C to stop)...", "continuous" if args.duration <= 0 else args.duration)

        start_time = time.time()
        while monitor.is_running:
            time.sleep(0.5)
            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                logger.info("Reached target monitoring duration (%s seconds).", args.duration)
                break

    except KeyboardInterrupt:
        logger.info("User interrupted live monitoring session.")
    finally:
        monitor.stop_monitoring()

        # Print Daily Report Summary
        report = monitor.alert_engine.generate_daily_report()
        print("\n==========================================")
        print("MODULE 11: LIVE INTRUSION MONITOR SUMMARY")
        print("==========================================")
        print(f"Date: {report.get('date')}")
        print(f"Total Live Alerts Generated: {report.get('total_alerts')}")
        print(f"Attack Counts: {report.get('attack_counts')}")
        print(f"Risk Counts: {report.get('risk_counts')}")
        print(f"Average Confidence: {report.get('average_confidence', 0) * 100:.2f}%")
        print(f"Average Risk Score: {report.get('average_risk_score', 0)} / 100")
        print("==========================================\n")


if __name__ == "__main__":
    main()
