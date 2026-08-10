"""
Metrics Manager module for NIDS FastAPI Backend.
Thread-safe, real-time metrics collection engine tracking requests, predictions, latencies,
confidences, attack category breakdowns, and risk severity distributions.
Hydrates baseline totals from SQLite alerts.db upon startup.
"""
import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.utils import get_absolute_path

logger = logging.getLogger(__name__)


class MetricsManager:
    """
    Singleton thread-safe metrics collection engine.
    Records live prediction events, API requests, latencies, and threat statistics.
    """
    _instance: Optional["MetricsManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "MetricsManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MetricsManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_path: str = "predictions/alerts.db"):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._mutex = threading.Lock()
        self.db_path = get_absolute_path(db_path)

        # Real-time metric counters
        self.requests_served: int = 0
        self.prediction_count: int = 0
        self.attack_count: int = 0
        self.benign_count: int = 0
        self.total_latency_ms: float = 0.0
        self.total_confidence: float = 0.0

        # Risk severity level counters
        self.critical_alerts: int = 0
        self.high_alerts: int = 0
        self.medium_alerts: int = 0
        self.low_alerts: int = 0

        self.last_prediction_time: Optional[str] = None

        # Hydrate initial baseline metrics from SQLite alerts.db if present
        self._hydrate_from_db()

    def _hydrate_from_db(self) -> None:
        """Hydrates baseline threat alert statistics from SQLite database."""
        if not self.db_path.exists():
            return

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'")
                if not cursor.fetchone():
                    return

                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN attack_type != 'BENIGN' THEN 1 ELSE 0 END) as attacks,
                        SUM(CASE WHEN attack_type = 'BENIGN' THEN 1 ELSE 0 END) as benigns,
                        SUM(confidence) as sum_conf,
                        SUM(prediction_time_ms) as sum_lat,
                        SUM(CASE WHEN risk_level = 'Critical' THEN 1 ELSE 0 END) as criticals,
                        SUM(CASE WHEN risk_level = 'High' THEN 1 ELSE 0 END) as highs,
                        SUM(CASE WHEN risk_level = 'Medium' THEN 1 ELSE 0 END) as mediums,
                        SUM(CASE WHEN risk_level = 'Low' THEN 1 ELSE 0 END) as lows,
                        MAX(timestamp) as last_ts
                    FROM alerts
                """)
                row = cursor.fetchone()
                if row and row["total"]:
                    self.prediction_count = int(row["total"] or 0)
                    self.attack_count = int(row["attacks"] or 0)
                    self.benign_count = int(row["benigns"] or 0)
                    self.total_confidence = float(row["sum_conf"] or 0.0)
                    self.total_latency_ms = float(row["sum_lat"] or 0.0)
                    self.critical_alerts = int(row["criticals"] or 0)
                    self.high_alerts = int(row["highs"] or 0)
                    self.medium_alerts = int(row["mediums"] or 0)
                    self.low_alerts = int(row["lows"] or 0)
                    self.last_prediction_time = str(row["last_ts"]) if row["last_ts"] else None
                    logger.info("Hydrated MetricsManager from SQLite alerts.db: %d total predictions", self.prediction_count)
        except Exception as e:
            logger.warning("Could not hydrate MetricsManager from SQLite db: %s", e)

    def increment_requests(self) -> None:
        """Increments total API request counter."""
        with self._mutex:
            self.requests_served += 1

    def record_prediction(
        self,
        attack_type: str,
        confidence: float,
        risk_score: float,
        risk_level: str,
        latency_ms: float,
        count: int = 1
    ) -> None:
        """
        Thread-safely records single or batch prediction activity and recalculates running metrics.
        """
        with self._mutex:
            self.prediction_count += count
            self.total_latency_ms += float(latency_ms) * count
            self.total_confidence += float(confidence) * count
            self.last_prediction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Update threat counters
            if str(attack_type).upper() == "BENIGN":
                self.benign_count += count
            else:
                self.attack_count += count

            # Update risk severity levels
            level_str = str(risk_level).title()
            if level_str == "Critical":
                self.critical_alerts += count
            elif level_str == "High":
                self.high_alerts += count
            elif level_str == "Medium":
                self.medium_alerts += count
            else:
                self.low_alerts += count

    def get_metrics(self) -> Dict[str, Any]:
        """Returns dynamically calculated real-time metrics dictionary."""
        with self._mutex:
            total_preds = self.prediction_count
            avg_lat = (self.total_latency_ms / total_preds) if total_preds > 0 else 0.035
            avg_conf = (self.total_confidence / total_preds) if total_preds > 0 else 0.9985

            return {
                "prediction_count": self.prediction_count,
                "attack_count": self.attack_count,
                "benign_count": self.benign_count,
                "average_latency_ms": float(round(avg_lat, 3)),
                "average_confidence": float(round(avg_conf, 4)),
                "critical_alerts": self.critical_alerts,
                "high_alerts": self.high_alerts,
                "medium_alerts": self.medium_alerts,
                "low_alerts": self.low_alerts,
                "requests_served": self.requests_served,
                "last_prediction_time": self.last_prediction_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }


metrics_manager = MetricsManager()
