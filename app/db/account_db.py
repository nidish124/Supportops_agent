"""
Tiny SQLLite-backed account DB helper. This is used to store the account information of the user.

Provides:
- Account creation -> AccountDB(path: str) : initialize DB file (use ":memory:" for tests)
- Account update -> upsert_account(account: dict)
- Account retrieval -> get_account(user_id: str) -> returns account dict or None

Schema (accounts):
- user_id TEXT PRIMARY KEY
- subscription TEXT
- last_payment_attempt TEXT (ISO timestamp or NULL)
- metadata TEXT (JSON string) optional
"""

import sqlite3
from typing import Dict, Optional
import json

class AccountDB:
    def __init__(self, path: str):
        self.path = path
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_tables()

    def _ensure_tables(self):
        cur = self._conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                user_id TEXT PRIMARY KEY,
                subscription TEXT,
                last_payment_attempt TEXT,
                metadata TEXT)

        """)
        self._conn.commit()

    def upsert_account(self, account: Dict[str, object]) -> None:
        """
        Upsert an account into the database.
        account: dict with keys user_id, subscription, last_payment_attempt, metadata
        """
        cur = self._conn.cursor()
        metadata = json.dumps(account.get("metadata") or {})
        cur.execute("""
            INSERT OR REPLACE INTO accounts (user_id, subscription, last_payment_attempt, metadata)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
              subscription=excluded.subscription,
              last_payment_attempt=excluded.last_payment_attempt,
              metadata=excluded.metadata
        """, (
            account['user_id'],
            account['subscription'],
            account['last_payment_attempt'],
            metadata,
        )) 
        self._conn.commit()

    def get_account(self, user_id: str) -> Optional[Dict[str, object]]:
        """
        Get an account from the database.
        user_id: str
        """
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM accounts WHERE user_id = ?", (user_id,))
        raw = cur.fetchone()
        if raw is None:
            return None
        return {
            "user_id": raw["user_id"],
            "subscription": raw["subscription"],
            "last_payment_attempt": raw["last_payment_attempt"],
            "metadata": json.loads(raw["metadata"])
        }

    def close(self):
        try:
            self._conn.close()
        except Exception as e:
            print(f"Error closing database: {e}")