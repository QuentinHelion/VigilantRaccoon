from __future__ import annotations

import smtplib
from email.mime.text import MIMEText
from typing import Iterable

from config import EmailConfig
from domain.entities import Alert


class EmailNotifier:
    def __init__(self, cfg: EmailConfig) -> None:
        self._cfg = cfg

    def send_alerts(self, alerts: Iterable[Alert]) -> None:
        alerts_list = list(alerts)
        if not self._cfg.enabled or not alerts_list or not self._cfg.to_addrs:
            return

        subject = f"VigilantRaccoon: {len(alerts_list)} new security alert(s)"
        body_lines = []
        for a in alerts_list:
            body_lines.append(
                f"[{a.timestamp.isoformat()}] {a.level.upper()} {a.server_name} {a.source_log} {a.ip_address or ''}\n{a.message}\n"
            )
        body = "\n".join(body_lines)

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self._cfg.from_addr or (self._cfg.username or "alerts@example.com")
        msg["To"] = ", ".join(self._cfg.to_addrs)

        if self._cfg.use_tls:
            server = smtplib.SMTP(self._cfg.smtp_host, self._cfg.smtp_port, timeout=15)
            server.starttls()
        else:
            server = smtplib.SMTP(self._cfg.smtp_host, self._cfg.smtp_port, timeout=15)

        try:
            if self._cfg.username and self._cfg.password:
                server.login(self._cfg.username, self._cfg.password)
            server.sendmail(msg["From"], self._cfg.to_addrs, msg.as_string())
        finally:
            try:
                server.quit()
            except Exception:
                pass
