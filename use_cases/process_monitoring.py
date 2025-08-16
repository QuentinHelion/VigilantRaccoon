from __future__ import annotations

import re
import subprocess
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from domain.entities import Alert


@dataclass
class ProcessInfo:
    pid: int
    name: str
    user: str
    command: str
    cpu_percent: float
    memory_percent: float
    connections: List[Tuple[str, int, str, int, str]]  # (src_ip, src_port, dst_ip, dst_port, status)


class ProcessMonitor:
    """Moniteur de processus pour détecter les comportements suspects"""
    
    def __init__(self):
        self.suspicious_patterns = {
            'reverse_shell': re.compile(r'(?:nc|netcat|bash\s+-i|python\s+-c\s+.*import\s+socket)', re.IGNORECASE),
            'download_tools': re.compile(r'(?:wget|curl|ftp|scp)\s+.*http', re.IGNORECASE),
            'privilege_escalation': re.compile(r'(?:sudo|su|doas)\s+.*(?:bash|sh|python|perl)', re.IGNORECASE),
            'file_manipulation': re.compile(r'(?:chmod|chown)\s+.*[0-7]{3,4}', re.IGNORECASE),
            'network_tools': re.compile(r'(?:nmap|masscan|hydra|john)', re.IGNORECASE),
            'crypto_mining': re.compile(r'(?:xmr|monero|bitcoin|mining)', re.IGNORECASE),
        }
        
        self.whitelist_commands = {
            'sshd', 'systemd', 'cron', 'rsyslogd', 'ntpd', 'snmpd',
            'apache2', 'nginx', 'mysql', 'postgresql', 'redis-server'
        }
        
        self.suspicious_ports = {22, 23, 3389, 5900, 5901, 8080, 8443, 9000}
    
    def get_active_processes(self, server_name: str) -> List[ProcessInfo]:
        """Récupère la liste des processus actifs"""
        try:
            # Utilise ps pour obtenir les informations des processus
            result = subprocess.run([
                'ps', 'aux', '--no-headers'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return []
            
            processes = []
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                    
                parts = line.split(None, 10)
                if len(parts) < 11:
                    continue
                    
                try:
                    user = parts[0]
                    pid = int(parts[1])
                    cpu = float(parts[2])
                    mem = float(parts[2])
                    command = parts[10]
                    
                    # Ignore les processus système et whitelist
                    if user in ['root', 'systemd'] or any(cmd in command for cmd in self.whitelist_commands):
                        continue
                    
                    processes.append(ProcessInfo(
                        pid=pid,
                        name=parts[10].split()[0] if parts[10] else 'unknown',
                        user=user,
                        command=command,
                        cpu_percent=cpu,
                        memory_percent=mem,
                        connections=[]
                    ))
                except (ValueError, IndexError):
                    continue
            
            return processes
        except Exception as e:
            print(f"Erreur lors de la récupération des processus: {e}")
            return []
    
    def get_network_connections(self, pid: int) -> List[Tuple[str, int, str, int, str]]:
        """Récupère les connexions réseau d'un processus"""
        try:
            result = subprocess.run([
                'netstat', '-tulpn', '--numeric-ports'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return []
            
            connections = []
            for line in result.stdout.strip().split('\n'):
                if str(pid) in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        local_addr, local_port = parts[3].rsplit(':', 1)
                        remote_addr, remote_port = parts[4].rsplit(':', 1) if ':' in parts[4] else ('*', '*')
                        status = parts[5] if len(parts) > 5 else 'UNKNOWN'
                        
                        try:
                            local_port = int(local_port)
                            remote_port = int(remote_port) if remote_port != '*' else 0
                            connections.append((local_addr, local_port, remote_addr, remote_port, status))
                        except ValueError:
                            continue
            
            return connections
        except Exception as e:
            print(f"Erreur lors de la récupération des connexions pour PID {pid}: {e}")
            return []
    
    def analyze_process_behavior(self, process: ProcessInfo) -> List[Alert]:
        """Analyse le comportement d'un processus pour détecter des activités suspectes"""
        alerts = []
        
        # Vérification des patterns suspects dans la commande
        for pattern_name, pattern in self.suspicious_patterns.items():
            if pattern.search(process.command):
                alerts.append(Alert(
                    server_name="localhost",  # Sera remplacé par le vrai nom du serveur
                    log_source="process_monitoring",
                    rule=f"suspicious_{pattern_name}",
                    level="high",
                    message=f"Processus suspect détecté: {process.user} (PID {process.pid}) - {process.command}",
                    username=process.user,
                    timestamp=datetime.utcnow()
                ))
        
        # Vérification des connexions réseau suspectes
        for local_addr, local_port, remote_addr, remote_port, status in process.connections:
            if remote_port in self.suspicious_ports:
                alerts.append(Alert(
                    server_name="localhost",
                    log_source="process_monitoring",
                    rule="suspicious_network_connection",
                    level="medium",
                    message=f"Connexion réseau suspecte: {process.user} (PID {process.pid}) -> {remote_addr}:{remote_port}",
                    username=process.user,
                    timestamp=datetime.utcnow()
                ))
        
        # Vérification de l'utilisation excessive des ressources
        if process.cpu_percent > 80 or process.memory_percent > 80:
            alerts.append(Alert(
                server_name="localhost",
                log_source="process_monitoring",
                rule="high_resource_usage",
                level="medium",
                message=f"Utilisation élevée des ressources: {process.user} (PID {process.pid}) - CPU: {process.cpu_percent}%, RAM: {process.memory_percent}%",
                username=process.user,
                timestamp=datetime.utcnow()
            ))
        
        return alerts
    
    def monitor_processes(self, server_name: str) -> List[Alert]:
        """Surveille tous les processus et génère des alertes"""
        alerts = []
        
        # Récupère les processus actifs
        processes = self.get_active_processes(server_name)
        
        for process in processes:
            # Récupère les connexions réseau
            process.connections = self.get_network_connections(process.pid)
            
            # Analyse le comportement
            process_alerts = self.analyze_process_behavior(process)
            alerts.extend(process_alerts)
        
        return alerts
    
    def check_file_activity(self, server_name: str) -> List[Alert]:
        """Vérifie l'activité des fichiers suspects"""
        alerts = []
        
        suspicious_locations = [
            '/tmp',
            '/var/tmp', 
            '/dev/shm',
            '/home/*/.cache',
            '/var/log'
        ]
        
        try:
            for location in suspicious_locations:
                if location == '/home/*/.cache':
                    # Vérification spéciale pour les caches utilisateur
                    result = subprocess.run([
                        'find', '/home', '-name', '.cache', '-type', 'd', '-exec', 'ls', '-la', '{}', ';'
                    ], capture_output=True, text=True, timeout=30)
                else:
                    result = subprocess.run([
                        'ls', '-la', location
                    ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if any(ext in line.lower() for ext in ['.sh', '.py', '.pl', '.rb', '.js', '.php', '.exe', '.bat']):
                            if 'root' in line or '777' in line or '666' in line:
                                alerts.append(Alert(
                                    server_name=server_name,
                                    log_source="file_monitoring",
                                    rule="suspicious_file_permissions",
                                    level="high",
                                    message=f"Fichier suspect avec permissions dangereuses: {line.strip()}",
                                    timestamp=datetime.utcnow()
                                ))
        except Exception as e:
            print(f"Erreur lors de la vérification des fichiers: {e}")
        
        return alerts


def run_process_monitoring(server_name: str) -> List[Alert]:
    """Fonction principale pour exécuter la surveillance des processus"""
    monitor = ProcessMonitor()
    
    # Surveillance des processus
    process_alerts = monitor.monitor_processes(server_name)
    
    # Surveillance des fichiers
    file_alerts = monitor.check_file_activity(server_name)
    
    return process_alerts + file_alerts 