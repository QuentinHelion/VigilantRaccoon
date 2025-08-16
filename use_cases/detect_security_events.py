from __future__ import annotations

import re
from datetime import datetime
from typing import Iterable, List

from domain.entities import Alert

# Precompile regexes for performance
IPV4_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b")
FAIL2BAN_BAN_RE = re.compile(r"fail2ban.*\bBan\b\s+(?P<ip>\S+)", re.IGNORECASE)
FAIL2BAN_UNBAN_RE = re.compile(r"fail2ban.*\bUnban\b\s+(?P<ip>\S+)", re.IGNORECASE)
SSHD_FAILED_RE = re.compile(r"sshd\[\d+\]:\s+(Failed password|Invalid user|Connection closed by authenticating user|Received disconnect)\b.*", re.IGNORECASE)
PAM_AUTH_FAIL_RE = re.compile(r"pam_unix\(sshd:auth\):\s+authentication failure", re.IGNORECASE)
BREAKIN_RE = re.compile(r"Possible break-in attempt", re.IGNORECASE)
SSHD_ACCEPTED_RE = re.compile(r"sshd\[\d+\]:\s+Accepted (?:password|publickey) for (?P<user>\S+) from (?P<ip>\S+)\b", re.IGNORECASE)

# New process monitoring regexes
PROCESS_NETWORK_CONNECTION_RE = re.compile(r"kernel:\s+.*?SRC=(?P<src_ip>\S+)\s+DST=(?P<dst_ip>\S+)\s+.*?PROTO=(?P<proto>\S+)\s+SPT=(?P<src_port>\d+)\s+DPT=(?P<dst_port>\d+)", re.IGNORECASE)
PROCESS_PRIVILEGE_ESCALATION_RE = re.compile(r"sudo:\s+(?P<user>\S+)\s+:\s+(?P<command>.*?)\s+;\s+TTY=(?P<tty>\S+)", re.IGNORECASE)
PROCESS_SUID_EXECUTION_RE = re.compile(r"audit\[\d+\]:\s+path=(?P<path>\S+)\s+dev=\S+\s+ino=\d+\s+mode=\S+\s+ouid=\d+\s+ogid=\d+\s+ruid=\d+\s+rgid=\d+\s+suid=\d+\s+sgid=\d+\s+fsuid=\d+\s+fsgid=\d+\s+tty=\S+\s+ses=\d+\s+comm=(?P<comm>\S+)\s+exe=(?P<exe>\S+)\s+key=(?P<key>\S+)", re.IGNORECASE)
PROCESS_TEMP_FILE_CREATION_RE = re.compile(r"(?:/tmp/|/var/tmp/|/dev/shm/).*\.(?:sh|py|pl|rb|js|php|exe|bat|cmd)$", re.IGNORECASE)
PROCESS_CRON_JOB_ADDITION_RE = re.compile(r"cron\[\d+\]:\s+(?P<user>\S+)\s+CMD\s+\((?P<command>.*?)\)", re.IGNORECASE)
PROCESS_SERVICE_START_RE = re.compile(r"systemd\[\d+\]:\s+(?P<service>\S+)\.service:\s+(?:Started|Starting)", re.IGNORECASE)
PROCESS_SUSPICIOUS_COMMAND_RE = re.compile(r"(?:nc\s+.*?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|wget\s+.*?http|curl\s+.*?http|bash\s+-c\s+.*?\$|eval\s+.*?\$|base64\s+-d)", re.IGNORECASE)

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

        # Existing SSH and authentication alerts
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
            user = m.group("user")
            alerts.append(Alert(server_name=server_name, log_source=source_log, rule="sshd_accepted", level="info", message=line.strip(), ip_address=ip, username=user, timestamp=ts))
            continue
        if BREAKIN_RE.search(line):
            ip = None
            if m_ip := IPV4_RE.search(line):
                ip = m_ip.group(0)
            alerts.append(Alert(server_name=server_name, log_source=source_log, rule="break_in_attempt", level="high", message=line.strip(), ip_address=ip, timestamp=ts))
            continue

        # New process monitoring alerts
        if m := PROCESS_NETWORK_CONNECTION_RE.search(line):
            src_ip = m.group("src_ip")
            dst_ip = m.group("dst_ip")
            proto = m.group("proto")
            src_port = m.group("src_port")
            dst_port = m.group("dst_port")
            message = f"Network connection: {src_ip}:{src_port} -> {dst_ip}:{dst_port} ({proto})"
            alerts.append(Alert(server_name=server_name, log_source=source_log, rule="network_connection", level="medium", message=message, ip_address=dst_ip, timestamp=ts))
            continue

        if m := PROCESS_PRIVILEGE_ESCALATION_RE.search(line):
            user = m.group("user")
            command = m.group("command")
            tty = m.group("tty")
            message = f"Privilege escalation: {user} executed '{command}' via {tty}"
            alerts.append(Alert(server_name=server_name, log_source=source_log, rule="privilege_escalation", level="high", message=message, username=user, timestamp=ts))
            continue

        if m := PROCESS_SUID_EXECUTION_RE.search(line):
            path = m.group("path")
            comm = m.group("comm")
            exe = m.group("exe")
            message = f"SUID execution: {comm} ({exe}) executed {path}"
            alerts.append(Alert(server_name=server_name, log_source=source_log, rule="suid_execution", level="medium", message=message, timestamp=ts))
            continue

        if PROCESS_TEMP_FILE_CREATION_RE.search(line):
            message = f"Suspicious temporary file creation: {line.strip()}"
            alerts.append(Alert(server_name=server_name, log_source=source_log, rule="temp_file_creation", level="medium", message=message, timestamp=ts))
            continue

        if m := PROCESS_CRON_JOB_ADDITION_RE.search(line):
            user = m.group("user")
            command = m.group("command")
            message = f"Cron job execution: {user} executed '{command}'"
            alerts.append(Alert(server_name=server_name, log_source=source_log, rule="cron_job_execution", level="info", message=message, username=user, timestamp=ts))
            continue

        if m := PROCESS_SERVICE_START_RE.search(line):
            service = m.group("service")
            message = f"Service started: {service}"
            alerts.append(Alert(server_name=server_name, log_source=source_log, rule="service_start", level="info", message=message, timestamp=ts))
            continue

        if m := PROCESS_SUSPICIOUS_COMMAND_RE.search(line):
            message = f"Suspicious command detected: {line.strip()}"
            alerts.append(Alert(server_name=server_name, log_source=source_log, rule="suspicious_command", level="high", message=message, timestamp=ts))
            continue

    return alerts
