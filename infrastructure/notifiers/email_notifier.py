from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
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

        subject = f"🔒 VigilantRaccoon: {len(alerts_list)} new security alert(s)"
        
        # Create HTML email
        html_body = self._create_html_alerts_body(alerts_list)
        text_body = self._create_text_alerts_body(alerts_list)
        
        self._send_email(subject, html_body, text_body)

    def send_critical_alert(self, alerts: Iterable[Alert]) -> None:
        """Send immediate notification for critical security events."""
        alerts_list = list(alerts)
        if not self._cfg.enabled or not alerts_list or not self._cfg.to_addrs:
            return

        subject = f"🚨 URGENT: {len(alerts_list)} critical security event(s) detected!"
        
        # Create HTML email
        html_body = self._create_html_critical_body(alerts_list)
        text_body = self._create_text_critical_body(alerts_list)
        
        self._send_email(subject, html_body, text_body)

    def _create_html_alerts_body(self, alerts: list) -> str:
        """Create HTML body for regular alerts."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
                .container {{ max-width: 800px; margin: 20px auto; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: 300; }}
                .header .subtitle {{ margin: 10px 0 0 0; opacity: 0.9; font-size: 16px; }}
                .summary {{ background: #f8f9fa; padding: 25px; border-bottom: 1px solid #e9ecef; }}
                .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; margin-top: 20px; }}
                .summary-item {{ text-align: center; padding: 15px; background: white; border-radius: 8px; border: 1px solid #e9ecef; }}
                .summary-number {{ font-size: 24px; font-weight: bold; color: #495057; }}
                .summary-label {{ font-size: 12px; color: #6c757d; text-transform: uppercase; margin-top: 5px; }}
                .alerts-section {{ padding: 25px; }}
                .alert-item {{ background: #f8f9fa; margin: 15px 0; padding: 20px; border-radius: 8px; border-left: 4px solid #dee2e6; }}
                .alert-item.high {{ border-left-color: #dc3545; background: #fff5f5; }}
                .alert-item.medium {{ border-left-color: #fd7e14; background: #fff8f0; }}
                .alert-item.info {{ border-left-color: #17a2b8; background: #f0f9ff; }}
                .alert-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
                .alert-level {{ font-weight: bold; text-transform: uppercase; font-size: 12px; padding: 4px 8px; border-radius: 4px; }}
                .alert-level.high {{ background: #dc3545; color: white; }}
                .alert-level.medium {{ background: #fd7e14; color: white; }}
                .alert-level.info {{ background: #17a2b8; color: white; }}
                .alert-timestamp {{ color: #6c757d; font-size: 12px; }}
                .alert-server {{ font-weight: bold; color: #495057; margin: 5px 0; }}
                .alert-ip {{ background: #e9ecef; padding: 2px 6px; border-radius: 3px; font-family: monospace; font-size: 12px; }}
                .alert-message {{ margin: 10px 0; color: #495057; line-height: 1.5; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; font-size: 12px; border-top: 1px solid #e9ecef; }}
                .footer a {{ color: #667eea; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 VigilantRaccoon</h1>
                    <div class="subtitle">Security Monitoring System</div>
                </div>
                
                <div class="summary">
                    <h2 style="margin: 0 0 15px 0; color: #495057; font-size: 20px;">📊 Alert Summary</h2>
                    <div class="summary-grid">
                        <div class="summary-item">
                            <div class="summary-number">{len(alerts)}</div>
                            <div class="summary-label">Total Alerts</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-number">{len(set(a.server_name for a in alerts))}</div>
                            <div class="summary-label">Servers Affected</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-number">{len([a for a in alerts if a.level == 'high'])}</div>
                            <div class="summary-label">High Priority</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-number">{len([a for a in alerts if a.level == 'medium'])}</div>
                            <div class="summary-label">Medium Priority</div>
                        </div>
                    </div>
                </div>
                
                <div class="alerts-section">
                    <h2 style="margin: 0 0 20px 0; color: #495057; font-size: 20px;">🚨 Security Alerts</h2>
        """
        
        for alert in alerts:
            level_class = f"alert-item {alert.level}"
            level_badge = f"<span class='alert-level {alert.level}'>{alert.level.upper()}</span>"
            timestamp = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
            ip_display = f"<span class='alert-ip'>{alert.ip_address}</span>" if alert.ip_address else "N/A"
            
            html += f"""
                    <div class="{level_class}">
                        <div class="alert-header">
                            {level_badge}
                            <span class="alert-timestamp">{timestamp}</span>
                        </div>
                        <div class="alert-server">🖥️ {alert.server_name} - {alert.log_source}</div>
                        <div style="margin: 5px 0;">
                            <strong>IP:</strong> {ip_display}
                            {f'<br><strong>Rule:</strong> <span class="alert-ip">{alert.rule}</span>' if alert.rule else ''}
                        </div>
                        <div class="alert-message">{alert.message}</div>
                    </div>
            """
        
        html += """
                </div>
                
                <div class="footer">
                    <p>This is an automated alert from <strong>VigilantRaccoon</strong></p>
                    <p>Please review these security events and take appropriate action</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def _create_html_critical_body(self, alerts: list) -> str:
        """Create HTML body for critical alerts."""
        # Group alerts by server
        alerts_by_server = {}
        for a in alerts:
            if a.server_name not in alerts_by_server:
                alerts_by_server[a.server_name] = []
            alerts_by_server[a.server_name].append(a)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
                .container {{ max-width: 900px; margin: 20px auto; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 32px; font-weight: 300; }}
                .header .subtitle {{ margin: 10px 0 0 0; opacity: 0.9; font-size: 18px; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 20px; margin: 20px; border-radius: 8px; text-align: center; font-size: 16px; }}
                .summary {{ background: #f8f9fa; padding: 25px; border-bottom: 1px solid #e9ecef; }}
                .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; margin-top: 20px; }}
                .summary-item {{ text-align: center; padding: 15px; background: white; border-radius: 8px; border: 1px solid #e9ecef; }}
                .summary-number {{ font-size: 24px; font-weight: bold; color: #dc3545; }}
                .summary-label {{ font-size: 12px; color: #6c757d; text-transform: uppercase; margin-top: 5px; }}
                .server-section {{ margin: 20px; }}
                .server-header {{ background: #dc3545; color: white; padding: 15px 20px; border-radius: 8px 8px 0 0; font-weight: bold; font-size: 18px; }}
                .server-alerts {{ background: #fff5f5; border: 1px solid #fecaca; border-top: none; border-radius: 0 0 8px 8px; padding: 20px; }}
                .alert-item {{ background: white; margin: 10px 0; padding: 15px; border-radius: 6px; border-left: 4px solid #dc3545; }}
                .alert-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
                .alert-level {{ font-weight: bold; text-transform: uppercase; font-size: 12px; padding: 4px 8px; border-radius: 4px; background: #dc3545; color: white; }}
                .alert-timestamp {{ color: #6c757d; font-size: 12px; }}
                .alert-ip {{ background: #e9ecef; padding: 2px 6px; border-radius: 3px; font-family: monospace; font-size: 12px; }}
                .alert-message {{ margin: 10px 0; color: #495057; line-height: 1.5; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; font-size: 12px; border-top: 1px solid #e9ecef; }}
                .footer a {{ color: #dc3545; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 CRITICAL SECURITY ALERTS</h1>
                    <div class="subtitle">IMMEDIATE ATTENTION REQUIRED</div>
                </div>
                
                <div class="warning">
                    ⚠️ <strong>URGENT:</strong> {len(alerts)} critical security event(s) detected requiring immediate investigation!
                </div>
                
                <div class="summary">
                    <h2 style="margin: 0 0 15px 0; color: #495057; font-size: 20px;">📊 Critical Event Summary</h2>
                    <div class="summary-grid">
                        <div class="summary-item">
                            <div class="summary-number">{len(alerts)}</div>
                            <div class="summary-label">Critical Events</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-number">{len(alerts_by_server)}</div>
                            <div class="summary-label">Servers Affected</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-number">{len([a for a in alerts if a.rule == 'sshd_failed'])}</div>
                            <div class="summary-label">SSH Failures</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-number">{len([a for a in alerts if a.rule == 'fail2ban_ban'])}</div>
                            <div class="summary-label">Fail2Ban Bans</div>
                        </div>
                    </div>
                </div>
        """
        
        for server_name, server_alerts in alerts_by_server.items():
            html += f"""
                <div class="server-section">
                    <div class="server-header">🖥️ SERVER: {server_name}</div>
                    <div class="server-alerts">
            """
            
            for alert in server_alerts:
                timestamp = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
                ip_display = f"<span class='alert-ip'>{alert.ip_address}</span>" if alert.ip_address else "N/A"
                
                html += f"""
                        <div class="alert-item">
                            <div class="alert-header">
                                <span class="alert-level">{alert.rule.upper()}</span>
                                <span class="alert-timestamp">{timestamp}</span>
                            </div>
                            <div style="margin: 5px 0;">
                                <strong>Source:</strong> {alert.log_source}<br>
                                <strong>IP:</strong> {ip_display}
                            </div>
                            <div class="alert-message">{alert.message}</div>
                        </div>
                """
            
            html += """
                    </div>
                </div>
            """
        
        html += """
                <div class="footer">
                    <p><strong>🚨 IMMEDIATE ACTION REQUIRED</strong></p>
                    <p>This is an automated critical alert from <strong>VigilantRaccoon</strong></p>
                    <p>Please investigate these security events immediately and take appropriate action</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def _create_text_alerts_body(self, alerts: list) -> str:
        """Create plain text body for regular alerts."""
        body_lines = [
            "🔒 VigilantRaccoon - Security Monitoring System",
            "=" * 60,
            "",
            f"Total alerts: {len(alerts)}",
            f"Servers affected: {len(set(a.server_name for a in alerts))}",
            "",
        ]
        
        for a in alerts:
            body_lines.extend([
                f"[{a.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}] {a.level.upper()} {a.server_name} {a.log_source}",
                f"IP: {a.ip_address or 'N/A'}",
                f"Rule: {a.rule or 'N/A'}",
                f"Message: {a.message}",
                "-" * 40,
                ""
            ])
        
        body_lines.extend([
            "=" * 60,
            "This is an automated alert from VigilantRaccoon.",
            "Please review these security events and take appropriate action.",
        ])
        
        return "\n".join(body_lines)

    def _create_text_critical_body(self, alerts: list) -> str:
        """Create plain text body for critical alerts."""
        alerts_by_server = {}
        for a in alerts:
            if a.server_name not in alerts_by_server:
                alerts_by_server[a.server_name] = []
            alerts_by_server[a.server_name].append(a)

        body_lines = [
            "🚨 CRITICAL SECURITY ALERTS - IMMEDIATE ATTENTION REQUIRED 🚨",
            "=" * 70,
            "",
            f"Total critical events: {len(alerts)}",
            f"Servers affected: {len(alerts_by_server)}",
            "",
        ]

        for server_name, server_alerts in alerts_by_server.items():
            body_lines.extend([
                f"🔴 SERVER: {server_name}",
                "-" * 40,
            ])
            
            for a in server_alerts:
                body_lines.extend([
                    f"  • [{a.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}] {a.rule.upper()}",
                    f"    Source: {a.log_source}",
                    f"    IP: {a.ip_address or 'N/A'}",
                    f"    Message: {a.message}",
                    ""
                ])

        body_lines.extend([
            "=" * 70,
            "🚨 IMMEDIATE ACTION REQUIRED 🚨",
            "This is an automated critical alert from VigilantRaccoon.",
            "Please investigate these security events immediately and take appropriate action.",
        ])
        
        return "\n".join(body_lines)

    def _send_email(self, subject: str, html_body: str, text_body: str) -> None:
        """Send email with both HTML and text versions."""
        msg = MIMEMultipart('alternative')
        msg["Subject"] = subject
        msg["From"] = self._cfg.from_addr or (self._cfg.username or "alerts@example.com")
        msg["To"] = ", ".join(self._cfg.to_addrs)

        # Attach both HTML and text versions
        text_part = MIMEText(text_body, 'plain', 'utf-8')
        html_part = MIMEText(html_body, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)

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
