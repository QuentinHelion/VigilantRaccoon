from __future__ import annotations

import threading
import time
import logging
from datetime import datetime, timedelta
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

    def _check_recent_critical_events(self, server_name: str) -> List:
        """Check for critical events in the last hour that need immediate notification."""
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_alerts = self._alerts_repo.list_alerts(limit=1000, since=one_hour_ago)
        
        critical_events = []
        for alert in recent_alerts:
            if alert.server_name == server_name:
                # Check for recent auth failures or fail2ban events
                if (alert.rule in ["sshd_failed", "pam_auth_failure", "fail2ban_ban"] and 
                    alert.timestamp >= one_hour_ago):
                    critical_events.append(alert)
        
        return critical_events

    def _should_send_immediate_alert(self, new_alerts: List) -> bool:
        """Determine if we should send an immediate alert for critical events."""
        if not new_alerts:
            return False
        
        # Check if any new alerts are critical
        critical_rules = {"sshd_failed", "pam_auth_failure", "fail2ban_ban", "break_in_attempt"}
        return any(alert.rule in critical_rules for alert in new_alerts)

    def _filter_monitoring_job_logs(self, alerts: List) -> List:
        """Filter out SSH authentication logs that come from monitoring jobs to prevent spam."""
        filtered_alerts = []
        for alert in alerts:
            # Skip SSH accepted logins from monitoring jobs (these are usually just the app checking logs)
            if (alert.rule == "sshd_accepted" and 
                alert.ip_address in (self._cfg.collection.ignore_source_ips or [])):
                self._log.debug("Filtering out monitoring job SSH login: %s from %s", alert.ip_address, alert.server_name)
                continue
            
            # Skip SSH accepted logins that look like monitoring activity
            if (alert.rule == "sshd_accepted" and 
                alert.message and 
                any(keyword in alert.message.lower() for keyword in ["debian", "root", "bitwarden"])):
                # This is likely a legitimate monitoring login, not a security concern
                self._log.debug("Filtering out likely monitoring SSH login: %s", alert.message)
                continue
                
            filtered_alerts.append(alert)
        
        return filtered_alerts

    def stop(self) -> None:
        self._stop_event.set()
        self._wake_event.set()

    def run(self) -> None:
        self._log.info("Collector thread started")
        ignore_ips = set(self._cfg.collection.ignore_source_ips or [])
        while not self._stop_event.is_set():
            start = time.time()
            new_alerts: List = []
            critical_alerts: List = []

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
                    
                    # Filter out monitoring job logs to prevent spam
                    alerts = self._filter_monitoring_job_logs(alerts)

                    saved = self._alerts_repo.save_alerts(alerts)
                    if alerts:
                        newest_ts = max((a.timestamp for a in alerts), default=last_ts or now)
                        self._state_repo.set_last_seen_timestamp(server.name, log_identifier, newest_ts)
                    if saved:
                        new_alerts.extend(alerts)
                        # Check for critical events that need immediate notification
                        critical_rules = {"sshd_failed", "pam_auth_failure", "fail2ban_ban", "break_in_attempt"}
                        critical_new = [a for a in alerts if a.rule in critical_rules]
                        if critical_new:
                            critical_alerts.extend(critical_new)
                            self._log.warning("CRITICAL: %d new critical alert(s) from %s:%s", len(critical_new), server.name, log_identifier)
                        self._log.info("%d new alert(s) from %s:%s", saved, server.name, log_identifier)

            # Send immediate notifications for critical events
            if critical_alerts and self._cfg.email.enabled:
                try:
                    self._notifier.send_critical_alert(critical_alerts)
                    self._log.info("Sent immediate critical alert email for %d events", len(critical_alerts))
                except Exception as e:
                    self._log.error("Failed to send critical alert email: %s", e)

            # Send regular batch notifications for all new alerts
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
