#!/usr/bin/env python3
"""
Tests unitaires pour la configuration
"""

import unittest
import tempfile
import os
import yaml
from unittest.mock import patch, mock_open
from config import (
    AppConfig, ServerConfig, EmailConfig, StorageConfig,
    CollectionConfig, WebConfig, LoggingConfig, load_config
)


class TestServerConfig(unittest.TestCase):
    """Tests pour la classe ServerConfig"""
    
    def test_server_config_creation(self):
        """Test de création d'une configuration de serveur"""
        config = ServerConfig(
            name="test-server",
            host="192.168.1.100",
            port=22,
            username="admin",
            password="secret123",
            private_key_path="/path/to/key",
            logs=["/var/log/auth.log", "/var/log/syslog"]
        )
        
        self.assertEqual(config.name, "test-server")
        self.assertEqual(config.host, "192.168.1.100")
        self.assertEqual(config.port, 22)
        self.assertEqual(config.username, "admin")
        self.assertEqual(config.password, "secret123")
        self.assertEqual(config.private_key_path, "/path/to/key")
        self.assertEqual(config.logs, ["/var/log/auth.log", "/var/log/syslog"])
    
    def test_server_config_defaults(self):
        """Test des valeurs par défaut d'une configuration de serveur"""
        config = ServerConfig(
            name="test-server",
            host="192.168.1.100",
            username="admin"
        )
        
        self.assertEqual(config.port, 22)
        self.assertIsNone(config.password)
        self.assertIsNone(config.private_key_path)
        self.assertEqual(config.logs, [])


class TestEmailConfig(unittest.TestCase):
    """Tests pour la classe EmailConfig"""
    
    def test_email_config_creation(self):
        """Test de création d'une configuration email"""
        config = EmailConfig(
            enabled=True,
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            username="user@gmail.com",
            password="secret123",
            from_addr="noreply@example.com",
            to_addrs=["admin@example.com", "security@example.com"]
        )
        
        self.assertTrue(config.enabled)
        self.assertEqual(config.smtp_host, "smtp.gmail.com")
        self.assertEqual(config.smtp_port, 587)
        self.assertTrue(config.use_tls)
        self.assertEqual(config.username, "user@gmail.com")
        self.assertEqual(config.password, "secret123")
        self.assertEqual(config.from_addr, "noreply@example.com")
        self.assertEqual(config.to_addrs, ["admin@example.com", "security@example.com"])
    
    def test_email_config_defaults(self):
        """Test des valeurs par défaut d'une configuration email"""
        config = EmailConfig()
        
        self.assertFalse(config.enabled)
        self.assertEqual(config.smtp_host, "")
        self.assertEqual(config.smtp_port, 587)
        self.assertTrue(config.use_tls)
        self.assertIsNone(config.username)
        self.assertIsNone(config.password)
        self.assertIsNone(config.from_addr)
        self.assertEqual(config.to_addrs, [])


class TestStorageConfig(unittest.TestCase):
    """Tests pour la classe StorageConfig"""
    
    def test_storage_config_creation(self):
        """Test de création d'une configuration de stockage"""
        config = StorageConfig(sqlite_path="./custom/data.db")
        
        self.assertEqual(config.sqlite_path, "./custom/data.db")
    
    def test_storage_config_defaults(self):
        """Test des valeurs par défaut d'une configuration de stockage"""
        config = StorageConfig()
        
        self.assertEqual(config.sqlite_path, "./data/vigilant_raccoon.db")


class TestCollectionConfig(unittest.TestCase):
    """Tests pour la classe CollectionConfig"""
    
    def test_collection_config_creation(self):
        """Test de création d'une configuration de collecte"""
        config = CollectionConfig(
            tail_lines=5000,
            ignore_source_ips=["192.168.1.1", "10.0.0.1"]
        )
        
        self.assertEqual(config.tail_lines, 5000)
        self.assertEqual(config.ignore_source_ips, ["192.168.1.1", "10.0.0.1"])
    
    def test_collection_config_defaults(self):
        """Test des valeurs par défaut d'une configuration de collecte"""
        config = CollectionConfig()
        
        self.assertEqual(config.tail_lines, 2000)
        self.assertEqual(config.ignore_source_ips, [])


class TestWebConfig(unittest.TestCase):
    """Tests pour la classe WebConfig"""
    
    def test_web_config_creation(self):
        """Test de création d'une configuration web"""
        config = WebConfig(host="0.0.0.0", port=9000)
        
        self.assertEqual(config.host, "0.0.0.0")
        self.assertEqual(config.port, 9000)
    
    def test_web_config_defaults(self):
        """Test des valeurs par défaut d'une configuration web"""
        config = WebConfig()
        
        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 8000)


class TestLoggingConfig(unittest.TestCase):
    """Tests pour la classe LoggingConfig"""
    
    def test_logging_config_creation(self):
        """Test de création d'une configuration de logging"""
        config = LoggingConfig(
            level="DEBUG",
            file_path="./custom/app.log",
            max_bytes=2_000_000,
            backup_count=5,
            console=False
        )
        
        self.assertEqual(config.level, "DEBUG")
        self.assertEqual(config.file_path, "./custom/app.log")
        self.assertEqual(config.max_bytes, 2_000_000)
        self.assertEqual(config.backup_count, 5)
        self.assertFalse(config.console)
    
    def test_logging_config_defaults(self):
        """Test des valeurs par défaut d'une configuration de logging"""
        config = LoggingConfig()
        
        self.assertEqual(config.level, "INFO")
        self.assertEqual(config.file_path, "./logs/app.log")
        self.assertEqual(config.max_bytes, 1_000_000)
        self.assertEqual(config.backup_count, 3)
        self.assertTrue(config.console)


class TestAppConfig(unittest.TestCase):
    """Tests pour la classe AppConfig"""
    
    def test_app_config_creation(self):
        """Test de création d'une configuration d'application"""
        servers = [
            ServerConfig(name="server1", host="192.168.1.100", username="admin"),
            ServerConfig(name="server2", host="192.168.1.101", username="admin")
        ]
        
        email = EmailConfig(enabled=True, smtp_host="smtp.gmail.com")
        storage = StorageConfig(sqlite_path="./custom/data.db")
        collection = CollectionConfig(tail_lines=5000)
        web = WebConfig(host="0.0.0.0", port=9000)
        logging_cfg = LoggingConfig(level="DEBUG")
        
        config = AppConfig(
            servers=servers,
            poll_interval_seconds=120,
            email=email,
            storage=storage,
            collection=collection,
            web=web,
            logging=logging_cfg
        )
        
        self.assertEqual(len(config.servers), 2)
        self.assertEqual(config.poll_interval_seconds, 120)
        self.assertTrue(config.email.enabled)
        self.assertEqual(config.storage.sqlite_path, "./custom/data.db")
        self.assertEqual(config.collection.tail_lines, 5000)
        self.assertEqual(config.web.host, "0.0.0.0")
        self.assertEqual(config.logging.level, "DEBUG")
    
    def test_app_config_defaults(self):
        """Test des valeurs par défaut d'une configuration d'application"""
        servers = [ServerConfig(name="server1", host="192.168.1.100", username="admin")]
        
        config = AppConfig(servers=servers)
        
        self.assertEqual(config.poll_interval_seconds, 60)
        self.assertFalse(config.email.enabled)
        self.assertEqual(config.storage.sqlite_path, "./data/vigilant_raccoon.db")
        self.assertEqual(config.collection.tail_lines, 2000)
        self.assertEqual(config.web.host, "127.0.0.1")
        self.assertEqual(config.web.port, 8000)
        self.assertEqual(config.logging.level, "INFO")


class TestLoadConfig(unittest.TestCase):
    """Tests pour la fonction load_config"""
    
    def test_load_config_with_valid_yaml(self):
        """Test du chargement d'une configuration YAML valide"""
        yaml_content = """
        servers:
          - name: test-server
            host: 192.168.1.100
            username: admin
            logs:
              - /var/log/auth.log
              - /var/log/syslog
        
        poll_interval_seconds: 120
        
        email:
          enabled: true
          smtp_host: smtp.gmail.com
          smtp_port: 587
          username: user@gmail.com
          password: secret123
          from_addr: noreply@example.com
          to_addrs:
            - admin@example.com
        
        storage:
          sqlite_path: ./custom/data.db
        
        collection:
          tail_lines: 5000
          ignore_source_ips:
            - 192.168.1.1
        
        web:
          host: 0.0.0.0
          port: 9000
        
        logging:
          level: DEBUG
          file_path: ./custom/app.log
          max_bytes: 2000000
          backup_count: 5
          console: false
        """
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            config = load_config("config.yaml")
        
        # Vérification des serveurs
        self.assertEqual(len(config.servers), 1)
        server = config.servers[0]
        self.assertEqual(server.name, "test-server")
        self.assertEqual(server.host, "192.168.1.100")
        self.assertEqual(server.username, "admin")
        self.assertEqual(server.logs, ["/var/log/auth.log", "/var/log/syslog"])
        
        # Vérification des autres paramètres
        self.assertEqual(config.poll_interval_seconds, 120)
        self.assertTrue(config.email.enabled)
        self.assertEqual(config.email.smtp_host, "smtp.gmail.com")
        self.assertEqual(config.storage.sqlite_path, "./custom/data.db")
        self.assertEqual(config.collection.tail_lines, 5000)
        self.assertEqual(config.web.host, "0.0.0.0")
        self.assertEqual(config.web.port, 9000)
        self.assertEqual(config.logging.level, "DEBUG")
    
    def test_load_config_with_empty_yaml(self):
        """Test du chargement d'une configuration YAML vide"""
        with patch('builtins.open', mock_open(read_data="")):
            config = load_config("config.yaml")
        
        # Vérification des valeurs par défaut
        self.assertEqual(len(config.servers), 0)
        self.assertEqual(config.poll_interval_seconds, 60)
        self.assertFalse(config.email.enabled)
        self.assertEqual(config.storage.sqlite_path, "./data/vigilant_raccoon.db")
    
    def test_load_config_with_none_yaml(self):
        """Test du chargement d'une configuration YAML None"""
        with patch('builtins.open', mock_open(read_data="null")):
            config = load_config("config.yaml")
        
        # Vérification des valeurs par défaut
        self.assertEqual(len(config.servers), 0)
        self.assertEqual(config.poll_interval_seconds, 60)
    
    def test_load_config_with_partial_yaml(self):
        """Test du chargement d'une configuration YAML partielle"""
        yaml_content = """
        servers:
          - name: test-server
            host: 192.168.1.100
            username: admin
        
        email:
          enabled: true
          smtp_host: smtp.gmail.com
        """
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            config = load_config("config.yaml")
        
        # Vérification des valeurs définies
        self.assertEqual(len(config.servers), 1)
        self.assertTrue(config.email.enabled)
        self.assertEqual(config.email.smtp_host, "smtp.gmail.com")
        
        # Vérification des valeurs par défaut
        self.assertEqual(config.poll_interval_seconds, 60)
        self.assertEqual(config.storage.sqlite_path, "./data/vigilant_raccoon.db")
        self.assertEqual(config.web.host, "127.0.0.1")
        self.assertEqual(config.logging.level, "INFO")
    
    def test_load_config_with_invalid_yaml(self):
        """Test du chargement d'une configuration YAML invalide"""
        invalid_yaml = """
        servers:
          - name: test-server
            host: 192.168.1.100
            username: admin
            invalid_field: value
        """
        
        with patch('builtins.open', mock_open(read_data=invalid_yaml)):
            config = load_config("config.yaml")
        
        # La configuration devrait être chargée malgré les champs invalides
        self.assertEqual(len(config.servers), 1)
        server = config.servers[0]
        self.assertEqual(server.name, "test-server")
        self.assertEqual(server.host, "192.168.1.100")
        self.assertEqual(server.username, "admin")


if __name__ == '__main__':
    unittest.main() 