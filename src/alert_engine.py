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

    def get_max_rowid(self) -> int:
        """Returns the current maximum rowid in alerts table."""
        try:
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COALESCE(MAX(rowid), 0) FROM alerts")
                row = cursor.fetchone()
                return int(row[0]) if row else 0
        except Exception as e:
            logger.error("get_max_rowid error: %s", e)
            return 0

    def get_alerts_after_rowid(self, last_rowid: int = 0, limit: int = 50) -> Tuple[List[Dict[str, Any]], int]:
        """Fetches stored alerts inserted after last_rowid, returning (alerts_list, max_new_rowid)."""
        query = "SELECT rowid, * FROM alerts WHERE rowid > ? ORDER BY rowid ASC LIMIT ?"
        results = []
        max_rowid = last_rowid
        try:
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, (last_rowid, limit))
                rows = cursor.fetchall()
                for r in rows:
                    r_dict = dict(r)
                    cur_rowid = r_dict.pop("rowid")
                    if cur_rowid > max_rowid:
                        max_rowid = cur_rowid
                    results.append(r_dict)
        except Exception as e:
            logger.error("get_alerts_after_rowid error: %s", e)

        return results, max_rowid

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

    def query_historical_threats_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        time_range: str = "all",
        attack_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        search: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Queries permanent historical threat alerts from alerts.db with pagination, search, and filtering.
        """
        import math
        where_clauses = ["1=1"]
        params = []

        if time_range == "24h":
            where_clauses.append("timestamp >= datetime('now', '-1 day')")
        elif time_range == "7d":
            where_clauses.append("timestamp >= datetime('now', '-7 days')")
        elif time_range == "30d":
            where_clauses.append("timestamp >= datetime('now', '-30 days')")
        elif start_date and end_date:
            where_clauses.append("timestamp BETWEEN ? AND ?")
            params.extend([start_date, end_date])

        if attack_type and attack_type != "All":
            where_clauses.append("attack_type = ?")
            params.append(attack_type)

        if risk_level and risk_level != "All":
            where_clauses.append("risk_level = ?")
            params.append(risk_level)

        if search:
            search_pattern = f"%{search}%"
            where_clauses.append("(id LIKE ? OR src_ip LIKE ? OR dst_ip LIKE ? OR attack_type LIKE ?)")
            params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

        where_sql = " AND ".join(where_clauses)
        count_sql = f"SELECT COUNT(*) FROM alerts WHERE {where_sql}"
        
        offset = (page - 1) * page_size
        data_sql = f"SELECT * FROM alerts WHERE {where_sql} ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        data_params = params + [page_size, offset]

        total = 0
        results = []
        try:
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(count_sql, params)
                c_row = cursor.fetchone()
                total = int(c_row[0]) if c_row else 0

                cursor.execute(data_sql, data_params)
                for r in cursor.fetchall():
                    results.append(dict(r))
        except Exception as e:
            logger.error("Error querying historical threats paginated: %s", e)

        total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "alerts": results
        }

    def export_alerts_csv_string(
        self,
        time_range: str = "all",
        attack_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        search: Optional[str] = None
    ) -> str:
        """Exports filtered alerts from alerts.db as CSV string."""
        res = self.query_historical_threats_paginated(
            page=1, page_size=100000, time_range=time_range,
            attack_type=attack_type, risk_level=risk_level, search=search
        )
        alerts = res.get("alerts", [])
        if not alerts:
            return "id,timestamp,attack_type,confidence,risk_score,risk_level,src_ip,dst_ip,protocol,dst_port,prediction_time_ms\n"
        df = pd.DataFrame(alerts)
        if "class_probabilities" in df.columns:
            df = df.drop(columns=["class_probabilities"])
        return df.to_csv(index=False)

    def export_alerts_json_string(
        self,
        time_range: str = "all",
        attack_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        search: Optional[str] = None
    ) -> str:
        """Exports filtered alerts from alerts.db as formatted JSON string."""
        res = self.query_historical_threats_paginated(
            page=1, page_size=100000, time_range=time_range,
            attack_type=attack_type, risk_level=risk_level, search=search
        )
        return json.dumps(res.get("alerts", []), indent=2)

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

    # ==========================================
    # HISTORICAL ANALYTICS METHODS (alerts.db)
    # ==========================================

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Queries permanent historical totals from alerts.db."""
        if not self.sqlite_path.exists():
            return {
                "total_flows_ever": 0,
                "total_attacks_ever": 0,
                "total_benign_ever": 0,
                "average_confidence_ever": 0.0,
                "average_latency_ever": 0.0,
                "last_prediction_time": None
            }

        try:
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN attack_type != 'BENIGN' THEN 1 ELSE 0 END) as attacks,
                        SUM(CASE WHEN attack_type = 'BENIGN' THEN 1 ELSE 0 END) as benigns,
                        COALESCE(AVG(confidence), 0.0) as avg_conf,
                        COALESCE(AVG(prediction_time_ms), 0.0) as avg_lat,
                        MAX(timestamp) as last_ts
                    FROM alerts
                """)
                row = cursor.fetchone()
                if row:
                    return {
                        "total_flows_ever": int(row["total"] or 0),
                        "total_attacks_ever": int(row["attacks"] or 0),
                        "total_benign_ever": int(row["benigns"] or 0),
                        "average_confidence_ever": float(round(row["avg_conf"] or 0.0, 4)),
                        "average_latency_ever": float(round(row["avg_lat"] or 0.0, 3)),
                        "last_prediction_time": str(row["last_ts"]) if row["last_ts"] else None
                    }
        except Exception as e:
            logger.error("Error in get_analytics_summary: %s", e)

        return {
            "total_flows_ever": 0,
            "total_attacks_ever": 0,
            "total_benign_ever": 0,
            "average_confidence_ever": 0.0,
            "average_latency_ever": 0.0,
            "last_prediction_time": None
        }

    def get_analytics_trends(self, time_range: str = "all") -> List[Dict[str, Any]]:
        """Returns time series trend points from alerts.db grouped by hour/date."""
        if not self.sqlite_path.exists():
            return []

        # Determine datetime filter & grouping
        group_fmt = "%Y-%m-%d %H:00" if time_range == "24h" else "%Y-%m-%d"
        time_filter = ""
        params = []

        if time_range == "24h":
            time_filter = "WHERE timestamp >= datetime('now', '-1 day')"
        elif time_range == "7d":
            time_filter = "WHERE timestamp >= datetime('now', '-7 days')"
        elif time_range == "30d":
            time_filter = "WHERE timestamp >= datetime('now', '-30 days')"

        query = f"""
            SELECT
                strftime('{group_fmt}', timestamp) as time_label,
                COUNT(*) as total,
                SUM(CASE WHEN attack_type = 'BENIGN' THEN 1 ELSE 0 END) as benign,
                SUM(CASE WHEN attack_type != 'BENIGN' THEN 1 ELSE 0 END) as attacks
            FROM alerts
            {time_filter}
            GROUP BY time_label
            ORDER BY time_label ASC
            LIMIT 100
        """

        trends = []
        try:
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                for r in cursor.fetchall():
                    trends.append({
                        "time": str(r["time_label"] or "Unknown"),
                        "total": int(r["total"] or 0),
                        "benign": int(r["benign"] or 0),
                        "attacks": int(r["attacks"] or 0)
                    })
        except Exception as e:
            logger.error("Error in get_analytics_trends: %s", e)

        return trends

    def get_analytics_top_attacks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns top attack categories and counts from alerts.db."""
        if not self.sqlite_path.exists():
            return []

        query = """
            SELECT
                attack_type,
                COUNT(*) as count,
                AVG(confidence) as avg_confidence,
                AVG(risk_score) as avg_risk_score
            FROM alerts
            GROUP BY attack_type
            ORDER BY count DESC
            LIMIT ?
        """

        results = []
        try:
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, (limit,))
                for r in cursor.fetchall():
                    results.append({
                        "attack_type": str(r["attack_type"]),
                        "count": int(r["count"] or 0),
                        "average_confidence": float(round(r["avg_confidence"] or 0.0, 4)),
                        "average_risk_score": float(round(r["avg_risk_score"] or 0.0, 2))
                    })
        except Exception as e:
            logger.error("Error in get_analytics_top_attacks: %s", e)

        return results

    def get_analytics_severity(self) -> Dict[str, int]:
        """Returns severity breakdown counts from alerts.db."""
        if not self.sqlite_path.exists():
            return {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}

        query = """
            SELECT
                SUM(CASE WHEN risk_level = 'Critical' THEN 1 ELSE 0 END) as criticals,
                SUM(CASE WHEN risk_level = 'High' THEN 1 ELSE 0 END) as highs,
                SUM(CASE WHEN risk_level = 'Medium' THEN 1 ELSE 0 END) as mediums,
                SUM(CASE WHEN risk_level = 'Low' THEN 1 ELSE 0 END) as lows
            FROM alerts
        """

        try:
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query)
                row = cursor.fetchone()
                if row:
                    return {
                        "Critical": int(row["criticals"] or 0),
                        "High": int(row["highs"] or 0),
                        "Medium": int(row["mediums"] or 0),
                        "Low": int(row["lows"] or 0)
                    }
        except Exception as e:
            logger.error("Error in get_analytics_severity: %s", e)

        return {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}

