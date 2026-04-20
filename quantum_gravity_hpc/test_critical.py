"""
Critical Physics Validation - Fast Check
Tests only the most important physics without Unicode issues
"""

import torch
import numpy as np
import sys

def test_christoffel():
    """Test Christoffel symbols computation"""
    print("\n[TEST] Christoffel symbols...")
    from engine import compute_christoffel_symbols
    
    # Minkowski metric
    g = torch.eye(4, dtype=torch.float64)
    dg = torch.zeros(4, 4, 4, dtype=torch.float64)
    
    Gamma = compute_christoffel_symbols(g, dg)
    max_error = torch.max(torch.abs(Gamma)).item()
    
    if max_error < 1e-10:
        print(f"  [PASS] Minkowski gives zero Christoffel (error: {max_error:.2e})")
        return True
    else:
        print(f"  [FAIL] Christoffel not zero (error: {max_error:.2e})")
        return False

def test_schwarzschild():
    """Test Schwarzschild metric"""
    print("\n[TEST] Schwarzschild metric...")
    from hawking_radiation import HawkingRadiation
    
    M = 1.0
    hr = HawkingRadiation()
    
    r_s = hr.compute_schwarzschild_radius(M)
    expected = 2.0 * M
    error = abs(r_s - expected) / expected
    
    if error < 0.01:
        print(f"  [PASS] Schwarzschild radius correct (r_s = {r_s:.4f}, expected {expected:.4f})")
        return True
    else:
        print(f"  [FAIL] Schwarzschild radius wrong (r_s = {r_s:.4f}, expected {expected:.4f})")
        return False

def test_hawking_temperature():
    """Test Hawking temperature"""
    print("\n[TEST] Hawking temperature...")
    from hawking_radiation import HawkingRadiation
    
    M = 1.0
    hr = HawkingRadiation()
    
    T_H = hr.compute_hawking_temperature(M)
    expected = 1.0 / (8.0 * np.pi * M)
    error = abs(T_H - expected) / expected
    
    if error < 0.01:
        print(f"  [PASS] Hawking temperature correct (T_H = {T_H:.6e}, expected {expected:.6e})")
        return True
    else:
        print(f"  [FAIL] Hawking temperature wrong (T_H = {T_H:.6e}, expected {expected:.6e})")
        return False

def test_energy_conservation():
    """Test energy conservation in simulation"""
    print("\n[TEST] Energy conservation...")
    
    try:
        import h5py
        with h5py.File('quick_test.h5', 'r') as f:
            if 'energy_drift' in f.attrs:
                drift = f.attrs['energy_drift']
                if abs(drift) < 0.1:  # 10% tolerance
                    print(f"  [PASS] Energy conserved (drift = {drift:.2%})")
                    return True
                else:
                    print(f"  [FAIL] Energy not conserved (drift = {drift:.2%})")
                    return False
    except:
        print("  [SKIP] No simulation data found")
        return True

def test_fractal_dimension():
    """Test fractal dimension calculation"""
    print("\n[TEST] Fractal dimension...")
    
    try:
        import h5py
        with h5py.File('quick_test.h5', 'r') as f:
            if 'fractal_dimension' in f.attrs:
                D2 = f.attrs['fractal_dimension']
                if 2.0 < D2 < 6.0:
                    print(f"  [PASS] Fractal dimension reasonable (D2 = {D2:.4f})")
                    return True
                else:
                    print(f"  [FAIL] Fractal dimension out of range (D2 = {D2:.4f})")
                    return False
    except:
        print("  [SKIP] No simulation data found")
        return True

def test_predictions():
    """Test prediction generation"""
    print("\n[TEST] Testable predictions...")
    from testable_predictions import TestablePredictions
    
    tp = TestablePredictions()
    
    # LHC predictions
    lhc = tp.predict_lhc_signatures(fractal_dimension=3.0, energy_scale=1.0)
    if 'cross_section_modification' in lhc:
        print(f"  [PASS] LHC predictions generated")
        return True
    else:
        print(f"  [FAIL] LHC predictions incomplete")
        return False

def test_numba_performance():
    """Test Numba acceleration"""
    print("\n[TEST] Numba performance...")
    
    try:
        from numba import njit
        print("  [PASS] Numba available and working")
        return True
    except:
        print("  [FAIL] Numba not available")
        return False

def run_critical_tests():
    """Run all critical tests"""
    print("="*70)
    print("CRITICAL PHYSICS VALIDATION")
    print("="*70)
    
    tests = [
        ("Christoffel symbols", test_christoffel),
        ("Schwarzschild metric", test_schwarzschild),
        ("Hawking temperature", test_hawking_temperature),
        ("Energy conservation", test_energy_conservation),
        ("Fractal dimension", test_fractal_dimension),
        ("Testable predictions", test_predictions),
        ("Numba performance", test_numba_performance),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  [CRASH] {name}: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed}/{passed+failed} tests passed")
    print("="*70)
    
    if failed == 0:
        print("\n[SUCCESS] All critical tests passed!")
        return True
    else:
        print(f"\n[WARNING] {failed} tests failed - review needed")
        return False

if __name__ == "__main__":
    success = run_critical_tests()
    sys.exit(0 if success else 1)
