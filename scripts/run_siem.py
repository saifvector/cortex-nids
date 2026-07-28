"""
Runner script for Module 12: Enterprise SIEM & Threat Intelligence Integration.
Loads alerts, performs IOC matching, Threat Intelligence enrichment, and exports to
Elastic, Splunk, Sentinel, Syslog (CEF/LEEF), and Webhooks.

Usage:
    python scripts/run_siem.py
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
from src.siem_connector import SIEMConnectorManager
from src.utils.utils import get_absolute_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_siem")


def main():
    parser = argparse.ArgumentParser(description="NIDS Enterprise SIEM & Threat Intelligence Engine")
    parser.add_argument("--syslog-format", type=str, default="CEF", choices=["CEF", "LEEF", "RFC5424", "JSON"], help="Syslog message format")
    parser.add_argument("--webhook-url", type=str, default=None, help="Optional Webhook HTTP POST URL")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of alerts to process")

    args = parser.parse_args()

    logger.info("Starting Module 12: Enterprise SIEM & Threat Intelligence Pipeline...")

    alert_engine = AlertEngine()
    siem_manager = SIEMConnectorManager()
    siem_manager.syslog_exporter.log_format = args.syslog_format.upper()

    if args.webhook_url:
        siem_manager.webhook_dispatcher.add_endpoint(args.webhook_url)

    # Fetch recent alerts
    alerts = alert_engine.query_alerts(limit=args.limit)

    # If no alerts in database, generate sample alert to demonstrate pipeline
    if not alerts:
        logger.info("No stored alerts found in SQLite. Generating demonstration threat alert...")
        demo_alert = alert_engine.process_prediction(
            prediction_result={
                "Attack_Type": "DoS Hulk",
                "Prediction_Confidence": 0.9985,
                "Risk_Score": 82.5,
                "Risk_Level": "Critical",
                "Prediction_Time_ms": 0.028
            },
            src_ip="185.220.101.5",
            dst_ip="10.0.0.1",
            protocol="TCP",
            dst_port=80
        )
        alerts = [demo_alert]

    print(f"\n==========================================")
    print(f"PROCESSING {len(alerts)} ALERTS THROUGH SIEM PIPELINE")
    print(f"==========================================")

    processed_alerts = []
    for alert in alerts:
        enriched_alert = siem_manager.process_and_export_alert(alert)
        processed_alerts.append(enriched_alert)

    # Print Summary Report
    status = siem_manager.get_status()
    print("\n==========================================")
    print("MODULE 12: ENTERPRISE SIEM INTEGRATION SUMMARY")
    print("==========================================")
    print(f"Total Alerts Processed: {status.get('total_processed')}")
    print(f"Total Alerts Exported: {status.get('total_exported')}")
    print(f"Active Connectors: Elastic, Splunk HEC, Microsoft Sentinel, Syslog ({args.syslog_format})")
    print(f"IOC Rules Managed: {status.get('ioc_summary')}")
    print("==========================================\n")


if __name__ == "__main__":
    main()
