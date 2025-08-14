from __future__ import annotations

import re
from datetime import datetime
from typing import Iterable, List

from domain.entities import Alert

# Precompile regexes for performance
IPV4_RE = re.compile(r"(?:(?:\d{1,3}\.){3}\d{1,3})")
FAIL2BAN_BAN_RE = re.compile(r"fail2ban.*\bBan\b\s+(?P<ip>\S+)", re.IGNORECASE)
FAIL2BAN_UNBAN_RE = re.compile(r"fail2ban.*\bUnban\b\s+(?P<ip>\S+)", re.IGNORECASE)
SSHD_FAILED_RE = re.compile(r"sshd\[\d+\]:\s+(Failed password|Invalid user|Connection closed by authenticating user|Received disconnect)\b.*", re.IGNORECASE)
PAM_AUTH_FAIL_RE = re.compile(r"pam_unix\(sshd:auth\):\s+authentication failure", re.IGNORECASE)
BREAKIN_RE = re.compile(r"Possible break-in attempt", re.IGNORECASE)
SSHD_ACCEPTED_RE = re.compile(r"sshd\[\d+\]:\s+Accepted (?:password|publickey) for (?P<user>\S+) from (?P<ip>\S+)\b", re.IGNORECASE)

# Common log time formats
SYSLOG_PREFIX_RE = re.compile(r"^(?P<mon>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<host>\S+)\s+(?P<rest>.*)$")
ISO_PREFIX_RE = re.compile(r"^(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:,\d{3})?)\s+(?P<rest>.*)$")

MONTHS = {m: i for i, m in enumerate(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], start=1)}


def parse_timestamp(line: str, now: datetime) -> datetime | None:
    m = ISO_PREFIX_RE.match(line)
    if m:
        ts_str = m.group("ts").replace(",", ".")
        try:
            return datetime.fromisoformat(ts_str)
        except ValueError:
            pass

    m = SYSLOG_PREFIX_RE.match(line)
    if m:
        mon = MONTHS.get(m.group("mon"))
        day = int(m.group("day"))
        time_part = m.group("time")
        
        if mon is None:
            return None
            
        # Try to determine the correct year for the log entry
        # Start with current year and adjust if needed
        year = now.year
        
        # Create the timestamp
        try:
            log_time = datetime.fromisoformat(f"{year:04d}-{mon:02d}-{day:02d}T{time_part}")
            
            # If the log time is more than 6 months in the future, it's probably from last year
            # (e.g., if we're in January and the log is from December)
            if log_time > now and (now.month - log_time.month) > 6:
                year -= 1
                log_time = datetime.fromisoformat(f"{year:04d}-{mon:02d}-{day:02d}T{time_part}")
            
            # If the log time is more than 6 months in the past, it's probably from next year
            # (e.g., if we're in December and the log is from January)
            elif log_time < now and (log_time.month - now.month) > 6:
                year += 1
                log_time = datetime.fromisoformat(f"{year:04d}-{mon:02d}-{day:02d}T{time_part}")
            
            return log_time
            
        except Exception:
            return None

    return None


def detect_alerts(server_name: str, source_log: str, lines: Iterable[str], now: datetime | None = None) -> List[Alert]:
    if now is None:
        now = datetime.utcnow()

    alerts: List[Alert] = []

    for line in lines:
        ts = parse_timestamp(line, now) or now

        if m := FAIL2BAN_BAN_RE.search(line):
            ip = m.group("ip")
            alerts.append(Alert(server_name=server_name, log_source=source_log, rule="fail2ban_ban", level="high", message=line.strip(), ip_address=ip, timestamp=ts))
            continue
        if m := FAIL2BAN_UNBAN_RE.search(line):
            ip = m.group("ip")
            alerts.append(Alert(server_name=server_name, log_source=source_log, rule="fail2ban_unban", level="info", message=line.strip(), ip_address=ip, timestamp=ts))
            continue
        if SSHD_FAILED_RE.search(line):
            ip = None
            if m_ip := IPV4_RE.search(line):
                ip = m_ip.group(0)
            alerts.append(Alert(server_name=server_name, log_source=source_log, rule="sshd_failed", level="medium", message=line.strip(), ip_address=ip, timestamp=ts))
            continue
        if PAM_AUTH_FAIL_RE.search(line):
            ip = None
            if m_ip := IPV4_RE.search(line):
                ip = m_ip.group(0)
            alerts.append(Alert(server_name=server_name, log_source=source_log, rule="pam_auth_failure", level="medium", message=line.strip(), ip_address=ip, timestamp=ts))
            continue
        if m := SSHD_ACCEPTED_RE.search(line):
            ip = m.group("ip")
            alerts.append(Alert(server_name=server_name, log_source=source_log, rule="sshd_accepted", level="info", message=line.strip(), ip_address=ip, timestamp=ts))
            continue
        if BREAKIN_RE.search(line):
            ip = None
            if m_ip := IPV4_RE.search(line):
                ip = m_ip.group(0)
            alerts.append(Alert(server_name=server_name, log_source=source_log, rule="break_in_attempt", level="high", message=line.strip(), ip_address=ip, timestamp=ts))
            continue

    return alerts
