"""
Syslog Exporter module for NIDS.
Formats threat alerts into CEF, LEEF, RFC5424, and JSON formats, and exports them over UDP/TCP sockets to SIEM servers.
"""
import json
import logging
import socket
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SyslogExporter:
    """
    Formats and transmits threat alert logs to external SIEM syslog collectors over UDP/TCP.
    Supports CEF, LEEF, RFC5424, and JSON log specifications.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 514,
        protocol: str = "UDP",
        log_format: str = "CEF"
    ):
        self.host = host
        self.port = port
        self.protocol = protocol.upper()
        self.log_format = log_format.upper()
        self.exported_count = 0
        self.failure_count = 0

    def export_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Formats and transmits a single alert record to the configured Syslog endpoint.

        Returns:
            True if sent successfully, False otherwise.
        """
        formatted_msg = self.format_message(alert_data, self.log_format)
        success = self._send_syslog(formatted_msg)

        if success:
            self.exported_count += 1
            logger.info("Exported Syslog alert [%s] to %s:%d (%s format)",
                        alert_data.get("id"), self.host, self.port, self.log_format)
        else:
            self.failure_count += 1
            logger.error("Failed exporting Syslog alert [%s] to %s:%d",
                         alert_data.get("id"), self.host, self.port)

        return success

    def format_message(self, alert: Dict[str, Any], fmt: str = "CEF") -> str:
        """
        Formats alert dictionary into target log schema string.
        """
        alert_id = alert.get("id", "ALT-000")
        timestamp = alert.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))
        attack = alert.get("attack_type", "BENIGN")
        severity = alert.get("risk_level", "Low")
        score = alert.get("risk_score", 0)
        src_ip = alert.get("src_ip", "127.0.0.1")
        dst_ip = alert.get("dst_ip", "10.0.0.1")
        dst_port = alert.get("dst_port", 80)
        proto = alert.get("protocol", "TCP")

        sev_num = {"Low": 1, "Medium": 4, "High": 7, "Critical": 10}.get(severity, 1)

        if fmt == "CEF":
            # CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
            return (
                f"CEF:0|Cortex|NIDS-XDR|1.0.0|NIDS-{attack}|{attack} Intrusion Detected|"
                f"{sev_num}|src={src_ip} dst={dst_ip} dport={dst_port} proto={proto} "
                f"cn1={score} cn1Label=RiskScore msg=Confidence: {alert.get('confidence', 1.0)}"
            )

        elif fmt == "LEEF":
            # LEEF:1.0|Vendor|Product|Version|EventID|src=...|dst=...
            return (
                f"LEEF:1.0|Cortex|NIDS-XDR|1.0.0|{attack}|devTime={timestamp}\t"
                f"src={src_ip}\tdst={dst_ip}\tdstPort={dst_port}\tproto={proto}\t"
                f"sev={sev_num}\triskScore={score}"
            )

        elif fmt == "RFC5424":
            # <PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID STRUCTURED-DATA MSG
            return (
                f"<134>1 {timestamp} cortex-nids NIDS-ENGINE 1042 {alert_id} "
                f"[threat@cortex attack=\"{attack}\" risk=\"{score}\"] "
                f"Threat Alert: {attack} from {src_ip} targeting {dst_ip}:{dst_port}"
            )

        # Default JSON
        return json.dumps({
            "syslog_header": f"<134>1 {timestamp} cortex-nids NIDS-ENGINE",
            "alert": alert
        })

    def _send_syslog(self, message: str) -> bool:
        """Sends raw message bytes over UDP or TCP socket."""
        data = message.encode("utf-8")
        try:
            if self.protocol == "TCP":
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2.0)
                    s.connect((self.host, self.port))
                    s.sendall(data + b"\n")
            else:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.sendto(data, (self.host, self.port))
            return True
        except Exception as e:
            logger.debug("Syslog socket transmission failed: %s", e)
            return False
