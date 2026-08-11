"""
Session Metrics Module for NIDS FastAPI Backend.
Thread-safe, in-memory metrics engine tracking only CURRENT SESSION metrics.
Resets to ZERO every time FastAPI backend process starts or restarts.
No SQLite dependency.
"""
import logging
import threading
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SessionMetricsManager:
    """
    Singleton thread-safe session metrics engine.
    Stores and calculates metrics exclusively for the active backend process session.
    """
    _instance: Optional["SessionMetricsManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "SessionMetricsManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SessionMetricsManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._mutex = threading.Lock()
        self.reset()

    def reset(self) -> None:
        """Resets all session metric counters to zero."""
        with self._mutex if hasattr(self, "_mutex") else threading.Lock():
            self.requests_served: int = 0
            self.prediction_count: int = 0
            self.attack_count: int = 0
            self.benign_count: int = 0
            self.total_latency_ms: float = 0.0
            self.total_confidence: float = 0.0

            # Severity counters
            self.critical_alerts: int = 0
            self.high_alerts: int = 0
            self.medium_alerts: int = 0
            self.low_alerts: int = 0

            self.last_prediction_time: Optional[str] = None
            logger.info("Initialized fresh SessionMetricsManager (Counters reset to ZERO).")

    def increment_requests(self) -> None:
        """Increments session API request counter."""
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
        Thread-safely records single or batch session prediction activity.
        """
        with self._mutex:
            self.prediction_count += count
            self.total_latency_ms += float(latency_ms) * count
            self.total_confidence += float(confidence) * count
            self.last_prediction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Update threat category counters
            if str(attack_type).upper() == "BENIGN":
                self.benign_count += count
            else:
                self.attack_count += count

            # Update risk severity counters
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
        """Returns in-memory active session metrics dictionary."""
        with self._mutex:
            total_preds = self.prediction_count
            avg_lat = (self.total_latency_ms / total_preds) if total_preds > 0 else 0.0
            avg_conf = (self.total_confidence / total_preds) if total_preds > 0 else 0.0

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


session_metrics_manager = SessionMetricsManager()
