"""
Run All Tests - Quantum Gravity v3.2.1
======================================

Запускает все валидационные тесты проекта в правильном порядке.

Author: wosky021@gmail.com
Date: April 21, 2026
"""

import subprocess
import sys
import time

# Правильный Python executable
PYTHON = r"C:\Users\User\AppData\Local\Programs\Python\Python313\python.exe"

TESTS = [
    ("Bianchi Identities (Minkowski)", "test_bianchi_minkowski.py"),
    ("Performance Benchmark (40x speedup)", "test_performance_benchmark.py"),
    ("Schwarzschild & Kerr Metrics", "test_schwarzschild_kerr.py"),
    ("Parametric Alpha Analysis", "test_parametric_alpha.py"),
    ("Observational Signatures", "generate_observational_report.py"),
]


def run_test(name, script):
    """Запустить один тест."""
    print(f"\n{'='*70}")
    print(f"Running: {name}")
    print(f"Script: {script}")
    print(f"{'='*70}\n")
    
    start = time.time()
    
    try:
        result = subprocess.run(
            [PYTHON, script],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        elapsed = time.time() - start
        
        if result.returncode == 0:
            print(f"\n[OK] {name} - PASSED ({elapsed:.1f}s)")
            return True
        else:
            print(f"\n[FAIL] {name} - FAILED ({elapsed:.1f}s)")
            if result.stderr:
                print(f"Error: {result.stderr[:500]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"\n[TIMEOUT] {name} - exceeded 5 minutes")
        return False
    except Exception as e:
        print(f"\n[ERROR] {name} - {e}")
        return False


def main():
    """Запустить все тесты."""
    
    print("\n" + "="*70)
    print("QUANTUM GRAVITY v3.2.1 - COMPLETE TEST SUITE")
    print("="*70)
    print(f"\nDate: 2026-04-21")
    print(f"Total tests: {len(TESTS)}")
    print(f"\nThis will take approximately 5-10 minutes...")
    
    results = []
    total_start = time.time()
    
    for name, script in TESTS:
        success = run_test(name, script)
        results.append((name, success))
    
    total_time = time.time() - total_start
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}\n")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "[OK]  " if success else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\n{'='*70}")
    print(f"Results: {passed}/{total} tests passed ({100*passed/total:.0f}%)")
    print(f"Total time: {total_time:.1f}s")
    print(f"{'='*70}")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        print("Project is ready for publication.")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed.")
        print("Review the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
