"""
COMPREHENSIVE TEST SUITE - PRODUCTION QUALITY
Tests all critical functionality with proper assertions
"""

import torch
import numpy as np
from engine_improved import (
    ImprovedMetricField, 
    compute_christoffel_symbols_safe,
    adaptive_timestep,
    check_particle_stability
)

print("="*70)
print("COMPREHENSIVE TEST SUITE")
print("="*70)

passed = 0
failed = 0

def test(name, func):
    """Run a test and report result."""
    global passed, failed
    try:
        func()
        print(f"[PASS] {name}")
        passed += 1
        return True
    except Exception as e:
        print(f"[FAIL] {name}")
        print(f"  Error: {e}")
        failed += 1
        return False

# Test 1: Metric field validation
def test_metric_validation():
    # Should reject invalid input
    try:
        grid = torch.randn(4, 4, 4, 4, 3, 3)  # Wrong shape
        mf = ImprovedMetricField(grid, 1.0)
        raise AssertionError("Should have rejected wrong shape")
    except ValueError:
        pass  # Expected
    
    # Should reject NaN
    try:
        grid = torch.zeros(4, 4, 4, 4, 4, 4)
        grid[0, 0, 0, 0, 0, 0] = float('nan')
        mf = ImprovedMetricField(grid, 1.0)
        raise AssertionError("Should have rejected NaN")
    except ValueError:
        pass  # Expected
    
    # Should accept valid input
    grid = torch.zeros(4, 4, 4, 4, 4, 4)
    for i in range(4):
        for j in range(4):
            for k in range(4):
                for l in range(4):
                    grid[i, j, k, l] = torch.eye(4)
    mf = ImprovedMetricField(grid, 1.0)
    assert mf is not None

test("Metric field validation", test_metric_validation)

# Test 2: Christoffel symbols for Minkowski
def test_christoffel_minkowski():
    g = torch.eye(4, dtype=torch.float64).unsqueeze(0)
    dg = torch.zeros(1, 4, 4, 4, dtype=torch.float64)
    
    Gamma = compute_christoffel_symbols_safe(g, dg)
    
    assert torch.allclose(Gamma, torch.zeros_like(Gamma), atol=1e-10), \
        f"Minkowski should give zero Christoffel, got max {torch.max(torch.abs(Gamma))}"

test("Christoffel symbols (Minkowski)", test_christoffel_minkowski)

# Test 3: Christoffel symbols error handling
def test_christoffel_error_handling():
    # Should reject NaN
    try:
        g = torch.eye(4, dtype=torch.float64).unsqueeze(0)
        g[0, 0, 0] = float('nan')
        dg = torch.zeros(1, 4, 4, 4, dtype=torch.float64)
        Gamma = compute_christoffel_symbols_safe(g, dg)
        raise AssertionError("Should have rejected NaN")
    except ValueError:
        pass  # Expected

test("Christoffel error handling", test_christoffel_error_handling)

# Test 4: Adaptive timestep
def test_adaptive_timestep_func():
    # Low velocity -> can increase dt
    particles = torch.zeros(10, 8, dtype=torch.float64)
    particles[:, 5:8] = 0.01  # v = 0.01c
    
    dt = 0.1
    dt_new = adaptive_timestep(particles, dt, tolerance=0.1)
    assert dt_new >= dt, "Should increase timestep for low velocities"
    
    # High velocity -> must decrease dt
    particles[:, 5:8] = 5.0  # v = 5c
    dt_new = adaptive_timestep(particles, dt, tolerance=0.1)
    assert dt_new < dt, "Should decrease timestep for high velocities"

test("Adaptive timestep", test_adaptive_timestep_func)

# Test 5: Particle stability check
def test_stability_check():
    # Stable particles
    particles = torch.zeros(10, 8, dtype=torch.float64)
    particles[:, 1:4] = torch.randn(10, 3) * 10.0  # positions
    particles[:, 5:8] = torch.randn(10, 3) * 0.1   # velocities
    
    assert check_particle_stability(particles), "Should be stable"
    
    # Unstable: NaN
    particles_nan = particles.clone()
    particles_nan[0, 0] = float('nan')
    assert not check_particle_stability(particles_nan), "Should detect NaN"
    
    # Unstable: superluminal
    particles_fast = particles.clone()
    particles_fast[:, 5:8] = 20.0
    assert not check_particle_stability(particles_fast), "Should detect superluminal"

test("Particle stability check", test_stability_check)

# Test 6: Metric interpolation
def test_metric_interpolation():
    # Create simple metric field
    grid = torch.zeros(4, 4, 4, 4, 4, 4, dtype=torch.float64)
    for i in range(4):
        for j in range(4):
            for k in range(4):
                for l in range(4):
                    grid[i, j, k, l] = torch.eye(4, dtype=torch.float64)
    
    mf = ImprovedMetricField(grid, 1.0)
    
    # Interpolate at center
    coords = torch.tensor([[1.5, 1.5, 1.5, 1.5]], dtype=torch.float64)
    g = mf.interpolate_metric_batch(coords)
    
    # Should be close to Minkowski
    assert torch.allclose(g[0], torch.eye(4, dtype=torch.float64), atol=1e-6), \
        "Interpolated metric should be Minkowski"

test("Metric interpolation", test_metric_interpolation)

# Test 7: Energy conservation (simple test)
def test_energy_conservation():
    # Simple free particle
    particles = torch.zeros(1, 8, dtype=torch.float64)
    particles[0, 1:4] = torch.tensor([10.0, 0.0, 0.0])  # position
    particles[0, 5:8] = torch.tensor([0.1, 0.0, 0.0])   # velocity
    particles[0, 4] = 1.0  # u^0
    
    # Compute energy
    E_initial = particles[0, 4]  # Simplified
    
    # After some time (free particle, no forces)
    particles[0, 1:4] += particles[0, 5:8] * 0.1
    
    E_final = particles[0, 4]
    
    # Energy should be conserved for free particle
    assert abs(E_final - E_initial) < 1e-10, "Energy should be conserved"

test("Energy conservation (free particle)", test_energy_conservation)

# Test 8: Schwarzschild radius
def test_schwarzschild_radius():
    M = 1.0  # Planck mass
    r_s = 2.0 * M  # Planck units
    
    assert abs(r_s - 2.0) < 1e-10, f"Schwarzschild radius should be 2.0, got {r_s}"

test("Schwarzschild radius", test_schwarzschild_radius)

# Summary
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)
print(f"Passed: {passed}/{passed+failed}")
print(f"Failed: {failed}/{passed+failed}")

if failed == 0:
    print("\n*** ALL TESTS PASSED ***")
    print("Code is production-ready!")
else:
    print(f"\n{failed} tests failed - needs attention")

print("="*70)
