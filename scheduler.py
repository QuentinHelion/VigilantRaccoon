from __future__ import annotations

import threading
import time
import logging
from datetime import datetime
from typing import List

from config import AppConfig
from infrastructure.ssh.ssh_client import SSHLogClient
from infrastructure.persistence.sqlite_repositories import (
    SQLiteAlertRepository,
    SQLiteStateRepository,
    SQLiteServerRepository,
)
from infrastructure.notifiers.email_notifier import EmailNotifier
from use_cases.detect_security_events import detect_alerts
from domain.entities import Server


class CollectorThread(threading.Thread):
    def __init__(self, cfg: AppConfig) -> None:
        super().__init__(daemon=True)
        self._cfg = cfg
        self._stop_event = threading.Event()
        self._wake_event = threading.Event()
        self._ssh = SSHLogClient(timeout_seconds=15)
        self._alerts_repo = SQLiteAlertRepository(cfg.storage.sqlite_path)
        self._state_repo = SQLiteStateRepository(cfg.storage.sqlite_path)
        self._server_repo = SQLiteServerRepository(cfg.storage.sqlite_path)
        self._notifier = EmailNotifier(cfg.email)
        self._log = logging.getLogger(self.__class__.__name__)
        self._seed_servers_if_needed()

    def trigger_refresh(self) -> None:
        self._wake_event.set()

    def _seed_servers_if_needed(self) -> None:
        existing = self._server_repo.list_servers()
        if not existing and self._cfg.servers:
            for s in self._cfg.servers:
                self._server_repo.upsert_server(
                    Server(
                        name=s.name,
                        host=s.host,
                        port=s.port,
                        username=s.username,
                        password=s.password,
                        private_key_path=s.private_key_path,
                        logs=s.logs,
                    )
                )
            self._log.info("Seeded %d server(s) from config.yaml", len(self._cfg.servers))

    def stop(self) -> None:
        self._stop_event.set()
        self._wake_event.set()

    def run(self) -> None:
        self._log.info("Collector thread started")
        ignore_ips = set(self._cfg.collection.ignore_source_ips or [])
        while not self._stop_event.is_set():
            start = time.time()
            new_alerts: List = []

            servers = self._server_repo.list_servers()
            self._log.debug("Collecting from %d server(s)", len(servers))

            for server in servers:
                sources = server.logs or ["ssh:auto"]
                self._log.debug("Server %s sources: %s", server.name, sources)
                for source in sources:
                    try:
                        if source == "ssh:auto":
                            lines, log_identifier = self._ssh.fetch_ssh_auto(_to_serverconfig(server), self._cfg.collection.tail_lines)
                        elif source.startswith("journal:"):
                            unit = source.split(":", 1)[1]
                            lines = self._ssh.fetch_journal_unit_tail(_to_serverconfig(server), unit, self._cfg.collection.tail_lines)
                            log_identifier = f"journal:{unit}"
                        else:
                            lines = self._ssh.fetch_tail(_to_serverconfig(server), source, self._cfg.collection.tail_lines)
                            log_identifier = source
                        self._log.debug("Fetched %d lines from %s:%s", len(lines), server.name, log_identifier)
                    except Exception as e:
                        self._log.warning("Fetch failed for %s %s: %s", server.name, source, e)
                        continue

                    last_ts = self._state_repo.get_last_seen_timestamp(server.name, log_identifier)
                    now = datetime.utcnow()
                    recent_lines = []
                    for line in lines:
                        ts = _safe_parse_ts(line, now)
                        if last_ts is None or (ts is not None and ts > last_ts):
                            recent_lines.append(line)

                    alerts = detect_alerts(server.name, log_identifier, recent_lines, now=now)
                    # Filter out alerts from ignored IPs
                    if ignore_ips:
                        alerts = [a for a in alerts if not (a.ip_address and a.ip_address in ignore_ips)]

                    saved = self._alerts_repo.save_alerts(alerts)
                    if alerts:
                        newest_ts = max((a.timestamp for a in alerts), default=last_ts or now)
                        self._state_repo.set_last_seen_timestamp(server.name, log_identifier, newest_ts)
                    if saved:
                        new_alerts.extend(alerts)
                        self._log.info("%d new alert(s) from %s:%s", saved, server.name, log_identifier)

            if new_alerts:
                try:
                    self._notifier.send_alerts(new_alerts)
                except Exception as e:
                    self._log.warning("Email notification failed: %s", e)

            elapsed = time.time() - start
            sleep_for = max(1.0, self._cfg.poll_interval_seconds - elapsed)
            self._log.debug("Cycle done in %.2fs, sleeping %.2fs", elapsed, sleep_for)
            self._wake_event.wait(timeout=sleep_for)
            self._wake_event.clear()


def _to_serverconfig(s: Server):
    from config import ServerConfig

    return ServerConfig(
        name=s.name,
        host=s.host,
        port=s.port,
        username=s.username,
        password=s.password,
        private_key_path=s.private_key_path,
        logs=s.logs or [],
    )


def _safe_parse_ts(line: str, now: datetime) -> datetime | None:
    from use_cases.detect_security_events import parse_timestamp

    try:
        return parse_timestamp(line, now)
    except Exception:
        return None
