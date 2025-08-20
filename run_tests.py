#!/usr/bin/env python3
"""
Test runner for VigilantRaccoon
Executes all tests and provides detailed reporting
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def find_test_directory(start_dir: str = None) -> Path:
    """Find the tests directory"""
    if start_dir is None:
        start_dir = os.getcwd()
    
    # Look for tests directory
    test_dir = Path(start_dir) / "tests"
    if test_dir.exists() and test_dir.is_dir():
        return test_dir
    
    # Look in parent directories
    parent = Path(start_dir).parent
    if parent != Path(start_dir):
        return find_test_directory(str(parent))
    
    print(f"Test directory not found: {start_dir}")
    return None

def run_tests(test_dir: Path, test_name: str = None) -> tuple[int, int, int]:
    """Run tests and return results"""
    os.chdir(test_dir)
    
    if test_name:
        # Run specific test
        cmd = [sys.executable, "-m", "pytest", f"test_{test_name}.py", "-v"]
    else:
        # Run all tests
        cmd = [sys.executable, "-m", "pytest", "-v"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        # Parse pytest output
        output_lines = result.stdout.split('\n')
        total_tests = 0
        failures = 0
        errors = 0
        
        for line in output_lines:
            if 'collected' in line and 'items' in line:
                # Extract total test count
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit() and i > 0 and parts[i-1] == 'collected':
                        total_tests = int(part)
                        break
            elif 'FAILED' in line:
                failures += 1
            elif 'ERROR' in line:
                errors += 1
        
        return total_tests, failures, errors
        
    except subprocess.TimeoutExpired:
        print("Tests timed out after 5 minutes")
        return 0, 0, 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 0, 0, 1

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py [all|test_name]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Find test directory
    test_dir = find_test_directory()
    if not test_dir:
        sys.exit(1)
    
    print(f"Test directory: {test_dir}")
    
    if command == "all":
        # Run all tests
        print("Running all tests...")
        start_time = time.time()
        
        total_tests, failures, errors = run_tests(test_dir)
        
        elapsed_time = time.time() - start_time
        
        print("\nTEST RESULTS")
        print("=" * 50)
        print(f"Tests executed: {total_tests}")
        print(f"Failures: {failures}")
        print(f"Errors: {errors}")
        print(f"Time elapsed: {elapsed_time:.2f} seconds")
        
        if failures > 0 or errors > 0:
            print("\nSOME TESTS FAILED")
            sys.exit(1)
        else:
            print("\nAll tests passed!")
            sys.exit(0)
    
    elif command == "list":
        # List available tests
        test_files = list(test_dir.glob("test_*.py"))
        if test_files:
            print("Available tests:")
            for test_file in test_files:
                test_name = test_file.stem[5:]  # Remove 'test_' prefix
                print(f"  - {test_name}")
        else:
            print("No test files found")
    
    elif command == "help":
        # Show help
        print("VigilantRaccoon Test Runner")
        print("=" * 30)
        print("Commands:")
        print("  all     - Run all tests")
        print("  list    - List available tests")
        print("  help    - Show this help")
        print("  <name>  - Run specific test (e.g., 'config' for test_config.py)")
        print("\nExamples:")
        print("  python run_tests.py all")
        print("  python run_tests.py config")
        print("  python run_tests.py list")
    
    else:
        # Run specific test
        test_name = command
        test_file = test_dir / f"test_{test_name}.py"
        
        if not test_file.exists():
            print(f"Test file not found: {test_file}")
            sys.exit(1)
        
        print(f"Running test: {test_name}")
        start_time = time.time()
        
        total_tests, failures, errors = run_tests(test_dir, test_name)
        
        elapsed_time = time.time() - start_time
        
        print(f"\nTest '{test_name}' completed in {elapsed_time:.2f} seconds")
        print(f"Tests executed: {total_tests}")
        print(f"Failures: {failures}")
        print(f"Errors: {errors}")
        
        if failures > 0 or errors > 0:
            print(f"Test '{test_name}' failed")
            sys.exit(1)
        else:
            print(f"Test '{test_name}' passed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1) 