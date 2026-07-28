"""
Webhook Dispatcher module for NIDS.
Sends threat alerts to external HTTP webhooks with automated retry logic and delivery logs.
"""
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests

from src.utils.utils import ensure_directory, get_absolute_path, save_json

logger = logging.getLogger(__name__)


class WebhookDispatcher:
    """
    Handles HTTP POST webhook notifications with automatic retry, backoff, and delivery logging.
    """

    def __init__(
        self,
        endpoints: Optional[List[str]] = None,
        max_retries: int = 3,
        retry_delay_sec: float = 1.0,
        log_path: Union[str, Path] = "predictions/webhook_delivery.json"
    ):
        self.endpoints = endpoints or []
        self.max_retries = max_retries
        self.retry_delay = retry_delay_sec
        self.log_path = get_absolute_path(log_path)
        ensure_directory(self.log_path.parent)

        self.delivery_history: List[Dict[str, Any]] = []

    def add_endpoint(self, url: str) -> None:
        """Adds a target webhook URL endpoint."""
        if url not in self.endpoints:
            self.endpoints.append(url)
            logger.info("Added webhook endpoint: %s", url)

    def dispatch_alert(self, alert_data: Dict[str, Any], target_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Dispatches alert JSON payload to configured endpoints or target_url.

        Returns:
            Dictionary summary of delivery attempt.
        """
        urls = [target_url] if target_url else self.endpoints
        if not urls:
            logger.warning("No webhook endpoints configured for alert dispatch.")
            return {"status": "skipped", "message": "No endpoints configured"}

        overall_status = True
        results = []

        for url in urls:
            success = self._send_with_retry(url, alert_data)
            results.append({"url": url, "success": success})
            if not success:
                overall_status = False

        record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "alert_id": alert_data.get("id"),
            "overall_success": overall_status,
            "dispatches": results
        }

        self.delivery_history.append(record)
        self._save_delivery_log()

        return record

    def _send_with_retry(self, url: str, alert_data: Dict[str, Any]) -> bool:
        """Sends HTTP POST payload to url with retry logic."""
        headers = {"Content-Type": "application/json", "User-Agent": "Cortex-NIDS-XDR/1.0"}

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.post(url, json=alert_data, headers=headers, timeout=4.0)
                if resp.status_code in (200, 201, 202, 204):
                    logger.info("Successfully dispatched alert [%s] to webhook %s (Attempt %d)",
                                alert_data.get("id"), url, attempt)
                    return True
                else:
                    logger.warning("Webhook %s returned status %d on attempt %d", url, resp.status_code, attempt)
            except Exception as e:
                logger.warning("Webhook dispatch error to %s on attempt %d: %s", url, attempt, e)

            if attempt < self.max_retries:
                time.sleep(self.retry_delay * attempt)

        logger.error("Failed dispatching alert [%s] to webhook %s after %d retries.",
                     alert_data.get("id"), url, self.max_retries)
        return False

    def _save_delivery_log(self) -> None:
        """Saves delivery history to JSON log file."""
        try:
            save_json({"delivery_history": self.delivery_history[-500:]}, self.log_path)
        except Exception as e:
            logger.error("Failed saving webhook delivery log: %s", e)
