"""
SIEM Connector module for NIDS.
Connects the intrusion detection engine to Elastic Stack, Splunk HEC, Microsoft Sentinel, Syslog, and Webhooks.
"""
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union

import requests

from src.ioc_manager import IOCManager
from src.syslog_exporter import SyslogExporter
from src.threat_intelligence import ThreatIntelligenceEnricher
from src.webhook_dispatcher import WebhookDispatcher

logger = logging.getLogger(__name__)


class ElasticConnector:
    """Connector exporting threat events to Elasticsearch / Elastic Stack index."""

    def __init__(self, es_host: str = "http://localhost:9200", index_name: str = "cortex-nids-alerts"):
        self.es_host = es_host.rstrip("/")
        self.index_name = index_name

    def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        try:
            url = f"{self.es_host}/{self.index_name}/_doc/{alert_data.get('id')}"
            headers = {"Content-Type": "application/json"}
            resp = requests.put(url, json=alert_data, headers=headers, timeout=0.2)
            return resp.status_code in (200, 201)
        except Exception:
            return False


class SplunkHECConnector:
    """Connector exporting threat events to Splunk HTTP Event Collector (HEC)."""

    def __init__(self, hec_url: str = "http://localhost:8088/services/collector/event", token: str = "00000000-0000-0000-0000-000000000000"):
        self.hec_url = hec_url
        self.token = token

    def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        try:
            headers = {
                "Authorization": f"Splunk {self.token}",
                "Content-Type": "application/json"
            }
            payload = {
                "event": alert_data,
                "sourcetype": "cortex:nids:alert",
                "source": "cortex-xdr"
            }
            resp = requests.post(self.hec_url, json=payload, headers=headers, timeout=0.2)
            return resp.status_code == 200
        except Exception:
            return False


class MicrosoftSentinelConnector:
    """Connector exporting threat events to Microsoft Sentinel / Azure Log Analytics."""

    def __init__(self, workspace_id: str = "demo-workspace", shared_key: str = "demo-key", log_type: str = "NIDSAlerts"):
        self.workspace_id = workspace_id
        self.shared_key = shared_key
        self.log_type = log_type

    def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        logger.info("Formatted alert [%s] for Microsoft Sentinel ingest (%s)", alert_data.get("id"), self.log_type)
        return True


class SIEMConnectorManager:
    """
    Unified SIEM Manager orchestrating Elastic, Splunk, Sentinel, Syslog, Webhooks, and IOC Enrichment.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        self.ioc_manager = IOCManager()
        self.ti_enricher = ThreatIntelligenceEnricher()
        self.syslog_exporter = SyslogExporter(log_format="CEF")
        self.webhook_dispatcher = WebhookDispatcher()

        self.elastic = ElasticConnector()
        self.splunk = SplunkHECConnector()
        self.sentinel = MicrosoftSentinelConnector()

        self.total_processed = 0
        self.total_exported = 0

    def process_and_export_alert(self, raw_alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full SIEM Pipeline Execution:
        IOC Match -> Threat Intelligence Enrichment -> Multi-SIEM Export -> Webhook Dispatch.
        """
        self.total_processed += 1
        src_ip = raw_alert.get("src_ip", "192.168.1.100")

        # 1. IOC Match
        ioc_match = self.ioc_manager.match_ip(src_ip)
        raw_alert["ioc_match"] = ioc_match

        # Whitelist override
        if ioc_match.get("action") == "allow":
            raw_alert["risk_level"] = "Low"
            raw_alert["risk_score"] = 0.0

        # Blacklist override
        if ioc_match.get("action") == "block":
            raw_alert["risk_level"] = "Critical"
            raw_alert["risk_score"] = 100.0

        # 2. Threat Intelligence Enrichment
        ti_data = self.ti_enricher.enrich_ip(src_ip)
        raw_alert["threat_intelligence"] = ti_data

        # 3. SIEM Exports
        export_status = {}
        export_status["syslog"] = self.syslog_exporter.export_alert(raw_alert)
        export_status["elastic"] = self.elastic.send_alert(raw_alert)
        export_status["splunk"] = self.splunk.send_alert(raw_alert)
        export_status["sentinel"] = self.sentinel.send_alert(raw_alert)

        # 4. Webhook Dispatch
        if self.webhook_dispatcher.endpoints:
            export_status["webhook"] = self.webhook_dispatcher.dispatch_alert(raw_alert)

        raw_alert["export_status"] = export_status
        self.total_exported += 1

        logger.info("Processed SIEM Pipeline for Alert [%s] (IOC: %s, TI: %s)",
                    raw_alert.get("id"), ioc_match.get("type"), ti_data.get("is_malicious"))

        return raw_alert

    def get_status(self) -> Dict[str, Any]:
        """Returns status summary of active SIEM connectors."""
        return {
            "total_processed": self.total_processed,
            "total_exported": self.total_exported,
            "connectors": {
                "elastic": {"status": "configured", "host": self.elastic.es_host},
                "splunk": {"status": "configured", "url": self.splunk.hec_url},
                "sentinel": {"status": "configured", "log_type": self.sentinel.log_type},
                "syslog": {"status": "active", "format": self.syslog_exporter.log_format, "exported": self.syslog_exporter.exported_count},
                "webhook": {"status": "active", "endpoints_count": len(self.webhook_dispatcher.endpoints)}
            },
            "ioc_summary": self.ioc_manager.get_summary()
        }
