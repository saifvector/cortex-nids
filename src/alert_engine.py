"""
Alert Engine module for NIDS.
Processes live predictions, generates alert events, persists them to SQLite, CSV, and JSON,
and provides multi-criteria filtering and report generation capabilities.
"""
import json
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

from src.utils.utils import ensure_directory, get_absolute_path, save_json

logger = logging.getLogger(__name__)


class AlertEngine:
    """
    Manages threat alert generation, SQLite persistence, CSV/JSON exporting,
    and multi-parameter filtering & reporting.
    """

    def __init__(self, db_dir: Union[str, Path] = "predictions"):
        self.db_dir = ensure_directory(db_dir)
        self.sqlite_path = self.db_dir / "alerts.db"
        self.csv_path = self.db_dir / "live_alerts.csv"
        self.json_path = self.db_dir / "live_alerts.json"

        self._init_sqlite_db()

    def _init_sqlite_db(self) -> None:
        """Initializes SQLite alerts database table schema."""
        try:
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT,
                        attack_type TEXT,
                        confidence REAL,
                        risk_score REAL,
                        risk_level TEXT,
                        src_ip TEXT,
                        dst_ip TEXT,
                        protocol TEXT,
                        dst_port INTEGER,
                        prediction_time_ms REAL,
                        class_probabilities TEXT
                    )
                """)
                conn.commit()
            logger.info("Initialized SQLite alert database at %s", self.sqlite_path)
        except Exception as e:
            logger.error("Failed to initialize SQLite database: %s", e)

    def process_prediction(
        self,
        prediction_result: Dict[str, Any],
        src_ip: str = "192.168.1.100",
        dst_ip: str = "10.0.0.1",
        protocol: str = "TCP",
        dst_port: int = 80
    ) -> Dict[str, Any]:
        """
        Processes a raw prediction result, attaches metadata, and persists the alert event.

        Args:
            prediction_result: Output dictionary from NIDSPredictor.
            src_ip: Source IP address.
            dst_ip: Destination IP address.
            protocol: IP Protocol name.
            dst_port: Destination port integer.

        Returns:
            Structured alert event dictionary.
        """
        now = datetime.now()
        alert_id = f"ALT-{now.strftime('%Y%m%d%H%M%S')}-{int(time.time() * 1000) % 1000}"

        alert_event = {
            "id": alert_id,
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "attack_type": prediction_result.get("Attack_Type", "BENIGN"),
            "confidence": float(prediction_result.get("Prediction_Confidence", 1.0)),
            "risk_score": float(prediction_result.get("Risk_Score", 0.0)),
            "risk_level": prediction_result.get("Risk_Level", "Low"),
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "protocol": protocol,
            "dst_port": int(dst_port),
            "prediction_time_ms": float(prediction_result.get("Prediction_Time_ms", 0.03)),
            "class_probabilities": json.dumps(prediction_result.get("Class_Probabilities", {}))
        }

        # Persist alert
        self._save_to_sqlite(alert_event)
        self._append_to_csv(alert_event)

        logger.info(
            "ALERT [%s]: %s | Risk: %s (%s/100) | %s -> %s:%d",
            alert_event["risk_level"], alert_event["attack_type"],
            alert_event["risk_level"], alert_event["risk_score"],
            src_ip, dst_ip, dst_port
        )

        return alert_event

    def save_alert(self, alert: Dict[str, Any]) -> None:
        """Public helper to save an alert dictionary directly into SQLite database."""
        if "class_probabilities" in alert and isinstance(alert["class_probabilities"], dict):
            alert["class_probabilities"] = json.dumps(alert["class_probabilities"])
        self._save_to_sqlite(alert)

    def _save_to_sqlite(self, alert: Dict[str, Any]) -> None:
        """Saves a single alert record into SQLite database."""
        try:
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO alerts VALUES (
                        :id, :timestamp, :attack_type, :confidence, :risk_score,
                        :risk_level, :src_ip, :dst_ip, :protocol, :dst_port,
                        :prediction_time_ms, :class_probabilities
                    )
                """, alert)
                conn.commit()
        except Exception as e:
            logger.error("Failed writing alert to SQLite: %s", e)

    def _append_to_csv(self, alert: Dict[str, Any]) -> None:
        """Appends alert record to live_alerts.csv."""
        try:
            df = pd.DataFrame([alert])
            header = not self.csv_path.exists()
            df.to_csv(self.csv_path, mode="a", index=False, header=header)
        except Exception as e:
            logger.error("Failed appending alert to CSV: %s", e)

    def query_alerts(
        self,
        protocol: Optional[str] = None,
        src_ip: Optional[str] = None,
        dst_ip: Optional[str] = None,
        risk_level: Optional[str] = None,
        attack_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Queries and filters stored alerts with multi-parameter criteria.
        """
        query = "SELECT * FROM alerts WHERE 1=1"
        params = []

        if protocol:
            query += " AND protocol = ?"
            params.append(protocol)
        if src_ip:
            query += " AND src_ip = ?"
            params.append(src_ip)
        if dst_ip:
            query += " AND dst_ip = ?"
            params.append(dst_ip)
        if risk_level:
            query += " AND risk_level = ?"
            params.append(risk_level)
        if attack_type:
            query += " AND attack_type = ?"
            params.append(attack_type)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        results = []
        try:
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                for r in rows:
                    results.append(dict(r))
        except Exception as e:
            logger.error("Query alerts SQLite error: %s", e)

        return results

    def generate_daily_report(self) -> Dict[str, Any]:
        """
        Generates a summary report of daily threat statistics.
        """
        today_prefix = datetime.now().strftime("%Y-%m-%d")
        query = "SELECT * FROM alerts WHERE timestamp LIKE ?"
        results = []
        try:
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, (f"{today_prefix}%",))
                results = [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            logger.error("Error fetching daily report data: %s", e)

        df = pd.DataFrame(results) if results else pd.DataFrame()
        if df.empty:
            return {
                "date": today_prefix,
                "total_alerts": 0,
                "attack_counts": {},
                "risk_counts": {}
            }

        return {
            "date": today_prefix,
            "total_alerts": len(df),
            "attack_counts": df["attack_type"].value_counts().to_dict(),
            "risk_counts": df["risk_level"].value_counts().to_dict(),
            "average_confidence": float(round(df["confidence"].mean(), 4)),
            "average_risk_score": float(round(df["risk_score"].mean(), 2))
        }
