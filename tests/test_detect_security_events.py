#!/usr/bin/env python3
"""
Tests unitaires pour la détection des événements de sécurité
"""

import unittest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from use_cases.detect_security_events import (
    detect_alerts, 
    parse_timestamp,
    IPV4_RE,
    FAIL2BAN_BAN_RE,
    FAIL2BAN_UNBAN_RE,
    SSHD_FAILED_RE,
    PAM_AUTH_FAIL_RE,
    BREAKIN_RE,
    SSHD_ACCEPTED_RE
)


class TestTimestampParsing(unittest.TestCase):
    """Tests pour le parsing des timestamps"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    
    def test_iso_timestamp_parsing(self):
        """Test du parsing des timestamps ISO"""
        # Test avec format ISO standard
        line = "2024-01-15 10:30:45 Test log message"
        ts = parse_timestamp(line, self.now)
        self.assertIsNotNone(ts)
        self.assertEqual(ts.year, 2024)
        self.assertEqual(ts.month, 1)
        self.assertEqual(ts.day, 15)
        self.assertEqual(ts.hour, 10)
        self.assertEqual(ts.minute, 30)
        self.assertEqual(ts.second, 45)
    
    def test_iso_timestamp_with_milliseconds(self):
        """Test du parsing des timestamps ISO avec millisecondes"""
        line = "2024-01-15 10:30:45,123 Test log message"
        ts = parse_timestamp(line, self.now)
        self.assertIsNotNone(ts)
        self.assertEqual(ts.microsecond, 123000)
    
    def test_syslog_timestamp_parsing(self):
        """Test du parsing des timestamps syslog"""
        line = "Jan 15 10:30:45 test-host Test log message"
        ts = parse_timestamp(line, self.now)
        self.assertIsNotNone(ts)
        self.assertEqual(ts.month, 1)
        self.assertEqual(ts.day, 15)
        self.assertEqual(ts.hour, 10)
        self.assertEqual(ts.minute, 30)
        self.assertEqual(ts.second, 45)
    
    def test_syslog_timestamp_last_year(self):
        """Test du parsing des timestamps syslog de l'année précédente"""
        # Test en janvier avec un log de décembre
        now = datetime(2024, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
        line = "Dec 31 23:59:59 test-host Test log message"
        ts = parse_timestamp(line, now)
        self.assertIsNotNone(ts)
        self.assertEqual(ts.year, 2023)  # Devrait être l'année précédente
        self.assertEqual(ts.month, 12)
        self.assertEqual(ts.day, 31)
    
    def test_invalid_timestamp(self):
        """Test avec un timestamp invalide"""
        line = "Invalid timestamp format Test log message"
        ts = parse_timestamp(line, self.now)
        self.assertIsNone(ts)
    
    def test_empty_line(self):
        """Test avec une ligne vide"""
        line = ""
        ts = parse_timestamp(line, self.now)
        self.assertIsNone(ts)


class TestRegexPatterns(unittest.TestCase):
    """Tests pour les patterns regex"""
    
    def test_ipv4_regex(self):
        """Test du pattern de détection des adresses IPv4"""
        # Adresses valides
        self.assertIsNotNone(IPV4_RE.search("192.168.1.1"))
        self.assertIsNotNone(IPV4_RE.search("10.0.0.1"))
        self.assertIsNotNone(IPV4_RE.search("172.16.0.1"))
        
        # Adresses invalides
        self.assertIsNone(IPV4_RE.search("256.1.2.3"))
        self.assertIsNone(IPV4_RE.search("192.168.1"))
        self.assertIsNone(IPV4_RE.search("192.168.1.1.1"))
    
    def test_fail2ban_ban_regex(self):
        """Test du pattern de détection des bannissements fail2ban"""
        # Bannissements valides
        self.assertIsNotNone(FAIL2BAN_BAN_RE.search("fail2ban.actions: WARNING [sshd] Ban 192.168.1.100"))
        self.assertIsNotNone(FAIL2BAN_BAN_RE.search("fail2ban.actions: WARNING [nginx-http-auth] Ban 10.0.0.50"))
        
        # Bannissements invalides
        self.assertIsNone(FAIL2BAN_BAN_RE.search("fail2ban.actions: WARNING [sshd] Unban 192.168.1.100"))
        self.assertIsNone(FAIL2BAN_BAN_RE.search("sshd: Failed password for user from 192.168.1.100"))
    
    def test_fail2ban_unban_regex(self):
        """Test du pattern de détection des débannissements fail2ban"""
        # Débannissements valides
        self.assertIsNotNone(FAIL2BAN_UNBAN_RE.search("fail2ban.actions: WARNING [sshd] Unban 192.168.1.100"))
        self.assertIsNotNone(FAIL2BAN_UNBAN_RE.search("fail2ban.actions: WARNING [nginx-http-auth] Unban 10.0.0.50"))
        
        # Débannissements invalides
        self.assertIsNone(FAIL2BAN_UNBAN_RE.search("fail2ban.actions: WARNING [sshd] Ban 192.168.1.100"))
    
    def test_sshd_failed_regex(self):
        """Test du pattern de détection des échecs SSH"""
        # Échecs valides
        self.assertIsNotNone(SSHD_FAILED_RE.search("sshd[12345]: Failed password for user from 192.168.1.100"))
        self.assertIsNotNone(SSHD_FAILED_RE.search("sshd[67890]: Invalid user testuser from 192.168.1.100"))
        self.assertIsNotNone(SSHD_FAILED_RE.search("sshd[11111]: Connection closed by authenticating user"))
        
        # Échecs invalides
        self.assertIsNone(SSHD_FAILED_RE.search("sshd[12345]: Accepted password for user from 192.168.1.100"))
    
    def test_pam_auth_fail_regex(self):
        """Test du pattern de détection des échecs d'authentification PAM"""
        # Échecs valides
        self.assertIsNotNone(PAM_AUTH_FAIL_RE.search("pam_unix(sshd:auth): authentication failure"))
        
        # Échecs invalides
        self.assertIsNone(PAM_AUTH_FAIL_RE.search("pam_unix(sshd:auth): session opened"))
    
    def test_breakin_regex(self):
        """Test du pattern de détection des tentatives d'intrusion"""
        # Tentatives valides
        self.assertIsNotNone(BREAKIN_RE.search("Possible break-in attempt detected"))
        self.assertIsNotNone(BREAKIN_RE.search("POSSIBLE BREAK-IN ATTEMPT"))
        
        # Tentatives invalides
        self.assertIsNone(BREAKIN_RE.search("Break-in attempt failed"))
    
    def test_sshd_accepted_regex(self):
        """Test du pattern de détection des connexions SSH acceptées"""
        # Connexions valides
        self.assertIsNotNone(SSHD_ACCEPTED_RE.search("sshd[12345]: Accepted password for admin from 192.168.1.100"))
        self.assertIsNotNone(SSHD_ACCEPTED_RE.search("sshd[67890]: Accepted publickey for user from 10.0.0.50"))
        
        # Connexions invalides
        self.assertIsNone(SSHD_ACCEPTED_RE.search("sshd[12345]: Failed password for admin from 192.168.1.100"))


class TestAlertDetection(unittest.TestCase):
    """Tests pour la détection des alertes"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.server_name = "test-server"
        self.log_source = "test-log"
        self.now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    
    def test_fail2ban_ban_detection(self):
        """Test de la détection des bannissements fail2ban"""
        lines = [
            "2024-01-15 10:30:45 fail2ban.actions: WARNING [sshd] Ban 192.168.1.100"
        ]
        
        alerts = detect_alerts(self.server_name, self.log_source, lines, self.now)
        self.assertEqual(len(alerts), 1)
        
        alert = alerts[0]
        self.assertEqual(alert.server_name, self.server_name)
        self.assertEqual(alert.log_source, self.log_source)
        self.assertEqual(alert.rule, "fail2ban_ban")
        self.assertEqual(alert.level, "high")
        self.assertEqual(alert.ip_address, "192.168.1.100")
    
    def test_fail2ban_unban_detection(self):
        """Test de la détection des débannissements fail2ban"""
        lines = [
            "2024-01-15 10:30:45 fail2ban.actions: WARNING [sshd] Unban 192.168.1.100"
        ]
        
        alerts = detect_alerts(self.server_name, self.log_source, lines, self.now)
        self.assertEqual(len(alerts), 1)
        
        alert = alerts[0]
        self.assertEqual(alert.rule, "fail2ban_unban")
        self.assertEqual(alert.level, "info")
        self.assertEqual(alert.ip_address, "192.168.1.100")
    
    def test_sshd_failed_detection(self):
        """Test de la détection des échecs SSH"""
        lines = [
            "2024-01-15 10:30:45 sshd[12345]: Failed password for user from 192.168.1.100"
        ]
        
        alerts = detect_alerts(self.server_name, self.log_source, lines, self.now)
        self.assertEqual(len(alerts), 1)
        
        alert = alerts[0]
        self.assertEqual(alert.rule, "sshd_failed")
        self.assertEqual(alert.level, "medium")
        self.assertEqual(alert.ip_address, "192.168.1.100")
    
    def test_pam_auth_failure_detection(self):
        """Test de la détection des échecs d'authentification PAM"""
        lines = [
            "2024-01-15 10:30:45 pam_unix(sshd:auth): authentication failure"
        ]
        
        alerts = detect_alerts(self.server_name, self.log_source, lines, self.now)
        self.assertEqual(len(alerts), 1)
        
        alert = alerts[0]
        self.assertEqual(alert.rule, "pam_auth_failure")
        self.assertEqual(alert.level, "medium")
    
    def test_sshd_accepted_detection(self):
        """Test de la détection des connexions SSH acceptées"""
        lines = [
            "2024-01-15 10:30:45 sshd[12345]: Accepted password for admin from 192.168.1.100"
        ]
        
        alerts = detect_alerts(self.server_name, self.log_source, lines, self.now)
        self.assertEqual(len(alerts), 1)
        
        alert = alerts[0]
        self.assertEqual(alert.rule, "sshd_accepted")
        self.assertEqual(alert.level, "info")
        self.assertEqual(alert.ip_address, "192.168.1.100")
        self.assertEqual(alert.username, "admin")
    
    def test_breakin_attempt_detection(self):
        """Test de la détection des tentatives d'intrusion"""
        lines = [
            "2024-01-15 10:30:45 Possible break-in attempt detected from 192.168.1.100"
        ]
        
        alerts = detect_alerts(self.server_name, self.log_source, lines, self.now)
        self.assertEqual(len(alerts), 1)
        
        alert = alerts[0]
        self.assertEqual(alert.rule, "break_in_attempt")
        self.assertEqual(alert.level, "high")
        self.assertEqual(alert.ip_address, "192.168.1.100")
    
    def test_multiple_alerts_detection(self):
        """Test de la détection de multiples alertes"""
        lines = [
            "2024-01-15 10:30:45 sshd[12345]: Failed password for user from 192.168.1.100",
            "2024-01-15 10:31:00 fail2ban.actions: WARNING [sshd] Ban 192.168.1.100",
            "2024-01-15 10:32:00 sshd[67890]: Accepted password for admin from 10.0.0.50"
        ]
        
        alerts = detect_alerts(self.server_name, self.log_source, lines, self.now)
        self.assertEqual(len(alerts), 3)
        
        # Vérification des types d'alertes
        alert_rules = [alert.rule for alert in alerts]
        self.assertIn("sshd_failed", alert_rules)
        self.assertIn("fail2ban_ban", alert_rules)
        self.assertIn("sshd_accepted", alert_rules)
    
    def test_no_alerts_detection(self):
        """Test avec des lignes qui ne génèrent pas d'alertes"""
        lines = [
            "2024-01-15 10:30:45 systemd[1]: Started ssh.service",
            "2024-01-15 10:31:00 kernel: [12345.67890] CPU temperature above threshold"
        ]
        
        alerts = detect_alerts(self.server_name, self.log_source, lines, self.now)
        self.assertEqual(len(alerts), 0)
    
    def test_empty_lines(self):
        """Test avec des lignes vides"""
        lines = ["", "   ", "\n"]
        
        alerts = detect_alerts(self.server_name, self.log_source, lines, self.now)
        self.assertEqual(len(alerts), 0)
    
    def test_timestamp_parsing_in_alerts(self):
        """Test que les timestamps sont correctement parsés dans les alertes"""
        lines = [
            "Jan 15 10:30:45 test-host sshd[12345]: Failed password for user from 192.168.1.100"
        ]
        
        alerts = detect_alerts(self.server_name, self.log_source, lines, self.now)
        self.assertEqual(len(alerts), 1)
        
        alert = alerts[0]
        self.assertIsInstance(alert.timestamp, datetime)
        # Le timestamp devrait être de l'année courante (2024)
        self.assertEqual(alert.timestamp.year, 2024)


if __name__ == '__main__':
    unittest.main() 