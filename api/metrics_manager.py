"""
Metrics Manager module for NIDS FastAPI Backend.
Thread-safe, real-time metrics collection engine that combines:
  1. SQLite alerts.db (source of truth for all persisted predictions - live monitor + API)
  2. In-memory API-session counters (for /predict and /batch_predict calls not yet in DB)

The get_metrics() method always re-reads from SQLite (with a short cache) to pick up
alerts written by external processes (e.g., run_live_monitor.py running in a separate process).
"""
import logging
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.utils import get_absolute_path

logger = logging.getLogger(__name__)

# SQL query to aggregate all prediction metrics from the alerts table
_METRICS_SQL = """
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN attack_type != 'BENIGN' THEN 1 ELSE 0 END) as attacks,
        SUM(CASE WHEN attack_type = 'BENIGN' THEN 1 ELSE 0 END) as benigns,
        COALESCE(AVG(confidence), 0) as avg_conf,
        COALESCE(AVG(prediction_time_ms), 0) as avg_lat,
        SUM(CASE WHEN risk_level = 'Critical' THEN 1 ELSE 0 END) as criticals,
        SUM(CASE WHEN risk_level = 'High' THEN 1 ELSE 0 END) as highs,
        SUM(CASE WHEN risk_level = 'Medium' THEN 1 ELSE 0 END) as mediums,
        SUM(CASE WHEN risk_level = 'Low' THEN 1 ELSE 0 END) as lows,
        MAX(timestamp) as last_ts
    FROM alerts
"""


class MetricsManager:
    """
    Singleton thread-safe metrics engine.

    Architecture:
    - SQLite alerts.db is the single source of truth for prediction metrics.
    - get_metrics() re-queries the DB every call (cached for 2 seconds).
    - API-session predictions that haven't been persisted to DB yet are tracked
      via in-memory delta counters and merged into the response.
    - requests_served is API-server-only (in-memory, not in DB).
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

        # In-memory API request counter (not stored in DB)
        self.requests_served: int = 0

        # In-memory delta counters for API predictions NOT yet persisted to alerts.db.
        # These track predictions made via /predict and /batch_predict endpoints.
        self._api_prediction_count: int = 0
        self._api_attack_count: int = 0
        self._api_benign_count: int = 0
        self._api_total_latency_ms: float = 0.0
        self._api_total_confidence: float = 0.0
        self._api_critical: int = 0
        self._api_high: int = 0
        self._api_medium: int = 0
        self._api_low: int = 0
        self._api_last_prediction_time: Optional[str] = None

        # DB query cache (avoids hitting SQLite on every dashboard poll)
        self._cache_ttl_sec: float = 2.0
        self._cached_db_metrics: Optional[Dict[str, Any]] = None
        self._cache_timestamp: float = 0.0

        logger.info("MetricsManager initialized. DB path: %s", self.db_path)

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
        Records API-session prediction activity into in-memory delta counters.
        These are merged with DB totals in get_metrics().
        """
        with self._mutex:
            self._api_prediction_count += count
            self._api_total_latency_ms += float(latency_ms) * count
            self._api_total_confidence += float(confidence) * count
            self._api_last_prediction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if str(attack_type).upper() == "BENIGN":
                self._api_benign_count += count
            else:
                self._api_attack_count += count

            level_str = str(risk_level).title()
            if level_str == "Critical":
                self._api_critical += count
            elif level_str == "High":
                self._api_high += count
            elif level_str == "Medium":
                self._api_medium += count
            else:
                self._api_low += count

    def _query_db_metrics(self) -> Dict[str, Any]:
        """
        Queries SQLite alerts.db for aggregated prediction metrics.
        Returns zero-initialized dict if DB is unavailable.
        """
        empty = {
            "total": 0, "attacks": 0, "benigns": 0,
            "avg_conf": 0.0, "avg_lat": 0.0,
            "criticals": 0, "highs": 0, "mediums": 0, "lows": 0,
            "last_ts": None
        }

        if not self.db_path.exists():
            return empty

        try:
            with sqlite3.connect(str(self.db_path), timeout=3) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Check table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'")
                if not cursor.fetchone():
                    return empty

                cursor.execute(_METRICS_SQL)
                row = cursor.fetchone()
                if row and row["total"]:
                    return {
                        "total": int(row["total"] or 0),
                        "attacks": int(row["attacks"] or 0),
                        "benigns": int(row["benigns"] or 0),
                        "avg_conf": float(row["avg_conf"] or 0.0),
                        "avg_lat": float(row["avg_lat"] or 0.0),
                        "criticals": int(row["criticals"] or 0),
                        "highs": int(row["highs"] or 0),
                        "mediums": int(row["mediums"] or 0),
                        "lows": int(row["lows"] or 0),
                        "last_ts": str(row["last_ts"]) if row["last_ts"] else None
                    }
                return empty
        except Exception as e:
            logger.warning("Could not query MetricsManager DB: %s", e)
            return empty

    def _get_cached_db_metrics(self) -> Dict[str, Any]:
        """Returns DB metrics with a short TTL cache to avoid excessive queries."""
        now = time.monotonic()
        if self._cached_db_metrics is None or (now - self._cache_timestamp) > self._cache_ttl_sec:
            self._cached_db_metrics = self._query_db_metrics()
            self._cache_timestamp = now
        return self._cached_db_metrics

    def get_metrics(self) -> Dict[str, Any]:
        """
        Returns real-time metrics by merging:
        1. Fresh SQLite DB totals (captures live monitor + any persisted predictions)
        2. In-memory API-session deltas (for /predict, /batch_predict not yet in DB)
        """
        with self._mutex:
            db = self._get_cached_db_metrics()

            # Merge DB totals + API-session deltas
            total_preds = db["total"] + self._api_prediction_count
            total_attacks = db["attacks"] + self._api_attack_count
            total_benigns = db["benigns"] + self._api_benign_count
            total_criticals = db["criticals"] + self._api_critical
            total_highs = db["highs"] + self._api_high
            total_mediums = db["mediums"] + self._api_medium
            total_lows = db["lows"] + self._api_low

            # Weighted average for latency and confidence
            if total_preds > 0:
                if db["total"] > 0 and self._api_prediction_count > 0:
                    # Merge DB averages with API running totals
                    db_total_lat = db["avg_lat"] * db["total"]
                    db_total_conf = db["avg_conf"] * db["total"]
                    avg_lat = (db_total_lat + self._api_total_latency_ms) / total_preds
                    avg_conf = (db_total_conf + self._api_total_confidence) / total_preds
                elif db["total"] > 0:
                    avg_lat = db["avg_lat"]
                    avg_conf = db["avg_conf"]
                else:
                    avg_lat = self._api_total_latency_ms / self._api_prediction_count
                    avg_conf = self._api_total_confidence / self._api_prediction_count
            else:
                avg_lat = 0.0
                avg_conf = 0.0

            # Pick the most recent timestamp
            last_ts = self._api_last_prediction_time or db["last_ts"]
            if self._api_last_prediction_time and db["last_ts"]:
                last_ts = max(self._api_last_prediction_time, db["last_ts"])

            return {
                "prediction_count": total_preds,
                "attack_count": total_attacks,
                "benign_count": total_benigns,
                "average_latency_ms": float(round(avg_lat, 3)),
                "average_confidence": float(round(avg_conf, 4)),
                "critical_alerts": total_criticals,
                "high_alerts": total_highs,
                "medium_alerts": total_mediums,
                "low_alerts": total_lows,
                "requests_served": self.requests_served,
                "last_prediction_time": last_ts or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }


metrics_manager = MetricsManager()
