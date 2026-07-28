"""
Runner script for Module 13: Automated Threat Response, Active Mitigation & Playbooks (SOAR).
Loads high-risk threat alerts, triggers automated response playbooks, enforces firewall block rules,
and logs incident mitigation history.

Usage:
    python scripts/run_soar.py --playbook dos_mitigation --target-ip 185.220.101.5
"""
import argparse
import logging
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.alert_engine import AlertEngine
from src.soar_engine import SOAREngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_soar")


def main():
    parser = argparse.ArgumentParser(description="NIDS SOAR Automated Threat Response & Active Mitigation Engine")
    parser.add_argument("--playbook", "-p", type=str, default="dos_mitigation", choices=["dos_mitigation", "port_scan_containment", "botnet_isolation", "auto"], help="Playbook to execute")
    parser.add_argument("--target-ip", "-i", type=str, default="185.220.101.5", help="Target IP address for active mitigation")
    parser.add_argument("--unblock", action="store_true", help="Unblock the target IP address")

    args = parser.parse_args()

    soar_engine = SOAREngine()

    if args.unblock:
        logger.info("Unblocking target IP: %s", args.target_ip)
        res = soar_engine.firewall.unblock_ip(args.target_ip)
        print(f"\n==========================================")
        print(f"UNBLOCK ACTION: {res}")
        print(f"==========================================\n")
        return

    logger.info("Starting Module 13: SOAR Automated Threat Response Engine...")

    # Construct alert payload
    sample_alert = {
        "id": f"ALT-SOAR-{int(time.time())}",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "attack_type": "DoS Hulk" if "dos" in args.playbook else "PortScan",
        "confidence": 0.998,
        "risk_score": 85.0,
        "risk_level": "Critical",
        "src_ip": args.target_ip,
        "dst_ip": "10.0.0.1",
        "protocol": "TCP",
        "dst_port": 80
    }

    result = soar_engine.execute_playbook(args.playbook, sample_alert)

    summary = soar_engine.get_summary()

    print("\n==========================================")
    print("MODULE 13: SOAR AUTOMATED THREAT MITIGATION SUMMARY")
    print("==========================================")
    print(f"Playbook Executed: {result.get('playbook')}")
    print(f"Target Malicious IP: {result.get('target_ip')}")
    print(f"Actions Enforced: {result.get('actions_taken')}")
    print(f"Active Firewall Block Rules: {summary.get('active_blocks_count')}")
    print(f"Total Response Playbooks Executed: {summary.get('total_playbooks_executed')}")
    print("==========================================\n")


if __name__ == "__main__":
    main()
