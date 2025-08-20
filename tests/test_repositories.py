#!/usr/bin/env python3
"""
Tests unitaires pour les repositories SQLite
"""

import unittest
import tempfile
import os
import sqlite3
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from infrastructure.persistence.sqlite_repositories import (
    SQLiteAlertRepository,
    SQLiteStateRepository,
    SQLiteServerRepository,
    SQLiteAlertExceptionRepository
)
from domain.entities import Alert, Server, AlertException


class TestSQLiteAlertRepository(unittest.TestCase):
    """Tests pour SQLiteAlertRepository"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.repo = SQLiteAlertRepository(self.db_path)
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_database_creation(self):
        """Test de la création de la base de données"""
        self.assertTrue(os.path.exists(self.db_path))
        
        # Vérification de la structure de la table
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'")
        self.assertIsNotNone(cursor.fetchone())
        conn.close()
    
    def test_save_single_alert(self):
        """Test de la sauvegarde d'une seule alerte"""
        alert = Alert(
            server_name="test-server",
            log_source="test-log",
            rule="test_rule",
            level="high",
            message="Test alert message",
            ip_address="192.168.1.1",
            username="testuser"
        )
        
        saved_count = self.repo.save_alerts([alert])
        self.assertEqual(saved_count, 1)
        
        # Vérification de la sauvegarde
        alerts = self.repo.list_alerts()
        self.assertEqual(len(alerts), 1)
        saved_alert = alerts[0]
        self.assertEqual(saved_alert.server_name, "test-server")
        self.assertEqual(saved_alert.rule, "test_rule")
        self.assertEqual(saved_alert.level, "high")
        self.assertEqual(saved_alert.ip_address, "192.168.1.1")
        self.assertEqual(saved_alert.username, "testuser")
    
    def test_save_multiple_alerts(self):
        """Test de la sauvegarde de multiples alertes"""
        alerts = [
            Alert(server_name="server1", log_source="log1", rule="rule1", message="Alert 1"),
            Alert(server_name="server2", log_source="log2", rule="rule2", message="Alert 2"),
            Alert(server_name="server3", log_source="log3", rule="rule3", message="Alert 3")
        ]
        
        saved_count = self.repo.save_alerts(alerts)
        self.assertEqual(saved_count, 3)
        
        # Vérification de la sauvegarde
        saved_alerts = self.repo.list_alerts()
        self.assertEqual(len(saved_alerts), 3)
    
    def test_list_alerts_with_limit(self):
        """Test de la liste des alertes avec limite"""
        # Création de 5 alertes
        alerts = []
        for i in range(5):
            alert = Alert(
                server_name=f"server{i}",
                log_source=f"log{i}",
                rule=f"rule{i}",
                message=f"Alert {i}"
            )
            alerts.append(alert)
        
        self.repo.save_alerts(alerts)
        
        # Test avec limite
        limited_alerts = self.repo.list_alerts(limit=3)
        self.assertEqual(len(limited_alerts), 3)
    
    def test_list_alerts_with_since_filter(self):
        """Test de la liste des alertes avec filtre de date"""
        # Création d'alertes avec différents timestamps
        now = datetime.now(timezone.utc)
        old_time = now.replace(year=now.year - 1)
        
        old_alert = Alert(
            server_name="old-server",
            log_source="old-log",
            rule="old-rule",
            message="Old alert",
            timestamp=old_time
        )
        
        new_alert = Alert(
            server_name="new-server",
            log_source="new-log",
            rule="new-rule",
            message="New alert",
            timestamp=now
        )
        
        self.repo.save_alerts([old_alert, new_alert])
        
        # Test avec filtre de date
        recent_alerts = self.repo.list_alerts(since=now.replace(day=now.day - 1))
        self.assertEqual(len(recent_alerts), 1)
        self.assertEqual(recent_alerts[0].server_name, "new-server")
    
    def test_update_alert_acknowledgment(self):
        """Test de la mise à jour de l'acquittement d'une alerte"""
        alert = Alert(
            server_name="test-server",
            log_source="test-log",
            rule="test_rule",
            message="Test alert"
        )
        
        self.repo.save_alerts([alert])
        saved_alerts = self.repo.list_alerts()
        alert_id = saved_alerts[0].id
        
        # Mise à jour de l'acquittement
        ack_time = datetime.now(timezone.utc)
        success = self.repo.acknowledge_alert(alert_id, "admin", ack_time)
        self.assertTrue(success)
        
        # Vérification de la mise à jour
        updated_alerts = self.repo.list_alerts()
        updated_alert = next(a for a in updated_alerts if a.id == alert_id)
        self.assertTrue(updated_alert.acknowledged)
        self.assertEqual(updated_alert.acknowledged_by, "admin")
        self.assertEqual(updated_alert.acknowledged_at, ack_time)
    
    def test_delete_alert(self):
        """Test de la suppression d'une alerte"""
        alert = Alert(
            server_name="test-server",
            log_source="test-log",
            rule="test_rule",
            message="Test alert"
        )
        
        self.repo.save_alerts([alert])
        saved_alerts = self.repo.list_alerts()
        alert_id = saved_alerts[0].id
        
        # Suppression de l'alerte
        success = self.repo.delete_alert(alert_id)
        self.assertTrue(success)
        
        # Vérification de la suppression
        remaining_alerts = self.repo.list_alerts()
        self.assertEqual(len(remaining_alerts), 0)


class TestSQLiteStateRepository(unittest.TestCase):
    """Tests pour SQLiteStateRepository"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.repo = SQLiteStateRepository(self.db_path)
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_database_creation(self):
        """Test de la création de la base de données"""
        self.assertTrue(os.path.exists(self.db_path))
        
        # Vérification de la structure de la table
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='state'")
        self.assertIsNotNone(cursor.fetchone())
        conn.close()
    
    def test_set_and_get_timestamp(self):
        """Test de la définition et récupération d'un timestamp"""
        server_name = "test-server"
        log_identifier = "test-log"
        timestamp = "2024-01-15T10:30:45"
        
        # Définition du timestamp
        self.repo.set_last_seen_timestamp(server_name, log_identifier, timestamp)
        
        # Récupération du timestamp
        retrieved_timestamp = self.repo.get_last_seen_timestamp(server_name, log_identifier)
        self.assertEqual(retrieved_timestamp, timestamp)
    
    def test_get_nonexistent_timestamp(self):
        """Test de la récupération d'un timestamp inexistant"""
        timestamp = self.repo.get_last_seen_timestamp("nonexistent-server", "nonexistent-log")
        self.assertIsNone(timestamp)
    
    def test_update_existing_timestamp(self):
        """Test de la mise à jour d'un timestamp existant"""
        server_name = "test-server"
        log_identifier = "test-log"
        
        # Premier timestamp
        timestamp1 = "2024-01-15T10:30:45"
        self.repo.set_last_seen_timestamp(server_name, log_identifier, timestamp1)
        
        # Mise à jour avec un nouveau timestamp
        timestamp2 = "2024-01-15T11:00:00"
        self.repo.set_last_seen_timestamp(server_name, log_identifier, timestamp2)
        
        # Vérification de la mise à jour
        retrieved_timestamp = self.repo.get_last_seen_timestamp(server_name, log_identifier)
        self.assertEqual(retrieved_timestamp, timestamp2)


class TestSQLiteServerRepository(unittest.TestCase):
    """Tests pour SQLiteServerRepository"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.repo = SQLiteServerRepository(self.db_path)
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_database_creation(self):
        """Test de la création de la base de données"""
        self.assertTrue(os.path.exists(self.db_path))
        
        # Vérification de la structure de la table
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='servers'")
        self.assertIsNotNone(cursor.fetchone())
        conn.close()
    
    def test_save_and_get_server(self):
        """Test de la sauvegarde et récupération d'un serveur"""
        server = Server(
            name="test-server",
            host="192.168.1.100",
            port=22,
            username="admin",
            password="secret123",
            private_key_path="/path/to/key",
            logs=["/var/log/auth.log", "/var/log/syslog"]
        )
        
        # Sauvegarde du serveur
        self.repo.save_server(server)
        
        # Récupération du serveur
        saved_servers = self.repo.list_servers()
        self.assertEqual(len(saved_servers), 1)
        
        saved_server = saved_servers[0]
        self.assertEqual(saved_server.name, "test-server")
        self.assertEqual(saved_server.host, "192.168.1.100")
        self.assertEqual(saved_server.port, 22)
        self.assertEqual(saved_server.username, "admin")
        self.assertEqual(saved_server.password, "secret123")
        self.assertEqual(saved_server.private_key_path, "/path/to/key")
        self.assertEqual(saved_server.logs, ["/var/log/auth.log", "/var/log/syslog"])
    
    def test_update_server(self):
        """Test de la mise à jour d'un serveur"""
        server = Server(
            name="test-server",
            host="192.168.1.100",
            username="admin"
        )
        
        # Sauvegarde initiale
        self.repo.save_server(server)
        saved_servers = self.repo.list_servers()
        server_id = saved_servers[0].id
        
        # Mise à jour du serveur
        updated_server = Server(
            id=server_id,
            name="test-server",
            host="192.168.1.101",  # IP modifiée
            username="admin",
            port=2222  # Port modifié
        )
        
        self.repo.save_server(updated_server)
        
        # Vérification de la mise à jour
        updated_servers = self.repo.list_servers()
        self.assertEqual(len(updated_servers), 1)
        updated = updated_servers[0]
        self.assertEqual(updated.host, "192.168.1.101")
        self.assertEqual(updated.port, 2222)
    
    def test_delete_server(self):
        """Test de la suppression d'un serveur"""
        server = Server(
            name="test-server",
            host="192.168.1.100",
            username="admin"
        )
        
        # Sauvegarde du serveur
        self.repo.save_server(server)
        saved_servers = self.repo.list_servers()
        server_id = saved_servers[0].id
        
        # Suppression du serveur
        success = self.repo.delete_server(server_id)
        self.assertTrue(success)
        
        # Vérification de la suppression
        remaining_servers = self.repo.list_servers()
        self.assertEqual(len(remaining_servers), 0)
    
    def test_get_server_by_id(self):
        """Test de la récupération d'un serveur par ID"""
        server = Server(
            name="test-server",
            host="192.168.1.100",
            username="admin"
        )
        
        # Sauvegarde du serveur
        self.repo.save_server(server)
        saved_servers = self.repo.list_servers()
        server_id = saved_servers[0].id
        
        # Récupération par ID
        retrieved_server = self.repo.get_server(server_id)
        self.assertIsNotNone(retrieved_server)
        self.assertEqual(retrieved_server.name, "test-server")
        self.assertEqual(retrieved_server.host, "192.168.1.100")
    
    def test_get_nonexistent_server(self):
        """Test de la récupération d'un serveur inexistant"""
        server = self.repo.get_server(99999)
        self.assertIsNone(server)


class TestSQLiteAlertExceptionRepository(unittest.TestCase):
    """Tests pour SQLiteAlertExceptionRepository"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.repo = SQLiteAlertExceptionRepository(self.db_path)
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_database_creation(self):
        """Test de la création de la base de données"""
        self.assertTrue(os.path.exists(self.db_path))
        
        # Vérification de la structure de la table
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alert_exceptions'")
        self.assertIsNotNone(cursor.fetchone())
        conn.close()
    
    def test_save_and_get_exception(self):
        """Test de la sauvegarde et récupération d'une exception"""
        exception = AlertException(
            rule_type="ip",
            value="192.168.1.1",
            description="Test exception for IP",
            enabled=True
        )
        
        # Sauvegarde de l'exception
        self.repo.save_exception(exception)
        
        # Récupération de l'exception
        saved_exceptions = self.repo.list_exceptions()
        self.assertEqual(len(saved_exceptions), 1)
        
        saved_exception = saved_exceptions[0]
        self.assertEqual(saved_exception.rule_type, "ip")
        self.assertEqual(saved_exception.value, "192.168.1.1")
        self.assertEqual(saved_exception.description, "Test exception for IP")
        self.assertTrue(saved_exception.enabled)
    
    def test_is_alert_excepted(self):
        """Test de la vérification si une alerte est exceptée"""
        # Création d'une exception pour une IP
        exception = AlertException(
            rule_type="ip",
            value="192.168.1.1",
            description="Test exception for IP",
            enabled=True
        )
        
        self.repo.save_exception(exception)
        
        # Création d'une alerte avec cette IP
        alert = Alert(
            server_name="test-server",
            log_source="test-log",
            rule="test_rule",
            message="Test alert",
            ip_address="192.168.1.1"
        )
        
        # Vérification que l'alerte est exceptée
        is_excepted = self.repo.is_alert_excepted(alert)
        self.assertTrue(is_excepted)
    
    def test_is_alert_not_excepted(self):
        """Test de la vérification qu'une alerte n'est pas exceptée"""
        # Création d'une alerte sans exception
        alert = Alert(
            server_name="test-server",
            log_source="test-log",
            rule="test_rule",
            message="Test alert",
            ip_address="192.168.1.2"
        )
        
        # Vérification que l'alerte n'est pas exceptée
        is_excepted = self.repo.is_alert_excepted(alert)
        self.assertFalse(is_excepted)
    
    def test_exception_disabled(self):
        """Test d'une exception désactivée"""
        # Création d'une exception désactivée
        exception = AlertException(
            rule_type="ip",
            value="192.168.1.1",
            description="Test exception for IP",
            enabled=False
        )
        
        self.repo.save_exception(exception)
        
        # Création d'une alerte avec cette IP
        alert = Alert(
            server_name="test-server",
            log_source="test-log",
            rule="test_rule",
            message="Test alert",
            ip_address="192.168.1.1"
        )
        
        # Vérification que l'alerte n'est pas exceptée (exception désactivée)
        is_excepted = self.repo.is_alert_excepted(alert)
        self.assertFalse(is_excepted)


if __name__ == '__main__':
    unittest.main() 