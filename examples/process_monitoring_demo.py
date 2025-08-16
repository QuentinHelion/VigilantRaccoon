#!/usr/bin/env python3
"""
Démonstration du module de surveillance des processus
"""

import sys
import os
import time
import subprocess
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from use_cases.process_monitoring import ProcessMonitor, run_process_monitoring
from domain.entities import Alert
import logging
import re

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def demo_basic_monitoring():
    """Démonstration de base de la surveillance des processus"""
    print("🔍 Démonstration de base de la surveillance des processus")
    print("=" * 60)
    
    try:
        # Création du moniteur
        monitor = ProcessMonitor()
        
        # Récupération des processus actifs
        print("📋 Récupération des processus actifs...")
        processes = monitor.get_active_processes("demo-server")
        print(f"✅ {len(processes)} processus récupérés")
        
        # Affichage des premiers processus
        print("\n📊 Aperçu des processus surveillés:")
        for i, process in enumerate(processes[:10], 1):
            print(f"   {i:2d}. {process.user:12s} - {process.name:20s} (PID: {process.pid:6d})")
        
        # Analyse d'un processus spécifique
        if processes:
            print(f"\n🔍 Analyse du processus {processes[0].name} (PID: {processes[0].pid})...")
            alerts = monitor.analyze_process_behavior(processes[0])
            print(f"✅ {len(alerts)} alertes générées")
            
            for alert in alerts:
                print(f"   🚨 {alert.rule}: {alert.message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def demo_network_monitoring():
    """Démonstration de la surveillance réseau"""
    print("\n🌐 Démonstration de la surveillance réseau")
    print("=" * 60)
    
    try:
        monitor = ProcessMonitor()
        
        # Récupération des connexions réseau
        print("📡 Récupération des connexions réseau...")
        connections = monitor.get_network_connections(1)  # PID 1 (systemd)
        print(f"✅ {len(connections)} connexions réseau trouvées")
        
        # Affichage des connexions
        if connections:
            print("\n📊 Connexions réseau actives:")
            for i, (local_addr, local_port, remote_addr, remote_port, status) in enumerate(connections[:10], 1):
                print(f"   {i:2d}. {local_addr:15s}:{local_port:5d} -> {remote_addr:15s}:{remote_port:5d} ({status})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def demo_file_monitoring():
    """Démonstration de la surveillance des fichiers"""
    print("\n📁 Démonstration de la surveillance des fichiers")
    print("=" * 60)
    
    try:
        monitor = ProcessMonitor()
        
        # Vérification des fichiers suspects
        print("🔍 Vérification des fichiers suspects...")
        alerts = monitor.check_file_activity("demo-server")
        print(f"✅ {len(alerts)} alertes de fichiers générées")
        
        # Affichage des alertes
        if alerts:
            print("\n🚨 Alertes de fichiers:")
            for alert in alerts:
                print(f"   • {alert.rule}: {alert.message}")
        else:
            print("✅ Aucun fichier suspect détecté")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def demo_full_monitoring():
    """Démonstration complète de la surveillance"""
    print("\n🚀 Démonstration complète de la surveillance")
    print("=" * 60)
    
    try:
        print("🔄 Exécution de la surveillance complète...")
        start_time = time.time()
        
        alerts = run_process_monitoring("demo-server")
        
        elapsed_time = time.time() - start_time
        print(f"✅ Surveillance terminée en {elapsed_time:.2f} secondes")
        print(f"📊 {len(alerts)} alertes générées")
        
        # Groupement des alertes par type
        alert_types = {}
        for alert in alerts:
            alert_types[alert.rule] = alert_types.get(alert.rule, 0) + 1
        
        print("\n📈 Répartition des alertes par type:")
        for alert_type, count in sorted(alert_types.items()):
            print(f"   • {alert_type}: {count} alerte(s)")
        
        # Affichage des alertes les plus critiques
        high_alerts = [a for a in alerts if a.level == "high"]
        if high_alerts:
            print(f"\n🚨 Alertes critiques (niveau HIGH): {len(high_alerts)}")
            for alert in high_alerts[:5]:  # Limite à 5 pour éviter le spam
                print(f"   • {alert.rule}: {alert.message[:80]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def demo_custom_patterns():
    """Démonstration des patterns personnalisés"""
    print("\n🎯 Démonstration des patterns personnalisés")
    print("=" * 60)
    
    try:
        # Création d'un moniteur avec des patterns personnalisés
        monitor = ProcessMonitor()
        
        # Ajout de patterns personnalisés
        custom_patterns = {
            'custom_test': re.compile(r'test_pattern', re.IGNORECASE),
            'suspicious_activity': re.compile(r'suspicious', re.IGNORECASE)
        }
        
        print("🔧 Patterns personnalisés ajoutés:")
        for pattern_name, pattern in custom_patterns.items():
            print(f"   • {pattern_name}: {pattern.pattern}")
        
        # Test avec un processus fictif
        from dataclasses import dataclass
        
        @dataclass
        class TestProcess:
            pid: int
            name: str
            user: str
            command: str
            cpu_percent: float
            memory_percent: float
            connections: list
        
        test_process = TestProcess(
            pid=99999,
            name="test_process",
            user="test_user",
            command="test_pattern suspicious activity",
            cpu_percent=50.0,
            memory_percent=30.0,
            connections=[]
        )
        
        print(f"\n🧪 Test avec un processus fictif: {test_process.command}")
        
        # Analyse du comportement
        alerts = monitor.analyze_process_behavior(test_process)
        print(f"✅ {len(alerts)} alertes générées pour le processus de test")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def demo_performance_monitoring():
    """Démonstration de la surveillance des performances"""
    print("\n⚡ Démonstration de la surveillance des performances")
    print("=" * 60)
    
    try:
        monitor = ProcessMonitor()
        
        # Récupération des processus avec utilisation des ressources
        print("📊 Récupération des processus avec utilisation des ressources...")
        processes = monitor.get_active_processes("demo-server")
        
        # Tri par utilisation CPU
        high_cpu_processes = sorted(processes, key=lambda p: p.cpu_percent, reverse=True)[:5]
        
        print("\n🔥 Top 5 des processus par utilisation CPU:")
        for i, process in enumerate(high_cpu_processes, 1):
            print(f"   {i}. {process.user:12s} - {process.name:20s} - CPU: {process.cpu_percent:5.1f}%")
        
        # Tri par utilisation mémoire
        high_mem_processes = sorted(processes, key=lambda p: p.memory_percent, reverse=True)[:5]
        
        print("\n💾 Top 5 des processus par utilisation mémoire:")
        for i, process in enumerate(high_mem_processes, 1):
            print(f"   {i}. {process.user:12s} - {process.name:20s} - RAM: {process.memory_percent:5.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Fonction principale de démonstration"""
    print("🎬 Démonstration du module de surveillance des processus")
    print("=" * 80)
    
    demos = [
        ("Surveillance de base", demo_basic_monitoring),
        ("Surveillance réseau", demo_network_monitoring),
        ("Surveillance des fichiers", demo_file_monitoring),
        ("Surveillance complète", demo_full_monitoring),
        ("Patterns personnalisés", demo_custom_patterns),
        ("Surveillance des performances", demo_performance_monitoring),
    ]
    
    successful_demos = 0
    total_demos = len(demos)
    
    for demo_name, demo_func in demos:
        print(f"\n{'='*20} {demo_name} {'='*20}")
        
        try:
            if demo_func():
                successful_demos += 1
                print(f"✅ Démo '{demo_name}' réussie")
            else:
                print(f"❌ Démo '{demo_name}' échouée")
        except Exception as e:
            print(f"❌ Erreur lors de la démo '{demo_name}': {e}")
    
    print(f"\n{'='*80}")
    print(f"📊 Résumé: {successful_demos}/{total_demos} démonstrations réussies")
    
    if successful_demos == total_demos:
        print("🎉 Toutes les démonstrations sont passées avec succès!")
        print("\n💡 Le module de surveillance des processus est prêt à être utilisé!")
    else:
        print("⚠️  Certaines démonstrations ont échoué")
    
    print(f"\n📚 Consultez la documentation dans docs/PROCESS_MONITORING.md")
    print(f"🧪 Exécutez les tests avec: python3 test_process_monitoring.py")

if __name__ == "__main__":
    main() 