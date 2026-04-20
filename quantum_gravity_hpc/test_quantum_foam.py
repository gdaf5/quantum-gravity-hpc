"""
Unit Tests for Quantum Foam Module
Tests stochastic creation, collapse, and evaporation mechanisms.
"""

import torch
import numpy as np
from quantum_foam import QuantumFoam, VirtualParticle
from engine import MetricField


def create_test_metric(grid_shape=(8, 8, 8, 8), dtype=torch.float64):
    """Create simple Minkowski metric for testing"""
    g_metric = torch.zeros((*grid_shape, 4, 4), dtype=dtype)
    
    for it in range(grid_shape[0]):
        for ix in range(grid_shape[1]):
            for iy in range(grid_shape[2]):
                for iz in range(grid_shape[3]):
                    g_metric[it, ix, iy, iz] = torch.diag(
                        torch.tensor([-1.0, 1.0, 1.0, 1.0], dtype=dtype)
                    )
    
    return g_metric


def test_foam_initialization():
    """Test quantum foam initialization"""
    print("\n" + "="*70)
    print("TEST 1: Foam Initialization")
    print("="*70)
    
    foam = QuantumFoam(
        grid_shape=(8, 8, 8, 8),
        grid_spacing=1.0,
        creation_rate=0.1,
        collapse_threshold=1.0,
        softening_length=0.1
    )
    
    assert len(foam.virtual_particles) == 0
    assert foam.stats['total_created'] == 0
    assert foam.stats['current_particles'] == 0
    
    print("[OK] Foam initialized correctly")
    print(f"  Grid shape: {foam.grid_shape}")
    print(f"  Creation rate: {foam.creation_rate}")
    print(f"  Softening: {foam.softening_length} l_P")


def test_virtual_particle_creation():
    """Test virtual particle creation"""
    print("\n" + "="*70)
    print("TEST 2: Virtual Particle Creation")
    print("="*70)
    
    foam = QuantumFoam(creation_rate=0.5)
    
    position = torch.tensor([0.0, 1.0, 2.0, 3.0], dtype=torch.float64)
    current_time = 0.0
    
    particle = foam.create_virtual_particle(position, current_time)
    
    assert particle.mass > 0
    assert particle.lifetime > 0
    assert particle.birth_time == current_time
    assert not particle.is_singularity
    assert len(foam.virtual_particles) == 1
    assert foam.stats['total_created'] == 1
    
    print("[OK] Virtual particle created successfully")
    print(f"  Mass: {particle.mass:.3f} m_P")
    print(f"  Lifetime: {particle.lifetime:.3f} t_P")
    print(f"  Position: {particle.position.numpy()}")


def test_collapse_condition():
    """Test singularity collapse condition"""
    print("\n" + "="*70)
    print("TEST 3: Collapse Condition")
    print("="*70)
    
    foam = QuantumFoam(collapse_threshold=1.0)
    
    # Create two particles close together
    pos1 = torch.tensor([0.0, 0.0, 0.0, 0.0], dtype=torch.float64)
    pos2 = torch.tensor([0.0, 0.5, 0.0, 0.0], dtype=torch.float64)
    
    p1 = VirtualParticle(pos1, mass=1.0, lifetime=10.0, birth_time=0.0)
    p2 = VirtualParticle(pos2, mass=1.0, lifetime=10.0, birth_time=0.0)
    
    # Check collapse (r_s = 2*2 = 4, r = 0.5, should collapse)
    should_collapse = foam.check_collapse_condition(p1, p2)
    
    print(f"  Particle 1: m = {p1.mass:.2f} m_P at {p1.position[1:].numpy()}")
    print(f"  Particle 2: m = {p2.mass:.2f} m_P at {p2.position[1:].numpy()}")
    print(f"  Distance: {0.5:.2f} l_P")
    print(f"  Combined r_s: {4.0:.2f} l_P")
    print(f"  Should collapse: {should_collapse}")
    
    assert should_collapse, "Particles should collapse"
    print("[OK] Collapse condition working correctly")


def test_singularity_formation():
    """Test singularity formation from particle collapse"""
    print("\n" + "="*70)
    print("TEST 4: Singularity Formation")
    print("="*70)
    
    foam = QuantumFoam()
    
    pos1 = torch.tensor([0.0, 0.0, 0.0, 0.0], dtype=torch.float64)
    pos2 = torch.tensor([0.0, 1.0, 0.0, 0.0], dtype=torch.float64)
    
    p1 = VirtualParticle(pos1, mass=1.5, lifetime=10.0, birth_time=0.0)
    p2 = VirtualParticle(pos2, mass=2.5, lifetime=10.0, birth_time=0.0)
    
    singularity = foam.collapse_to_singularity(p1, p2)
    
    assert singularity.is_singularity
    assert singularity.mass == 4.0  # 1.5 + 2.5
    assert singularity.schwarzschild_radius == 8.0  # 2 * 4.0
    assert foam.stats['total_collapsed'] == 1
    
    print("[OK] Singularity formed successfully")
    print(f"  Total mass: {singularity.mass:.2f} m_P")
    print(f"  Schwarzschild radius: {singularity.schwarzschild_radius:.2f} l_P")
    print(f"  Evaporation time: {singularity.lifetime:.3e} t_P")


def test_hawking_evaporation():
    """Test Hawking evaporation of singularities"""
    print("\n" + "="*70)
    print("TEST 5: Hawking Evaporation")
    print("="*70)
    
    foam = QuantumFoam(enable_hawking_evaporation=True)
    
    # Create singularity
    pos = torch.tensor([0.0, 0.0, 0.0, 0.0], dtype=torch.float64)
    singularity = VirtualParticle(pos, mass=2.0, lifetime=1000.0, 
                                  birth_time=0.0, is_singularity=True)
    
    initial_mass = singularity.mass
    dt = 1.0
    
    dM = foam.compute_hawking_evaporation(singularity, dt)
    
    assert dM < 0, "Mass should decrease"
    
    # Apply evaporation
    singularity.mass += dM
    
    print(f"  Initial mass: {initial_mass:.6f} m_P")
    print(f"  Mass loss (dt={dt} t_P): {dM:.6e} m_P")
    print(f"  Final mass: {singularity.mass:.6f} m_P")
    print(f"  Luminosity: {1.0/(15360*np.pi*initial_mass**2):.6e} P_P")
    print("[OK] Hawking evaporation working correctly")


def test_softening_regularization():
    """Test softening parameter prevents numerical explosions"""
    print("\n" + "="*70)
    print("TEST 6: Softening Regularization")
    print("="*70)
    
    foam = QuantumFoam(softening_length=0.1)
    
    # Test force at very small distances
    distances = [0.001, 0.01, 0.1, 1.0]
    m1, m2 = 1.0, 1.0
    
    print(f"  Testing force with epsilon = {foam.softening_length} l_P")
    print(f"  Masses: m1 = {m1} m_P, m2 = {m2} m_P\n")
    
    for r in distances:
        F = foam.compute_regularized_force(r, m1, m2)
        F_newton = m1 * m2 / r**2  # Without softening
        
        print(f"  r = {r:6.3f} l_P: F_soft = {F:8.3f}, F_newton = {F_newton:8.3f}")
        
        assert not np.isinf(F), f"Force should be finite at r={r}"
        assert not np.isnan(F), f"Force should not be NaN at r={r}"
    
    print("\n[OK] Softening prevents numerical explosions")


def test_foam_evolution():
    """Test full foam evolution cycle"""
    print("\n" + "="*70)
    print("TEST 7: Full Foam Evolution")
    print("="*70)
    
    grid_shape = (8, 8, 8, 8)
    g_metric = create_test_metric(grid_shape)
    
    # Add fluctuations
    g_metric += torch.randn_like(g_metric) * 0.1
    
    metric_field = MetricField(g_metric, grid_spacing=1.0)
    
    foam = QuantumFoam(
        grid_shape=grid_shape,
        creation_rate=0.5,
        collapse_threshold=1.0,
        enable_hawking_evaporation=True
    )
    
    dt = 0.1
    n_steps = 20
    
    print(f"  Evolving for {n_steps} steps (dt = {dt} t_P)...\n")
    
    for step in range(n_steps):
        current_time = step * dt
        stats = foam.evolve_foam(metric_field, current_time, dt)
        
        if step % 5 == 0:
            print(f"  Step {step:2d}: Particles = {stats['total_particles']:2d}, "
                  f"Singularities = {stats['singularities']:2d}")
    
    final_stats = foam.get_statistics()
    
    print(f"\n  Final state:")
    print(f"    Total created: {final_stats['total_created']}")
    print(f"    Total collapsed: {final_stats['total_collapsed']}")
    print(f"    Current particles: {final_stats['current_particles']}")
    
    assert final_stats['total_created'] > 0, "Should create particles"
    print("\n[OK] Foam evolution working correctly")


def test_energy_density_computation():
    """Test local energy density computation"""
    print("\n" + "="*70)
    print("TEST 8: Energy Density Computation")
    print("="*70)
    
    grid_shape = (8, 8, 8, 8)
    
    # Minkowski (should have zero energy density)
    g_minkowski = create_test_metric(grid_shape)
    metric_field_flat = MetricField(g_minkowski, grid_spacing=1.0)
    
    # Perturbed (should have non-zero energy density)
    g_perturbed = g_minkowski + torch.randn_like(g_minkowski) * 0.2
    metric_field_curved = MetricField(g_perturbed, grid_spacing=1.0)
    
    foam = QuantumFoam()
    
    position = torch.tensor([4.0, 4.0, 4.0, 4.0], dtype=torch.float64)
    
    rho_flat = foam.compute_local_energy_density(position, metric_field_flat)
    rho_curved = foam.compute_local_energy_density(position, metric_field_curved)
    
    print(f"  Minkowski energy density: {rho_flat:.6f} rho_P")
    print(f"  Perturbed energy density: {rho_curved:.6f} rho_P")
    
    assert rho_flat < rho_curved, "Perturbed metric should have higher energy"
    print("\n[OK] Energy density computation working correctly")


def run_all_tests():
    """Run all unit tests"""
    print("\n" + "="*70)
    print("QUANTUM FOAM UNIT TESTS")
    print("="*70)
    
    tests = [
        test_foam_initialization,
        test_virtual_particle_creation,
        test_collapse_condition,
        test_singularity_formation,
        test_hawking_evaporation,
        test_softening_regularization,
        test_foam_evolution,
        test_energy_density_computation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\nX TEST FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\nX TEST ERROR: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\nALL TESTS PASSED!")
    else:
        print(f"\n{failed} test(s) failed")
    
    print("="*70 + "\n")
    
    return passed, failed


if __name__ == "__main__":
    run_all_tests()
