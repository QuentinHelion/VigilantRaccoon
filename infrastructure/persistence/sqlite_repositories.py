from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional, Iterable

from domain.entities import Alert, Server, AlertException
from domain.repositories import AlertRepository, ServerRepository, StateRepository, AlertExceptionRepository


class SQLiteAlertRepository(AlertRepository):
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._init_db()

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_name TEXT NOT NULL,
                    log_source TEXT NOT NULL,
                    rule TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    ip_address TEXT,
                    username TEXT,
                    timestamp DATETIME NOT NULL,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_at DATETIME,
                    acknowledged_by TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def save_alerts(self, alerts: Iterable[Alert]) -> int:
        """Save multiple alerts and return count of saved alerts."""
        saved_count = 0
        with self._get_connection() as conn:
            for alert in alerts:
                cursor = conn.execute("""
                    INSERT INTO alerts (server_name, log_source, rule, level, message, ip_address, username, timestamp, acknowledged, acknowledged_at, acknowledged_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.server_name, alert.log_source, alert.rule, alert.level, alert.message,
                    alert.ip_address, alert.username, alert.timestamp.isoformat(),
                    alert.acknowledged, alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                    alert.acknowledged_by
                ))
                alert.id = cursor.lastrowid
                saved_count += 1
            conn.commit()
        return saved_count

    def list_alerts(self, server_name: Optional[str] = None, acknowledged: Optional[bool] = None, limit: Optional[int] = None) -> List[Alert]:
        with self._get_connection() as conn:
            query = "SELECT * FROM alerts WHERE 1=1"
            params = []
            
            if server_name:
                query += " AND server_name = ?"
                params.append(server_name)
            
            if acknowledged is not None:
                query += " AND acknowledged = ?"
                params.append(acknowledged)
            
            query += " ORDER BY timestamp DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor = conn.execute(query, params)
            alerts = []
            for row in cursor.fetchall():
                alert = Alert(
                    id=row['id'],
                    server_name=row['server_name'],
                    log_source=row['log_source'],
                    rule=row['rule'],
                    level=row['level'],
                    message=row['message'],
                    ip_address=row['ip_address'],
                    username=row['username'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    acknowledged=bool(row['acknowledged']),
                    acknowledged_at=datetime.fromisoformat(row['acknowledged_at']) if row['acknowledged_at'] else None,
                    acknowledged_by=row['acknowledged_by']
                )
                alerts.append(alert)
            return alerts

    def acknowledge_alert(self, alert_id: int, acknowledged_by: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                UPDATE alerts 
                SET acknowledged = TRUE, acknowledged_at = ?, acknowledged_by = ?
                WHERE id = ?
            """, (datetime.utcnow().isoformat(), acknowledged_by, alert_id))
            conn.commit()
            return cursor.rowcount > 0

    def acknowledge_alerts_by_rule(self, rule: str, acknowledged_by: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                UPDATE alerts 
                SET acknowledged = TRUE, acknowledged_at = ?, acknowledged_by = ?
                WHERE rule = ? AND acknowledged = FALSE
            """, (datetime.utcnow().isoformat(), acknowledged_by, rule))
            conn.commit()
            return cursor.rowcount


class SQLiteStateRepository(StateRepository):
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._init_db()

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS collection_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_name TEXT NOT NULL,
                    log_source TEXT NOT NULL,
                    last_position TEXT NOT NULL,
                    last_seen_timestamp TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(server_name, log_source)
                )
            """)
            conn.commit()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def get_last_seen_timestamp(self, server_name: str, log_source: str) -> Optional[str]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT last_seen_timestamp FROM collection_state 
                WHERE server_name = ? AND log_source = ?
            """, (server_name, log_source))
            row = cursor.fetchone()
            if row and row['last_seen_timestamp']:
                try:
                    # Try to parse the timestamp and return it as ISO string
                    ts = datetime.fromisoformat(row['last_seen_timestamp'])
                    return ts.isoformat()
                except (ValueError, TypeError):
                    # If parsing fails, return the raw string
                    return row['last_seen_timestamp']
            return None

    def set_last_seen_timestamp(self, server_name: str, log_source: str, timestamp: str) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO collection_state (server_name, log_source, last_position, last_seen_timestamp, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (server_name, log_source, "", timestamp, datetime.utcnow().isoformat()))
            conn.commit()


class SQLiteServerRepository(ServerRepository):
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._init_db()

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT,
                    private_key_path TEXT,
                    logs TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def save_server(self, server: Server) -> bool:
        with self._get_connection() as conn:
            # Convert logs list to comma-separated string
            logs_str = ','.join(server.logs) if server.logs else ''
            
            if server.id:
                # Update existing server
                conn.execute("""
                    UPDATE servers 
                    SET name = ?, host = ?, port = ?, username = ?, password = ?, 
                        private_key_path = ?, logs = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    server.name, server.host, server.port, server.username,
                    server.password, server.private_key_path, logs_str,
                    datetime.utcnow().isoformat(), server.id
                ))
            else:
                # Insert new server
                conn.execute("""
                    INSERT INTO servers (name, host, port, username, password, private_key_path, logs)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    server.name, server.host, server.port, server.username,
                    server.password, server.private_key_path, logs_str
                ))
            
            conn.commit()
            return True

    def get_server(self, name: str) -> Optional[Server]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM servers WHERE name = ?
            """, (name,))
            row = cursor.fetchone()
            if row:
                # Parse logs back to list
                logs = row['logs'].split(',') if row['logs'] else []
                return Server(
                    id=row['id'],
                    name=row['name'],
                    host=row['host'],
                    port=row['port'],
                    username=row['username'],
                    password=row['password'],
                    private_key_path=row['private_key_path'],
                    logs=logs
                )
            return None

    def list_servers(self) -> List[Server]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM servers ORDER BY name")
            servers = []
            for row in cursor.fetchall():
                # Parse logs back to list
                logs = row['logs'].split(',') if row['logs'] else []
                server = Server(
                    id=row['id'],
                    name=row['name'],
                    host=row['host'],
                    port=row['port'],
                    username=row['username'],
                    password=row['password'],
                    private_key_path=row['private_key_path'],
                    logs=logs
                )
                servers.append(server)
            return servers

    def delete_server(self, name: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM servers WHERE name = ?", (name,))
            conn.commit()
            return cursor.rowcount > 0


class SQLiteAlertExceptionRepository(AlertExceptionRepository):
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._init_db()

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alert_exceptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_type TEXT NOT NULL,
                    value TEXT NOT NULL,
                    description TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def save_exception(self, exception: AlertException) -> bool:
        with self._get_connection() as conn:
            if exception.id:
                # Update existing exception
                conn.execute("""
                    UPDATE alert_exceptions 
                    SET rule_type = ?, value = ?, description = ?, enabled = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    exception.rule_type, exception.value, exception.description,
                    exception.enabled, datetime.utcnow().isoformat(), exception.id
                ))
            else:
                # Insert new exception
                conn.execute("""
                    INSERT INTO alert_exceptions (rule_type, value, description, enabled)
                    VALUES (?, ?, ?, ?)
                """, (
                    exception.rule_type, exception.value, exception.description, exception.enabled
                ))
            
            conn.commit()
            return True

    def list_exceptions(self) -> List[AlertException]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM alert_exceptions ORDER BY created_at DESC")
            exceptions = []
            for row in cursor.fetchall():
                exception = AlertException(
                    id=row['id'],
                    rule_type=row['rule_type'],
                    value=row['value'],
                    description=row['description'],
                    enabled=bool(row['enabled']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
                )
                exceptions.append(exception)
            return exceptions

    def get_exception(self, exception_id: int) -> Optional[AlertException]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM alert_exceptions WHERE id = ?", (exception_id,))
            row = cursor.fetchone()
            if row:
                return AlertException(
                    id=row['id'],
                    rule_type=row['rule_type'],
                    value=row['value'],
                    description=row['description'],
                    enabled=bool(row['enabled']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
                )
            return None

    def update_exception(self, exception: AlertException) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                UPDATE alert_exceptions 
                SET rule_type = ?, value = ?, description = ?, enabled = ?, updated_at = ?
                WHERE id = ?
            """, (
                exception.rule_type, exception.value, exception.description,
                exception.enabled, datetime.utcnow().isoformat(), exception.id
            ))
            conn.commit()
            return cursor.rowcount > 0

    def delete_exception(self, exception_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM alert_exceptions WHERE id = ?", (exception_id,))
            conn.commit()
            return cursor.rowcount > 0

    def is_alert_excepted(self, alert: Alert) -> bool:
        with self._get_connection() as conn:
            # Check all enabled exceptions
            cursor = conn.execute("""
                SELECT * FROM alert_exceptions WHERE enabled = TRUE
            """)
            
            for row in cursor.fetchall():
                rule_type = row['rule_type']
                value = row['value']
                
                if rule_type == "ip" and alert.ip_address and value in alert.ip_address:
                    return True
                elif rule_type == "username" and alert.username and value in alert.username:
                    return True
                elif rule_type == "server" and value in alert.server_name:
                    return True
                elif rule_type == "log_source" and value in alert.log_source:
                    return True
                elif rule_type == "rule_pattern" and value in alert.rule:
                    return True
            
            return False
