"""
Audit Logger module for NIDS.
Records security audit events across SQLite, CSV, and JSON formats with filtering & report capabilities.
"""
import json
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from src.utils.utils import ensure_directory, get_absolute_path

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Records, persists, and queries platform security audit events.
    """

    def __init__(self, db_dir: Union[str, Path] = "predictions"):
        self.db_dir = ensure_directory(db_dir)
        self.sqlite_path = self.db_dir / "audit_logs.db"
        self.csv_path = self.db_dir / "audit_logs.csv"
        self.json_path = self.db_dir / "audit_logs.json"

        self._init_db()

    def _init_db(self) -> None:
        """Initializes SQLite audit log database schema."""
        try:
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT,
                        event_type TEXT,
                        username TEXT,
                        ip_address TEXT,
                        action TEXT,
                        status TEXT,
                        details TEXT
                    )
                """)
                conn.commit()
            logger.info("Initialized Audit Logger SQLite database at %s", self.sqlite_path)
        except Exception as e:
            logger.error("Failed initializing Audit Logger SQLite DB: %s", e)

    def log_event(
        self,
        event_type: str,
        username: str = "system",
        ip_address: str = "127.0.0.1",
        action: str = "execute",
        status: str = "success",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Logs a security audit event.

        Args:
            event_type: Category (e.g., 'LOGIN', 'LOGOUT', 'PREDICTION', 'PLAYBOOK', 'FIREWALL', 'SIEM_EXPORT', 'USER_MGMT')
            username: User triggering the event.
            ip_address: Client IP address.
            action: Action verb.
            status: Outcome ('success', 'failure', 'denied').
            details: Extra metadata.
        """
        now = datetime.now()
        event_id = f"AUD-{now.strftime('%Y%m%d%H%M%S')}-{int(time.time() * 1000) % 1000}"

        record = {
            "id": event_id,
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": event_type,
            "username": username,
            "ip_address": ip_address,
            "action": action,
            "status": status,
            "details": json.dumps(details or {})
        }

        self._save_to_sqlite(record)
        self._append_to_csv(record)

        logger.info("AUDIT LOG [%s]: %s by %s (%s) - %s",
                    event_type, action, username, ip_address, status)

        return record

    def _save_to_sqlite(self, record: Dict[str, Any]) -> None:
        """Saves audit record into SQLite database."""
        try:
            with sqlite3.connect(str(self.sqlite_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_logs VALUES (
                        :id, :timestamp, :event_type, :username, :ip_address,
                        :action, :status, :details
                    )
                """, record)
                conn.commit()
        except Exception as e:
            logger.error("Failed saving audit record to SQLite: %s", e)

    def _append_to_csv(self, record: Dict[str, Any]) -> None:
        """Appends audit record to CSV file."""
        try:
            df = pd.DataFrame([record])
            header = not self.csv_path.exists()
            df.to_csv(self.csv_path, mode="a", index=False, header=header)
        except Exception as e:
            logger.error("Failed appending audit record to CSV: %s", e)

    def query_audit_logs(
        self,
        event_type: Optional[str] = None,
        username: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Queries and filters stored security audit logs.
        """
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if username:
            query += " AND username = ?"
            params.append(username)
        if status:
            query += " AND status = ?"
            params.append(status)

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
            logger.error("Error querying audit logs: %s", e)

        return results
