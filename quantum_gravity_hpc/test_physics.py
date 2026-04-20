"""
Unit Tests for Quantum Gravity Modules
Tests correctness of physics implementations with known solutions.
"""

import torch
import numpy as np
import sys
import traceback

class TestRunner:
    """Simple test runner with colored output"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def test(self, name, func):
        """Run a single test"""
        try:
            func()
            self.passed += 1
            print(f"✓ {name}")
            self.tests.append((name, True, None))
        except Exception as e:
            self.failed += 1
            print(f"✗ {name}")
            print(f"  Error: {str(e)}")
            self.tests.append((name, False, str(e)))
    
    def summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        print("\n" + "="*70)
        print(f"TEST SUMMARY: {self.passed}/{total} passed")
        print("="*70)
        
        if self.failed > 0:
            print("\nFailed tests:")
            for name, passed, error in self.tests:
                if not passed:
                    print(f"  - {name}: {error}")
        
        return self.failed == 0


def test_engine():
    """Test geodesic engine"""
    print("\n" + "="*70)
    print("TESTING ENGINE.PY")
    print("="*70)
    
    runner = TestRunner()
    
    from engine import MetricField, compute_christoffel_symbols, geodesic_acceleration
    
    # Test 1: Minkowski metric should give zero Christoffel symbols
    def test_minkowski_christoffel():
        g = torch.eye(4, dtype=torch.float64)
        dg = torch.zeros(4, 4, 4, dtype=torch.float64)
        
        Gamma = compute_christoffel_symbols(g, dg)
        
        assert torch.allclose(Gamma, torch.zeros_like(Gamma), atol=1e-10), \
            f"Minkowski Christoffel symbols should be zero, got max {torch.max(torch.abs(Gamma))}"
    
    runner.test("Minkowski metric → zero Christoffel symbols", test_minkowski_christoffel)
    
    # Test 2: Metric field interpolation
    def test_metric_interpolation():
        grid = torch.zeros(4, 4, 4, 4, 4, 4, dtype=torch.float64)
        
        # Set Minkowski everywhere
        for i in range(4):
            for j in range(4):
                for k in range(4):
                    for l in range(4):
                        grid[i, j, k, l] = torch.eye(4, dtype=torch.float64)
        
        metric_field = MetricField(grid, grid_spacing=1.0)
        
        # Interpolate at center
        coords = torch.tensor([1.5, 1.5, 1.5, 1.5], dtype=torch.float64)
        g = metric_field.interpolate_metric(coords)
        
        assert torch.allclose(g, torch.eye(4, dtype=torch.float64), atol=1e-6), \
            "Interpolated metric should be Minkowski"
    
    runner.test("Metric field interpolation", test_metric_interpolation)
    
    # Test 3: Geodesic in flat space should be straight line
    def test_flat_geodesic():
        grid = torch.zeros(4, 4, 4, 4, 4, 4, dtype=torch.float64)
        
        for i in range(4):
            for j in range(4):
                for k in range(4):
                    for l in range(4):
                        grid[i, j, k, l] = torch.eye(4, dtype=torch.float64)
        
        metric_field = MetricField(grid, grid_spacing=1.0)
        
        coords = torch.tensor([0.0, 0.0, 0.0, 0.0], dtype=torch.float64)
        velocity = torch.tensor([1.0, 0.1, 0.0, 0.0], dtype=torch.float64)
        
        accel = geodesic_acceleration(coords, velocity, metric_field)
        
        assert torch.allclose(accel, torch.zeros(4, dtype=torch.float64), atol=1e-6), \
            f"Acceleration in flat space should be zero, got {accel}"
    
    runner.test("Flat space → zero acceleration", test_flat_geodesic)
    
    return runner.summary()


def test_einstein_solver():
    """Test Einstein equations solver"""
    print("\n" + "="*70)
    print("TESTING EINSTEIN_SOLVER.PY")
    print("="*70)
    
    runner = TestRunner()
    
    from einstein_solver import EinsteinSolver
    
    # Test 1: Vacuum solution (T=0) should preserve Minkowski
    def test_vacuum_solution():
        solver = EinsteinSolver(grid_shape=(4, 4, 4, 4))
        
        # Minkowski metric
        g = torch.zeros(4, 4, 4, 4, 4, 4, dtype=torch.float64)
        for i in range(4):
            for j in range(4):
                for k in range(4):
                    for l in range(4):
                        g[i, j, k, l] = torch.eye(4, dtype=torch.float64)
        
        # Zero stress-energy
        T = torch.zeros(4, 4, 4, 4, 4, 4, dtype=torch.float64)
        
        # Should stay Minkowski (already a solution)
        g_solution, diag = solver.solve_einstein_equations(
            T, g, max_iterations=5, tolerance=1e-4, relaxation_param=0.1
        )
        
        # Check it didn't change much
        diff = torch.norm(g_solution - g)
        assert diff < 0.1, f"Vacuum solution changed too much: {diff}"
    
    runner.test("Vacuum solution preserves Minkowski", test_vacuum_solution)
    
    # Test 2: Ricci tensor for flat space is zero
    def test_flat_ricci():
        solver = EinsteinSolver(grid_shape=(4, 4, 4, 4))
        
        g = torch.eye(4, dtype=torch.float64)
        dg = torch.zeros(4, 4, 4, dtype=torch.float64)
        ddg = torch.zeros(4, 4, 4, 4, dtype=torch.float64)
        
        R = solver.compute_ricci_tensor(g, dg, ddg)
        
        assert torch.allclose(R, torch.zeros(4, 4, dtype=torch.float64), atol=1e-6), \
            f"Ricci tensor for flat space should be zero, got max {torch.max(torch.abs(R))}"
    
    runner.test("Flat space → zero Ricci tensor", test_flat_ricci)
    
    return runner.summary()


def test_hawking_radiation():
    """Test Hawking radiation calculations"""
    print("\n" + "="*70)
    print("TESTING HAWKING_RADIATION.PY")
    print("="*70)
    
    runner = TestRunner()
    
    from hawking_radiation import HawkingRadiation
    
    hawking = HawkingRadiation()
    
    # Test 1: Schwarzschild radius
    def test_schwarzschild_radius():
        M = 1.0  # Planck mass
        r_s = hawking.compute_schwarzschild_radius(M)
        
        expected = 2.0  # 2M in Planck units
        assert abs(r_s - expected) < 1e-10, f"r_s should be 2.0, got {r_s}"
    
    runner.test("Schwarzschild radius r_s = 2M", test_schwarzschild_radius)
    
    # Test 2: Hawking temperature
    def test_hawking_temperature():
        M = 1.0
        T_H = hawking.compute_hawking_temperature(M)
        
        expected = 1.0 / (8.0 * np.pi)
        assert abs(T_H - expected) < 1e-10, f"T_H should be {expected}, got {T_H}"
    
    runner.test("Hawking temperature T_H = 1/(8πM)", test_hawking_temperature)
    
    # Test 3: Entropy scales as area
    def test_entropy_scaling():
        M1 = 1.0
        M2 = 2.0
        
        S1 = hawking.compute_entropy(M1)
        S2 = hawking.compute_entropy(M2)
        
        # S ~ M^2 (area ~ r_s^2 ~ M^2)
        ratio = S2 / S1
        expected_ratio = 4.0  # (2M)^2 / M^2 = 4
        
        assert abs(ratio - expected_ratio) < 0.01, \
            f"Entropy should scale as M^2, got ratio {ratio} vs expected {expected_ratio}"
    
    runner.test("Entropy scales as M^2 (area law)", test_entropy_scaling)
    
    # Test 4: Evaporation time scales as M^3
    def test_evaporation_scaling():
        M1 = 1.0
        M2 = 2.0
        
        t1 = hawking.compute_evaporation_time(M1)
        t2 = hawking.compute_evaporation_time(M2)
        
        ratio = t2 / t1
        expected_ratio = 8.0  # (2M)^3 / M^3 = 8
        
        assert abs(ratio - expected_ratio) < 0.01, \
            f"Evaporation time should scale as M^3, got ratio {ratio}"
    
    runner.test("Evaporation time scales as M^3", test_evaporation_scaling)
    
    return runner.summary()


def test_quantum_field():
    """Test quantum field theory module"""
    print("\n" + "="*70)
    print("TESTING QUANTUM_FIELD.PY")
    print("="*70)
    
    runner = TestRunner()
    
    from quantum_field import QuantumFieldCurvedSpace
    
    # Test 1: Field initialization
    def test_field_initialization():
        field = QuantumFieldCurvedSpace(grid_shape=(4, 4, 4, 4), field_mass=1.0)
        
        # Check vacuum fluctuations are non-zero
        phi_rms = torch.sqrt(torch.mean(field.phi**2))
        assert phi_rms > 0, "Vacuum fluctuations should be non-zero"
        assert phi_rms < 1.0, f"Vacuum fluctuations too large: {phi_rms}"
    
    runner.test("Field initialization with vacuum fluctuations", test_field_initialization)
    
    # Test 2: Vacuum expectation values
    def test_vacuum_expectation():
        field = QuantumFieldCurvedSpace(grid_shape=(4, 4, 4, 4), field_mass=0.0)
        
        vev = field.compute_vacuum_expectation_value()
        
        assert vev['phi_squared'] > 0, "⟨φ²⟩ should be positive"
        assert vev['field_energy'] > 0, "Field energy should be positive"
    
    runner.test("Vacuum expectation values", test_vacuum_expectation)
    
    return runner.summary()


def test_testable_predictions():
    """Test predictions module"""
    print("\n" + "="*70)
    print("TESTING TESTABLE_PREDICTIONS.PY")
    print("="*70)
    
    runner = TestRunner()
    
    from testable_predictions import TestablePredictions
    
    predictor = TestablePredictions()
    
    # Test 1: LHC predictions
    def test_lhc_predictions():
        predictions = predictor.predict_lhc_signatures(
            fractal_dimension=3.0,  # Classical
            energy_scale=1000.0  # GeV
        )
        
        # Classical dimension should give small corrections
        assert abs(predictions['cross_section_modification']) < 0.01, \
            "Classical dimension should give small corrections"
    
    runner.test("LHC predictions for classical case", test_lhc_predictions)
    
    # Test 2: GW dispersion
    def test_gw_dispersion():
        predictions = predictor.predict_gw_dispersion(fractal_dimension=3.0)
        
        # Should have predictions for different frequencies
        assert 'f_10Hz' in predictions, "Should have 10 Hz prediction"
        assert 'f_100Hz' in predictions, "Should have 100 Hz prediction"
    
    runner.test("Gravitational wave dispersion predictions", test_gw_dispersion)
    
    return runner.summary()


def run_all_tests():
    """Run all unit tests"""
    print("="*70)
    print("QUANTUM GRAVITY UNIT TESTS")
    print("="*70)
    print("Testing all modules for correctness...")
    
    all_passed = True
    
    try:
        all_passed &= test_engine()
    except Exception as e:
        print(f"\n✗ ENGINE TESTS CRASHED: {e}")
        traceback.print_exc()
        all_passed = False
    
    try:
        all_passed &= test_einstein_solver()
    except Exception as e:
        print(f"\n✗ EINSTEIN SOLVER TESTS CRASHED: {e}")
        traceback.print_exc()
        all_passed = False
    
    try:
        all_passed &= test_hawking_radiation()
    except Exception as e:
        print(f"\n✗ HAWKING RADIATION TESTS CRASHED: {e}")
        traceback.print_exc()
        all_passed = False
    
    try:
        all_passed &= test_quantum_field()
    except Exception as e:
        print(f"\n✗ QUANTUM FIELD TESTS CRASHED: {e}")
        traceback.print_exc()
        all_passed = False
    
    try:
        all_passed &= test_testable_predictions()
    except Exception as e:
        print(f"\n✗ TESTABLE PREDICTIONS TESTS CRASHED: {e}")
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("="*70)
        print("\nCode is working correctly!")
    else:
        print("✗ SOME TESTS FAILED")
        print("="*70)
        print("\nPlease review errors above.")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
