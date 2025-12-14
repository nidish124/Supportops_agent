"""
AuditDB - minimal sqllite-backed audit table for actions.

Schema (audits):
 - ID INTEGER PRIMARY KEY AUTOINCREMENT
 - request_id TEXT
 - user_id TEXT
 - action_type TEXT
 - action_payload TEXT (JSON string)
 - executor_id TEXT
 - status TEXT ('allowed'|'requires_approval'|'executed'|'rejected')
 - audit_token TEXT (nullable)
 - created_at TEXT (ISO timestamp)
"""

from setuptools.errors import ExecError
import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any
from datetime import datetime, UTC
import os

db_path = os.getenv("DB_PATH", "/tmp/supportops_audit.db")

class AuditDB:
    def __init__(self, path: str = None):
        self.path = path or db_path
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_table()

    def _ensure_table(self):
        cur = self._conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            user_id TEXT,
            action_type TEXT,
            action_payload TEXT,
            executor_id TEXT,
            status TEXT,
            audit_token TEXT,
            created_at TEXT
            )
        """) 
        self._conn.commit()

    def insert_audit(self, request_id: str, user_id: str, action_type: str, action_payload: Dict[str, Any], executor_id: Optional[str], status: str, audit_token: Optional[str]) -> int:
        cur = self._conn.cursor()
        payload_json = json.dumps(action_payload or {})
        now = datetime.now(UTC).isoformat()
        cur.execute(
            """INSERT INTO audits (request_id, user_id, action_type, action_payload, executor_id, status, audit_token, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (request_id, user_id, action_type, payload_json, executor_id, status, audit_token, now),
        )
        self._conn.commit()
        return cur.lastrowid

    def update_status(self, audit_id: int, status: str, audit_token: Optional[str]= None):
        cur = self._conn.cursor()
        if audit_token is not None:
            cur.execute("UPDATE audits SET status = ?, audit_token = ? WHERE id = ?", (status, audit_token, audit_id))
        else:
            cur.execute("UPDATE audits SET status = ? WHERE id = ?", (status, audit_id))
        self._conn.commit()

    def get_audit(self, audit_id: int) -> Optional[Dict[str, Any]]:
        """
        Get an audit details from the database.
        audit_id: str
        """
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM audits WHERE id = ?", (audit_id,))
        row = cur.fetchone()

        if not row:
            return None

        try:
            payload = json.loads(row["action_payload"]) if row["action_payload"] else {}
        except Exception:
            payload = {}

        return {
            "id": row["id"],
            "request_id": row["request_id"],
            "user_id": row["user_id"],
            "action_type": row["action_type"],
            "action_payload": payload,
            "executor_id": row["executor_id"],
            "status": row["status"],
            "audit_token": row["audit_token"],
            "created_at": row["created_at"],
        }
    
    def close(self):
        try:
            self._conn.close()
        except Exception as e:
            print(f"Error closing database: {e}")