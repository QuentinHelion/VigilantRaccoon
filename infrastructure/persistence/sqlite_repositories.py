from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from domain.entities import Alert, Server
from domain.repositories import AlertRepository, StateRepository, ServerRepository


def _ensure_db(path: str) -> None:
    db_path = Path(path)
    if not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_name TEXT NOT NULL,
                source_log TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                ip_address TEXT,
                rule TEXT,
                created_at TEXT NOT NULL,
                acknowledged BOOLEAN DEFAULT FALSE,
                acknowledged_at TEXT,
                acknowledged_by TEXT
            );
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged);
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS state (
                server_name TEXT NOT NULL,
                log_path TEXT NOT NULL,
                last_seen_ts TEXT NOT NULL,
                PRIMARY KEY (server_name, log_path)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS servers (
                name TEXT PRIMARY KEY,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                username TEXT NOT NULL,
                password TEXT,
                private_key_path TEXT,
                logs TEXT NOT NULL
            );
            """
        )
        conn.commit()


class SQLiteAlertRepository(AlertRepository):
    def __init__(self, db_path: str) -> None:
        _ensure_db(db_path)
        self._db_path = db_path

    def save_alerts(self, alerts: Iterable[Alert]) -> int:
        alerts_list = list(alerts)
        if not alerts_list:
            return 0
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self._db_path, check_same_thread=False) as conn:
            conn.executemany(
                """
                INSERT INTO alerts (server_name, source_log, timestamp, level, message, ip_address, rule, created_at, acknowledged, acknowledged_at, acknowledged_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        a.server_name,
                        a.source_log,
                        a.timestamp.isoformat(),
                        a.level,
                        a.message,
                        a.ip_address,
                        a.rule,
                        now,
                        a.acknowledged,
                        a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                        a.acknowledged_by,
                    )
                    for a in alerts_list
                ],
            )
            conn.commit()
        return len(alerts_list)

    def list_alerts(self, limit: int = 200, since: Optional[datetime] = None, acknowledged: Optional[bool] = None) -> List[Alert]:
        query = "SELECT id, server_name, source_log, timestamp, level, message, ip_address, rule, acknowledged, acknowledged_at, acknowledged_by FROM alerts"
        params: list = []
        where_clauses = []
        
        if since is not None:
            where_clauses.append("timestamp >= ?")
            params.append(since.isoformat())
        
        if acknowledged is not None:
            where_clauses.append("acknowledged = ?")
            params.append(acknowledged)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(int(limit))

        with sqlite3.connect(self._db_path, check_same_thread=False) as conn:
            rows = conn.execute(query, params).fetchall()

        alerts: List[Alert] = []
        for r in rows:
            alerts.append(
                Alert(
                    id=r[0],
                    server_name=r[1],
                    source_log=r[2],
                    timestamp=datetime.fromisoformat(r[3]),
                    level=r[4],
                    message=r[5],
                    ip_address=r[6],
                    rule=r[7],
                    acknowledged=bool(r[8]),
                    acknowledged_at=datetime.fromisoformat(r[9]) if r[9] else None,
                    acknowledged_by=r[10],
                )
            )
        return alerts

    def acknowledge_alert(self, alert_id: int, acknowledged_by: str) -> bool:
        """Mark an alert as acknowledged."""
        now = datetime.utcnow()
        with sqlite3.connect(self._db_path, check_same_thread=False) as conn:
            cursor = conn.execute(
                """
                UPDATE alerts 
                SET acknowledged = TRUE, acknowledged_at = ?, acknowledged_by = ?
                WHERE id = ?
                """,
                (now.isoformat(), acknowledged_by, alert_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def acknowledge_alerts_by_rule(self, rule: str, acknowledged_by: str) -> int:
        """Acknowledge all alerts with a specific rule."""
        now = datetime.utcnow()
        with sqlite3.connect(self._db_path, check_same_thread=False) as conn:
            cursor = conn.execute(
                """
                UPDATE alerts 
                SET acknowledged = TRUE, acknowledged_at = ?, acknowledged_by = ?
                WHERE rule = ? AND acknowledged = FALSE
                """,
                (now.isoformat(), acknowledged_by, rule),
            )
            conn.commit()
            return cursor.rowcount


class SQLiteStateRepository(StateRepository):
    def __init__(self, db_path: str) -> None:
        _ensure_db(db_path)
        self._db_path = db_path

    def get_last_seen_timestamp(self, server_name: str, log_path: str) -> Optional[datetime]:
        with sqlite3.connect(self._db_path, check_same_thread=False) as conn:
            row = conn.execute(
                "SELECT last_seen_ts FROM state WHERE server_name = ? AND log_path = ?",
                (server_name, log_path),
            ).fetchone()
        if row and row[0]:
            try:
                return datetime.fromisoformat(row[0])
            except Exception:
                return None
        return None

    def set_last_seen_timestamp(self, server_name: str, log_path: str, ts: datetime) -> None:
        with sqlite3.connect(self._db_path, check_same_thread=False) as conn:
            conn.execute(
                """
                INSERT INTO state (server_name, log_path, last_seen_ts)
                VALUES (?, ?, ?)
                ON CONFLICT(server_name, log_path) DO UPDATE SET last_seen_ts=excluded.last_seen_ts
                """,
                (server_name, log_path, ts.isoformat()),
            )
            conn.commit()


class SQLiteServerRepository(ServerRepository):
    def __init__(self, db_path: str) -> None:
        _ensure_db(db_path)
        self._db_path = db_path

    def list_servers(self) -> List[Server]:
        with sqlite3.connect(self._db_path, check_same_thread=False) as conn:
            rows = conn.execute(
                "SELECT name, host, port, username, password, private_key_path, logs FROM servers ORDER BY name"
            ).fetchall()
        servers: List[Server] = []
        for r in rows:
            servers.append(
                Server(
                    name=r[0], host=r[1], port=int(r[2]), username=r[3], password=r[4], private_key_path=r[5], logs=json.loads(r[6])
                )
            )
        return servers

    def upsert_server(self, server: Server) -> None:
        logs_json = json.dumps(server.logs or [])
        with sqlite3.connect(self._db_path, check_same_thread=False) as conn:
            conn.execute(
                """
                INSERT INTO servers (name, host, port, username, password, private_key_path, logs)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET host=excluded.host, port=excluded.port, username=excluded.username,
                    password=excluded.password, private_key_path=excluded.private_key_path, logs=excluded.logs
                """,
                (server.name, server.host, int(server.port), server.username, server.password, server.private_key_path, logs_json),
            )
            conn.commit()

    def delete_server(self, name: str) -> None:
        with sqlite3.connect(self._db_path, check_same_thread=False) as conn:
            conn.execute("DELETE FROM servers WHERE name = ?", (name,))
            conn.commit()

    def get_server(self, name: str) -> Optional[Server]:
        with sqlite3.connect(self._db_path, check_same_thread=False) as conn:
            row = conn.execute(
                "SELECT name, host, port, username, password, private_key_path, logs FROM servers WHERE name = ?",
                (name,),
            ).fetchone()
        if not row:
            return None
        return Server(
            name=row[0], host=row[1], port=int(row[2]), username=row[3], password=row[4], private_key_path=row[5], logs=json.loads(row[6])
        )
