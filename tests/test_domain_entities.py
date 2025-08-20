#!/usr/bin/env python3
"""
Tests unitaires pour les entités du domaine
"""

import unittest
from datetime import datetime, timezone
from domain.entities import Alert, Server, AlertException


class TestAlert(unittest.TestCase):
    """Tests pour la classe Alert"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.test_timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.alert = Alert(
            server_name="test-server",
            log_source="test-log",
            rule="test_rule",
            level="medium",
            message="Test alert message",
            ip_address="192.168.1.1",
            username="testuser",
            timestamp=self.test_timestamp
        )
    
    def test_alert_creation(self):
        """Test de création d'une alerte"""
        self.assertEqual(self.alert.server_name, "test-server")
        self.assertEqual(self.alert.log_source, "test-log")
        self.assertEqual(self.alert.rule, "test_rule")
        self.assertEqual(self.alert.level, "medium")
        self.assertEqual(self.alert.message, "Test alert message")
        self.assertEqual(self.alert.ip_address, "192.168.1.1")
        self.assertEqual(self.alert.username, "testuser")
        self.assertEqual(self.alert.timestamp, self.test_timestamp)
        self.assertFalse(self.alert.acknowledged)
        self.assertIsNone(self.alert.acknowledged_at)
        self.assertIsNone(self.alert.acknowledged_by)
    
    def test_alert_default_values(self):
        """Test des valeurs par défaut d'une alerte"""
        alert = Alert(
            server_name="test-server",
            log_source="test-log",
            rule="test_rule"
        )
        self.assertEqual(alert.level, "medium")
        self.assertEqual(alert.message, "")
        self.assertIsNone(alert.ip_address)
        self.assertIsNone(alert.username)
        self.assertFalse(alert.acknowledged)
        self.assertIsInstance(alert.timestamp, datetime)
    
    def test_alert_acknowledgment(self):
        """Test de l'acquittement d'une alerte"""
        ack_time = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        self.alert.acknowledged = True
        self.alert.acknowledged_at = ack_time
        self.alert.acknowledged_by = "admin"
        
        self.assertTrue(self.alert.acknowledged)
        self.assertEqual(self.alert.acknowledged_at, ack_time)
        self.assertEqual(self.alert.acknowledged_by, "admin")
    
    def test_alert_string_representation(self):
        """Test de la représentation en chaîne d'une alerte"""
        alert_str = str(self.alert)
        self.assertIn("test-server", alert_str)
        self.assertIn("test_rule", alert_str)
        self.assertIn("medium", alert_str)


class TestServer(unittest.TestCase):
    """Tests pour la classe Server"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.server = Server(
            name="test-server",
            host="192.168.1.100",
            port=22,
            username="admin",
            password="secret123",
            private_key_path="/path/to/key",
            logs=["/var/log/auth.log", "/var/log/syslog"]
        )
    
    def test_server_creation(self):
        """Test de création d'un serveur"""
        self.assertEqual(self.server.name, "test-server")
        self.assertEqual(self.server.host, "192.168.1.100")
        self.assertEqual(self.server.port, 22)
        self.assertEqual(self.server.username, "admin")
        self.assertEqual(self.server.password, "secret123")
        self.assertEqual(self.server.private_key_path, "/path/to/key")
        self.assertEqual(self.server.logs, ["/var/log/auth.log", "/var/log/syslog"])
    
    def test_server_default_values(self):
        """Test des valeurs par défaut d'un serveur"""
        server = Server(
            name="test-server",
            host="192.168.1.100",
            username="admin"
        )
        self.assertEqual(server.port, 22)
        self.assertIsNone(server.password)
        self.assertIsNone(server.private_key_path)
        self.assertEqual(server.logs, [])
    
    def test_server_string_representation(self):
        """Test de la représentation en chaîne d'un serveur"""
        server_str = str(self.server)
        self.assertIn("test-server", server_str)
        self.assertIn("192.168.1.100", server_str)
        self.assertIn("admin", server_str)


class TestAlertException(unittest.TestCase):
    """Tests pour la classe AlertException"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.exception = AlertException(
            rule_type="ip",
            value="192.168.1.1",
            description="Test exception for IP",
            enabled=True
        )
    
    def test_exception_creation(self):
        """Test de création d'une exception d'alerte"""
        self.assertEqual(self.exception.rule_type, "ip")
        self.assertEqual(self.exception.value, "192.168.1.1")
        self.assertEqual(self.exception.description, "Test exception for IP")
        self.assertTrue(self.exception.enabled)
        self.assertIsInstance(self.exception.created_at, datetime)
        self.assertIsNone(self.exception.updated_at)
    
    def test_exception_default_values(self):
        """Test des valeurs par défaut d'une exception"""
        exception = AlertException(
            rule_type="username",
            value="testuser"
        )
        self.assertEqual(exception.description, "")
        self.assertTrue(exception.enabled)
        self.assertIsInstance(exception.created_at, datetime)
        self.assertIsNone(exception.updated_at)
    
    def test_exception_update(self):
        """Test de la mise à jour d'une exception"""
        update_time = datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc)
        self.exception.enabled = False
        self.exception.updated_at = update_time
        
        self.assertFalse(self.exception.enabled)
        self.assertEqual(self.exception.updated_at, update_time)
    
    def test_exception_string_representation(self):
        """Test de la représentation en chaîne d'une exception"""
        exception_str = str(self.exception)
        self.assertIn("ip", exception_str)
        self.assertIn("192.168.1.1", exception_str)


if __name__ == '__main__':
    unittest.main() 