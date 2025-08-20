from __future__ import annotations

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from datetime import datetime
import logging

from domain.entities import Alert
from config import EmailConfig

log = logging.getLogger("EmailNotifier")

class EmailNotifier:
    """Email notification system for security alerts"""
    
    def __init__(self, config: EmailConfig):
        self.config = config
        self.smtp_server = config.smtp_host
        self.smtp_port = config.smtp_port
        self.username = config.username
        self.password = config.password
        self.from_addr = config.from_addr
        self.to_addrs = config.to_addrs
        self.use_tls = config.use_tls
        
    def send_alert_notification(self, alerts_list: List[Alert]) -> bool:
        """Send email notification for new alerts"""
        if not self.config.enabled or not alerts_list:
            return False
            
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"VigilantRaccoon: {len(alerts_list)} new security alert(s)"
            msg['From'] = self.from_addr
            msg['To'] = ', '.join(self.to_addrs)
            
            # Create HTML content
            html_content = self._create_html_content(alerts_list)
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            return self._send_email(msg)
            
        except Exception as e:
            log.error("Failed to send alert notification: %s", e)
            return False
    
    def send_critical_alert(self, alerts: List[Alert]) -> bool:
        """Send immediate notification for critical alerts"""
        if not self.config.enabled or not alerts:
            return False
            
        try:
            # Create urgent message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"URGENT: {len(alerts)} Critical Security Alert(s) - VigilantRaccoon"
            msg['From'] = self.from_addr
            msg['To'] = ', '.join(self.to_addrs)
            msg['Priority'] = 'high'
            msg['X-Priority'] = '1'
            msg['X-MSMail-Priority'] = 'High'
            
            # Create HTML content
            html_content = self._create_critical_html_content(alerts)
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            return self._send_email(msg)
            
        except Exception as e:
            log.error("Failed to send critical alert: %s", e)
            return False
    
    def _create_html_content(self, alerts: List[Alert]) -> str:
        """Create HTML content for regular alerts"""
        # Group alerts by server
        alerts_by_server = {}
        for alert in alerts:
            if alert.server_name not in alerts_by_server:
                alerts_by_server[alert.server_name] = []
            alerts_by_server[alert.server_name].append(alert)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Security Alerts</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .header h1 {{ color: #2c3e50; margin: 0; font-size: 28px; }}
                .header p {{ color: #7f8c8d; margin: 10px 0 0 0; }}
                .summary {{ background: #ecf0f1; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
                .summary h2 {{ margin: 0 0 15px 0; color: #2c3e50; font-size: 20px; }}
                .summary p {{ margin: 0; color: #34495e; }}
                .server-section {{ margin-bottom: 30px; }}
                .server-header {{ background: #3498db; color: white; padding: 15px; border-radius: 8px 8px 0 0; font-weight: bold; }}
                .alert-item {{ border: 1px solid #bdc3c7; border-top: none; padding: 15px; }}
                .alert-item:last-child {{ border-radius: 0 0 8px 8px; }}
                .alert-rule {{ font-weight: bold; color: #e74c3c; margin-bottom: 5px; }}
                .alert-message {{ color: #2c3e50; margin-bottom: 5px; }}
                .alert-server {{ color: #7f8c8d; font-size: 12px; }}
                .alert-time {{ color: #95a5a6; font-size: 11px; }}
                .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ecf0f1; color: #7f8c8d; font-size: 12px; }}
                .level-high {{ color: #e74c3c; }}
                .level-medium {{ color: #f39c12; }}
                .level-info {{ color: #3498db; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>VigilantRaccoon</h1>
                    <p>Security Monitoring System</p>
                </div>
                
                <div class="summary">
                    <h2>Alert Summary</h2>
                    <p><strong>{len(alerts)} new security alert(s)</strong> detected across <strong>{len(alerts_by_server)} server(s)</strong></p>
                    <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
        """
        
        # Add alerts by server
        for server_name, server_alerts in alerts_by_server.items():
            html += f"""
                <div class="server-section">
                    <div class="server-header">SERVER: {server_name}</div>
            """
            
            for alert in server_alerts:
                level_class = f"level-{alert.level}"
                html += f"""
                    <div class="alert-item">
                        <div class="alert-rule {level_class}">{alert.rule.upper()}</div>
                        <div class="alert-message">{alert.message}</div>
                        <div class="alert-server">SERVER: {alert.server_name} - {alert.log_source}</div>
                        <div class="alert-time">{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
                    </div>
                """
            
            html += "</div>"
        
        html += """
                <div class="footer">
                    <p>This is an automated message from VigilantRaccoon Security Monitoring System</p>
                    <p>Please do not reply to this email</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_critical_html_content(self, alerts: List[Alert]) -> str:
        """Create HTML content for critical alerts"""
        # Group alerts by server
        alerts_by_server = {}
        for alert in alerts:
            if alert.server_name not in alerts_by_server:
                alerts_by_server[alert.server_name] = []
            alerts_by_server[alert.server_name].append(alert)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Critical Security Alert</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .header h1 {{ color: #e74c3c; margin: 0; font-size: 32px; }}
                .header p {{ color: #7f8c8d; margin: 10px 0 0 0; }}
                .urgent {{ background: #e74c3c; color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; text-align: center; font-size: 18px; }}
                .summary {{ background: #ecf0f1; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
                .summary h2 {{ margin: 0 0 15px 0; color: #2c3e50; font-size: 20px; }}
                .summary p {{ margin: 0; color: #34495e; }}
                .server-section {{ margin-bottom: 30px; }}
                .server-header {{ background: #e74c3c; color: white; padding: 15px; border-radius: 8px 8px 0 0; font-weight: bold; }}
                .alert-item {{ border: 1px solid #bdc3c7; border-top: none; padding: 15px; }}
                .alert-item:last-child {{ border-radius: 0 0 8px 8px; }}
                .alert-rule {{ font-weight: bold; color: #e74c3c; margin-bottom: 5px; }}
                .alert-message {{ color: #2c3e50; margin-bottom: 5px; }}
                .alert-server {{ color: #7f8c8d; font-size: 12px; }}
                .alert-time {{ color: #95a5a6; font-size: 11px; }}
                .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ecf0f1; color: #7f8c8d; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>CRITICAL SECURITY ALERT</h1>
                    <p>VigilantRaccoon Security Monitoring System</p>
                </div>
                
                <div class="urgent">
                    <strong>URGENT:</strong> {len(alerts)} critical security event(s) detected requiring immediate investigation!
                </div>
                
                <div class="summary">
                    <h2>Critical Event Summary</h2>
                    <p><strong>{len(alerts)} critical alert(s)</strong> detected across <strong>{len(alerts_by_server)} server(s)</strong></p>
                    <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
        """
        
        # Add alerts by server
        for server_name, server_alerts in alerts_by_server.items():
            html += f"""
                <div class="server-section">
                    <div class="server-header">SERVER: {server_name}</div>
            """
            
            for alert in server_alerts:
                html += f"""
                    <div class="alert-item">
                        <div class="alert-rule">{alert.rule.upper()}</div>
                        <div class="alert-message">{alert.message}</div>
                        <div class="alert-server">SERVER: {alert.server_name} - {alert.log_source}</div>
                        <div class="alert-time">{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
                    </div>
                """
            
            html += "</div>"
        
        html += """
                <div class="footer">
                    <p>This is an automated URGENT message from VigilantRaccoon Security Monitoring System</p>
                    <p>IMMEDIATE ACTION REQUIRED - Please investigate these critical security events</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _send_email(self, msg: MIMEMultipart) -> bool:
        """Send email via SMTP"""
        try:
            if self.use_tls:
                # Use STARTTLS
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls(context=ssl.create_default_context())
            else:
                # Use SSL
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=ssl.create_default_context())
            
            if self.username and self.password:
                server.login(self.username, self.password)
            
            text = msg.as_string()
            server.sendmail(self.from_addr, self.to_addrs, text)
            server.quit()
            
            log.info("Email sent successfully to %s", self.to_addrs)
            return True
            
        except Exception as e:
            log.error("Failed to send email: %s", e)
            return False
    
    def send_daily_report(self, alerts: List[Alert]) -> bool:
        """Send daily summary report"""
        if not self.config.enabled or not alerts:
            return False
            
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Daily Security Report - {datetime.now().strftime('%Y-%m-%d')}"
            msg['From'] = self.from_addr
            msg['To'] = ', '.join(self.to_addrs)
            
            # Create HTML content for daily report
            html_content = self._create_daily_report_html(alerts)
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            return self._send_email(msg)
            
        except Exception as e:
            log.error("Failed to send daily report: %s", e)
            return False
    
    def _create_daily_report_html(self, alerts: List[Alert]) -> str:
        """Create HTML content for daily report"""
        # Group alerts by server and type
        alerts_by_server = {}
        for alert in alerts:
            if alert.server_name not in alerts_by_server:
                alerts_by_server[alert.server_name] = {}
            if alert.rule not in alerts_by_server[alert.server_name]:
                alerts_by_server[alert.server_name][alert.rule] = []
            alerts_by_server[alert.server_name][alert.rule].append(alert)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Daily Security Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .header h1 {{ color: #2c3e50; margin: 0; font-size: 28px; }}
                .header p {{ color: #7f8c8d; margin: 10px 0 0 0; }}
                .summary {{ background: #ecf0f1; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
                .summary h2 {{ margin: 0 0 15px 0; color: #2c3e50; font-size: 20px; }}
                .summary p {{ margin: 0; color: #34495e; }}
                .server-section {{ margin-bottom: 30px; }}
                .server-header {{ background: #3498db; color: white; padding: 15px; border-radius: 8px 8px 0 0; font-weight: bold; }}
                .rule-section {{ margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px; }}
                .rule-header {{ font-weight: bold; color: #2c3e50; margin-bottom: 5px; }}
                .alert-count {{ color: #7f8c8d; font-size: 12px; }}
                .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ecf0f1; color: #7f8c8d; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Daily Security Report</h1>
                    <p>VigilantRaccoon Security Monitoring System</p>
                </div>
                
                <div class="summary">
                    <h2>Daily Summary</h2>
                    <p><strong>{len(alerts)} total alert(s)</strong> across <strong>{len(alerts_by_server)} server(s)</strong></p>
                    <p>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
        """
        
        # Add alerts by server and rule
        for server_name, rules in alerts_by_server.items():
            html += f"""
                <div class="server-section">
                    <div class="server-header">SERVER: {server_name}</div>
            """
            
            for rule, rule_alerts in rules.items():
                html += f"""
                    <div class="rule-section">
                        <div class="rule-header">{rule.upper()}</div>
                        <div class="alert-count">{len(rule_alerts)} alert(s)</div>
                    </div>
                """
            
            html += "</div>"
        
        html += """
                <div class="footer">
                    <p>This is an automated daily report from VigilantRaccoon Security Monitoring System</p>
                    <p>Please do not reply to this email</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
