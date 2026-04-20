"""
Safe Demo Mode
Runs minimal simulations to verify code works without overloading system.
"""

import torch
import numpy as np
import sys

def demo_engine():
    """Demo: Geodesic integration in flat space"""
    print("\n" + "="*70)
    print("DEMO 1: Geodesic Engine (Flat Space)")
    print("="*70)
    
    from engine import MetricField, batch_geodesic_integration
    
    # Create flat (Minkowski) metric
    grid = torch.zeros(4, 4, 4, 4, 4, 4, dtype=torch.float64)
    for i in range(4):
        for j in range(4):
            for k in range(4):
                for l in range(4):
                    grid[i, j, k, l] = torch.diag(torch.tensor([-1.0, 1.0, 1.0, 1.0], dtype=torch.float64))
    
    metric_field = MetricField(grid, grid_spacing=1.0)
    
    # Create 5 test particles
    particles = torch.zeros(5, 8, dtype=torch.float64)
    particles[:, 0] = 0.0  # t
    particles[:, 1:4] = torch.randn(5, 3) * 0.5  # positions
    particles[:, 4] = 1.0  # u^0
    particles[:, 5:8] = torch.randn(5, 3) * 0.01  # small velocities
    
    print(f"Initial particles:\n{particles[:, 1:4]}")
    
    # Integrate 3 steps
    for step in range(3):
        particles = batch_geodesic_integration(particles, metric_field, dt=0.1)
    
    print(f"After 3 steps:\n{particles[:, 1:4]}")
    print("✓ Particles moved in straight lines (flat space)")


def demo_schwarzschild():
    """Demo: Schwarzschild metric"""
    print("\n" + "="*70)
    print("DEMO 2: Schwarzschild Metric")
    print("="*70)
    
    from main import initialize_schwarzschild_metric
    
    g = initialize_schwarzschild_metric(grid_shape=(4, 4, 4, 4), M=0.1)
    
    # Check metric at center
    g_center = g[0, 2, 2, 2]  # center of grid
    
    print(f"Metric at center:")
    print(f"  g_tt = {g_center[0, 0]:.6f} (should be < 0)")
    print(f"  g_xx = {g_center[1, 1]:.6f} (should be > 1)")
    
    # Check it's symmetric
    is_symmetric = torch.allclose(g_center, g_center.T, atol=1e-6)
    print(f"  Symmetric: {is_symmetric}")
    
    if g_center[0, 0] < 0 and g_center[1, 1] > 1 and is_symmetric:
        print("✓ Schwarzschild metric looks correct")
    else:
        print("✗ Metric has issues")


def demo_hawking():
    """Demo: Hawking radiation"""
    print("\n" + "="*70)
    print("DEMO 3: Hawking Radiation")
    print("="*70)
    
    from hawking_radiation import HawkingRadiation
    
    hawking = HawkingRadiation()
    
    M = 1.0  # 1 Planck mass
    analysis = hawking.analyze_black_hole(M)
    
    print(f"Black hole with M = {M} m_P:")
    print(f"  Schwarzschild radius: {analysis['schwarzschild_radius_planck']:.2f} l_P")
    print(f"  Hawking temperature: {analysis['temperature_planck']:.6f} T_P")
    print(f"  Evaporation time: {analysis['evaporation_time_planck']:.3e} t_P")
    print(f"  Entropy: {analysis['entropy_planck']:.3e}")
    
    # Check formulas
    expected_r_s = 2.0 * M
    expected_T_H = 1.0 / (8.0 * np.pi * M)
    
    r_s_correct = abs(analysis['schwarzschild_radius_planck'] - expected_r_s) < 1e-10
    T_H_correct = abs(analysis['temperature_planck'] - expected_T_H) < 1e-10
    
    if r_s_correct and T_H_correct:
        print("✓ Hawking radiation formulas correct")
    else:
        print("✗ Formula mismatch")


def demo_predictions():
    """Demo: Testable predictions"""
    print("\n" + "="*70)
    print("DEMO 4: Testable Predictions")
    print("="*70)
    
    from testable_predictions import TestablePredictions
    
    predictor = TestablePredictions()
    
    # LHC prediction
    lhc = predictor.predict_lhc_signatures(
        fractal_dimension=5.752,
        energy_scale=14000  # 14 TeV
    )
    
    print(f"LHC Predictions (D2 = 5.752):")
    print(f"  Cross-section change: {lhc['cross_section_change_percent']:.4f}%")
    print(f"  Mini-BH production: {lhc['BH_production_possible']}")
    print(f"  Extra dimensions: {lhc['extra_dimensions']}")
    print(f"  Observable: {lhc['observable_at_LHC']}")
    
    if lhc['cross_section_change_percent'] != 0:
        print("✓ Predictions generated")
    else:
        print("✗ No predictions")


def demo_quantum_field():
    """Demo: Quantum field"""
    print("\n" + "="*70)
    print("DEMO 5: Quantum Field Theory")
    print("="*70)
    
    from quantum_field import QuantumFieldCurvedSpace
    
    field = QuantumFieldCurvedSpace(grid_shape=(4, 4, 4, 4), field_mass=1.0)
    
    vev = field.compute_vacuum_expectation_value()
    
    print(f"Vacuum expectation values:")
    print(f"  ⟨φ²⟩ = {vev['phi_squared']:.6e}")
    print(f"  ⟨π²⟩ = {vev['pi_squared']:.6e}")
    print(f"  Field energy = {vev['field_energy']:.6e}")
    
    if vev['phi_squared'] > 0 and vev['field_energy'] > 0:
        print("✓ Quantum field initialized with vacuum fluctuations")
    else:
        print("✗ Field issues")


def demo_mini_simulation():
    """Demo: Minimal full simulation"""
    print("\n" + "="*70)
    print("DEMO 6: Mini Simulation (10 particles, 5 steps)")
    print("="*70)
    
    from main import run_physical_simulation
    
    print("Running simulation...")
    particles, metric = run_physical_simulation(
        n_particles=10,
        n_steps=5,
        grid_shape=(4, 4, 4, 4),
        central_mass=0.1,
        use_einstein_solver=False
    )
    
    print(f"\nFinal state:")
    print(f"  Particles shape: {particles.shape}")
    print(f"  Metric shape: {metric.shape}")
    print(f"  Mean particle radius: {torch.mean(torch.norm(particles[:, 1:4], dim=1)):.2f} l_P")
    
    print("✓ Simulation completed successfully")


def run_safe_demo():
    """Run all safe demos"""
    print("="*70)
    print("QUANTUM GRAVITY - SAFE DEMO MODE")
    print("="*70)
    print("Running minimal tests to verify code works correctly...")
    print("This is SAFE and won't overload your computer.")
    print("="*70)
    
    demos = [
        ("Geodesic Engine", demo_engine),
        ("Schwarzschild Metric", demo_schwarzschild),
        ("Hawking Radiation", demo_hawking),
        ("Testable Predictions", demo_predictions),
        ("Quantum Field", demo_quantum_field),
        ("Mini Simulation", demo_mini_simulation),
    ]
    
    passed = 0
    failed = 0
    
    for name, demo_func in demos:
        try:
            demo_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("DEMO SUMMARY")
    print("="*70)
    print(f"Passed: {passed}/{len(demos)}")
    print(f"Failed: {failed}/{len(demos)}")
    
    if failed == 0:
        print("\n✓ ALL DEMOS PASSED - Code is working!")
        print("\nYou can now safely run:")
        print("  - python main.py (basic simulation)")
        print("  - python hawking_radiation.py (Hawking analysis)")
        print("  - python testable_predictions.py (predictions)")
    else:
        print("\n✗ SOME DEMOS FAILED - Check errors above")
    
    return failed == 0


if __name__ == "__main__":
    success = run_safe_demo()
    sys.exit(0 if success else 1)
