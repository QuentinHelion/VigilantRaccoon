#!/usr/bin/env python3
"""
Process monitoring module demonstration
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def demo_basic_monitoring():
    """Basic process monitoring demonstration"""
    print("Basic process monitoring demonstration")
    print("=" * 60)
    
    try:
        # Create monitor
        monitor = ProcessMonitor()
        
        # Get active processes
        print("Retrieving active processes...")
        processes = monitor.get_active_processes("demo-server")
        print(f"Success: {len(processes)} processes retrieved")
        
        # Display first processes
        print("\nProcess monitoring overview:")
        for i, process in enumerate(processes[:10], 1):
            print(f"   {i:2d}. {process.user:12s} - {process.name:20s} (PID: {process.pid:6d})")
        
        # Analyze specific process
        if processes:
            print(f"\nAnalyzing process {processes[0].name} (PID: {processes[0].pid})...")
            alerts = monitor.analyze_process_behavior(processes[0])
            print(f"Success: {len(alerts)} alerts generated")
            
            for alert in alerts:
                print(f"   Alert: {alert.rule}: {alert.message}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def demo_network_monitoring():
    """Network monitoring demonstration"""
    print("\nNetwork monitoring demonstration")
    print("=" * 60)
    
    try:
        monitor = ProcessMonitor()
        
        # Get network connections
        print("Retrieving network connections...")
        connections = monitor.get_network_connections(1)  # PID 1 (systemd)
        print(f"Success: {len(connections)} network connections found")
        
        # Display connections
        if connections:
            print("\nActive network connections:")
            for i, (local_addr, local_port, remote_addr, remote_port, status) in enumerate(connections[:10], 1):
                print(f"   {i:2d}. {local_addr:15s}:{local_port:5d} -> {remote_addr:15s}:{remote_port:5d} ({status})")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def demo_file_monitoring():
    """File monitoring demonstration"""
    print("\nFile monitoring demonstration")
    print("=" * 60)
    
    try:
        monitor = ProcessMonitor()
        
        # Check suspicious files
        print("Checking suspicious files...")
        alerts = monitor.check_file_activity("demo-server")
        print(f"Success: {len(alerts)} file alerts generated")
        
        # Display alerts
        if alerts:
            print("\nFile alerts:")
            for alert in alerts:
                print(f"   • {alert.rule}: {alert.message}")
        else:
            print("No suspicious files detected")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def demo_complete_monitoring():
    """Complete monitoring demonstration"""
    print("\nComplete monitoring demonstration")
    print("=" * 60)
    
    try:
        print("Executing complete monitoring...")
        start_time = time.time()
        
        alerts = run_process_monitoring("demo-server")
        
        elapsed_time = time.time() - start_time
        
        print(f"Success: Monitoring completed in {elapsed_time:.2f} seconds")
        print(f"Summary: {len(alerts)} alerts generated")
        
        # Display alerts by type
        if alerts:
            by_type = {}
            for alert in alerts:
                alert_type = alert.rule
                if alert_type not in by_type:
                    by_type[alert_type] = []
                by_type[alert_type].append(alert)
            
            print("\nAlerts by type:")
            for alert_type, type_alerts in by_type.items():
                print(f"   {alert_type}: {len(type_alerts)} alerts")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def demo_test_process():
    """Test process creation demonstration"""
    print("\nTest process creation demonstration")
    print("=" * 60)
    
    try:
        # Create test process
        print("Creating test process...")
        process = subprocess.Popen(
            ["sleep", "10"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print(f"Test process created with PID: {process.pid}")
        
        # Monitor processes
        monitor = ProcessMonitor()
        alerts = monitor.monitor_processes("demo-server")
        
        print(f"Success: {len(alerts)} alerts generated for test process")
        
        # Terminate test process
        process.terminate()
        process.wait()
        print("Test process terminated")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def demo_resource_monitoring():
    """Resource usage monitoring demonstration"""
    print("\nResource usage monitoring demonstration")
    print("=" * 60)
    
    try:
        # Create resource-intensive process
        print("Creating resource-intensive process...")
        process = subprocess.Popen(
            ["python3", "-c", "import time; [i**2 for i in range(1000000)]; time.sleep(5)"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print(f"Resource-intensive process created with PID: {process.pid}")
        
        # Wait for process to start
        time.sleep(1)
        
        # Monitor processes
        monitor = ProcessMonitor()
        alerts = monitor.monitor_processes("demo-server")
        
        print(f"Success: {len(alerts)} alerts generated for resource monitoring")
        
        # Terminate process
        process.terminate()
        process.wait()
        print("Resource-intensive process terminated")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_demo(demo_name: str) -> bool:
    """Run specific demonstration"""
    demos = {
        'basic': demo_basic_monitoring,
        'network': demo_network_monitoring,
        'file': demo_file_monitoring,
        'complete': demo_complete_monitoring,
        'test_process': demo_test_process,
        'resources': demo_resource_monitoring
    }
    
    if demo_name not in demos:
        print(f"Unknown demonstration: {demo_name}")
        return False
    
    try:
        return demos[demo_name]()
    except Exception as e:
        print(f"Error during demonstration '{demo_name}': {e}")
        return False

def main():
    """Main function"""
    print("Process Monitoring Demonstration - VigilantRaccoon")
    print("=" * 60)
    
    # Available demonstrations
    demos = ['basic', 'network', 'file', 'complete', 'test_process', 'resources']
    
    print("Available demonstrations:")
    for i, demo in enumerate(demos, 1):
        print(f"   {i}. {demo}")
    
    print("\nRunning all demonstrations...")
    
    successful_demos = 0
    total_demos = len(demos)
    
    for demo_name in demos:
        print(f"\n{'='*20} {demo_name.upper()} {'='*20}")
        if run_demo(demo_name):
            successful_demos += 1
            print(f"Demo '{demo_name}' successful")
        else:
            print(f"Demo '{demo_name}' failed")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Summary: {successful_demos}/{total_demos} demonstrations successful")
    
    if successful_demos < total_demos:
        print("Some demonstrations failed")
    
    print("\nDocumentation available in docs/PROCESS_MONITORING.md")
    print("Run tests with: python3 test_process_monitoring.py")

if __name__ == "__main__":
    main() 