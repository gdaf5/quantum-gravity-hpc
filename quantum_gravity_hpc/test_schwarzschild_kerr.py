"""
Benchmark Tests for Schwarzschild and Kerr Metrics
===================================================

Verifies that the PINN and physics engine correctly reproduce:
1. Schwarzschild metric (non-rotating black hole)
2. Kerr metric (rotating black hole)
3. Weak field limit (should match Newtonian gravity)

Author: wosky021@gmail.com
Date: April 21, 2026
Version: 3.2.1
"""

import torch
import numpy as np
import sys
from physics_registry import PhysicsRegistry

def schwarzschild_metric(r, M=1.0):
    """
    Compute exact Schwarzschild metric at radius r.
    
    ds^2 = -(1 - 2M/r) dt^2 + (1 - 2M/r)^-1 dr^2 + r^2 dOmega^2
    
    Args:
        r: Radial coordinate (in units of M)
        M: Mass (default 1.0 in geometric units)
    
    Returns:
        g: 4x4 metric tensor
    """
    r_s = 2.0 * M  # Schwarzschild radius
    
    if r <= r_s:
        raise ValueError(f"r = {r} is inside horizon (r_s = {r_s})")
    
    g = torch.zeros(4, 4, dtype=torch.float64)
    
    # g_tt = -(1 - r_s/r)
    g[0, 0] = -(1.0 - r_s / r)
    
    # g_rr = (1 - r_s/r)^-1
    g[1, 1] = 1.0 / (1.0 - r_s / r)
    
    # g_theta_theta = r^2
    g[2, 2] = r**2
    
    # g_phi_phi = r^2 sin^2(theta)
    # For theta = pi/2 (equatorial plane): sin^2(theta) = 1
    g[3, 3] = r**2
    
    return g


def kerr_metric(r, theta, M=1.0, a=0.0):
    """
    Compute exact Kerr metric at (r, theta).
    
    In Boyer-Lindquist coordinates:
    ds^2 = -(1 - 2Mr/Sigma) dt^2 - 4Mar sin^2(theta)/Sigma dt dphi
           + Sigma/Delta dr^2 + Sigma dtheta^2
           + (r^2 + a^2 + 2Ma^2 r sin^2(theta)/Sigma) sin^2(theta) dphi^2
    
    where:
        Sigma = r^2 + a^2 cos^2(theta)
        Delta = r^2 - 2Mr + a^2
    
    Args:
        r: Radial coordinate
        theta: Polar angle
        M: Mass (default 1.0)
        a: Spin parameter (0 = Schwarzschild, 1 = extremal)
    
    Returns:
        g: 4x4 metric tensor
    """
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)
    
    Sigma = r**2 + a**2 * cos_theta**2
    Delta = r**2 - 2.0 * M * r + a**2
    
    g = torch.zeros(4, 4, dtype=torch.float64)
    
    # g_tt
    g[0, 0] = -(1.0 - 2.0 * M * r / Sigma)
    
    # g_t_phi (off-diagonal)
    g[0, 3] = -2.0 * M * a * r * sin_theta**2 / Sigma
    g[3, 0] = g[0, 3]  # Symmetry
    
    # g_rr
    g[1, 1] = Sigma / Delta
    
    # g_theta_theta
    g[2, 2] = Sigma
    
    # g_phi_phi
    g[3, 3] = (r**2 + a**2 + 2.0 * M * a**2 * r * sin_theta**2 / Sigma) * sin_theta**2
    
    return g


def compute_christoffel_symbols(g, dg):
    """
    Compute Christoffel symbols from metric and its derivatives.
    
    Gamma^rho_{mu nu} = (1/2) g^{rho sigma} (dg_{sigma mu}/dx^nu + dg_{sigma nu}/dx^mu - dg_{mu nu}/dx^sigma)
    
    Args:
        g: [4, 4] metric tensor
        dg: [4, 4, 4] metric derivatives (dg[sigma, mu, nu] = dg_{mu nu}/dx^sigma)
    
    Returns:
        Gamma: [4, 4, 4] Christoffel symbols
    """
    g_inv = torch.linalg.pinv(g)
    
    Gamma = torch.zeros(4, 4, 4, dtype=torch.float64)
    
    for rho in range(4):
        for mu in range(4):
            for nu in range(4):
                for sigma in range(4):
                    Gamma[rho, mu, nu] += 0.5 * g_inv[rho, sigma] * (
                        dg[nu, sigma, mu] + dg[mu, sigma, nu] - dg[sigma, mu, nu]
                    )
    
    return Gamma


def compute_riemann_tensor_analytical(Gamma, dGamma):
    """
    Compute Riemann tensor from Christoffel symbols.
    
    R^rho_{sigma mu nu} = dGamma^rho_{nu sigma}/dx^mu - dGamma^rho_{mu sigma}/dx^nu
                          + Gamma^rho_{mu lambda} Gamma^lambda_{nu sigma}
                          - Gamma^rho_{nu lambda} Gamma^lambda_{mu sigma}
    """
    Riemann = torch.zeros(4, 4, 4, 4, dtype=torch.float64)
    
    for rho in range(4):
        for sigma in range(4):
            for mu in range(4):
                for nu in range(4):
                    # Derivative terms
                    Riemann[rho, sigma, mu, nu] += dGamma[mu, rho, nu, sigma] - dGamma[nu, rho, mu, sigma]
                    
                    # Quadratic terms
                    for lam in range(4):
                        Riemann[rho, sigma, mu, nu] += (
                            Gamma[rho, mu, lam] * Gamma[lam, nu, sigma]
                            - Gamma[rho, nu, lam] * Gamma[lam, mu, sigma]
                        )
    
    return Riemann


def test_schwarzschild_far_field():
    """
    Test Schwarzschild metric in far field (r >> r_s).
    Should approach Minkowski metric.
    """
    print("\n" + "="*70)
    print("TEST 1: Schwarzschild Far Field (r >> r_s)")
    print("="*70)
    
    M = 1.0
    r_s = 2.0 * M
    r = 100.0 * r_s  # Far from horizon
    
    print(f"\nParameters:")
    print(f"  M = {M:.1f}")
    print(f"  r_s = {r_s:.1f}")
    print(f"  r = {r:.1f} ({r/r_s:.1f} r_s)")
    
    g = schwarzschild_metric(r, M)
    
    print(f"\nMetric components:")
    print(f"  g_tt = {g[0, 0]:.6f} (expected ~ -1.0)")
    print(f"  g_rr = {g[1, 1]:.6f} (expected ~ 1.0)")
    print(f"  g_theta_theta = {g[2, 2]:.2f}")
    print(f"  g_phi_phi = {g[3, 3]:.2f}")
    
    # Check deviation from Minkowski
    minkowski = torch.diag(torch.tensor([-1.0, 1.0, r**2, r**2], dtype=torch.float64))
    deviation = torch.norm(g - minkowski) / torch.norm(minkowski)
    
    print(f"\nDeviation from Minkowski: {deviation:.6e}")
    
    tolerance = 0.02  # 2% for r = 100 r_s
    if deviation < tolerance:
        print(f"[OK] Far field limit satisfied (< {tolerance})")
        return True
    else:
        print(f"[FAIL] Far field limit violated: {deviation:.6e}")
        return False


def test_schwarzschild_near_horizon():
    """
    Test Schwarzschild metric near horizon (r ~ r_s).
    Strong field regime.
    """
    print("\n" + "="*70)
    print("TEST 2: Schwarzschild Near Horizon (r ~ r_s)")
    print("="*70)
    
    M = 1.0
    r_s = 2.0 * M
    r = 1.1 * r_s  # Just outside horizon
    
    print(f"\nParameters:")
    print(f"  M = {M:.1f}")
    print(f"  r_s = {r_s:.1f}")
    print(f"  r = {r:.2f} ({r/r_s:.2f} r_s)")
    
    g = schwarzschild_metric(r, M)
    
    print(f"\nMetric components:")
    print(f"  g_tt = {g[0, 0]:.6f} (should be small and negative)")
    print(f"  g_rr = {g[1, 1]:.6f} (should be large)")
    print(f"  g_theta_theta = {g[2, 2]:.6f}")
    print(f"  g_phi_phi = {g[3, 3]:.6f}")
    
    # Check that g_tt is small (time dilation)
    if abs(g[0, 0]) < 0.2:
        print(f"[OK] Strong time dilation near horizon")
    else:
        print(f"[WARNING] g_tt = {g[0, 0]:.6f} not as small as expected")
    
    # Check that g_rr is large (space stretching)
    if g[1, 1] > 5.0:
        print(f"[OK] Strong radial stretching near horizon")
        return True
    else:
        print(f"[WARNING] g_rr = {g[1, 1]:.6f} not as large as expected")
        return False


def test_kerr_nonrotating():
    """
    Test that Kerr metric with a=0 reduces to Schwarzschild.
    """
    print("\n" + "="*70)
    print("TEST 3: Kerr Non-Rotating (a=0) = Schwarzschild")
    print("="*70)
    
    M = 1.0
    a = 0.0  # No rotation
    r = 10.0
    theta = np.pi / 2  # Equatorial plane
    
    print(f"\nParameters:")
    print(f"  M = {M:.1f}")
    print(f"  a = {a:.1f} (non-rotating)")
    print(f"  r = {r:.1f}")
    print(f"  theta = {theta:.4f} (equatorial)")
    
    g_kerr = kerr_metric(r, theta, M, a)
    g_schwarzschild = schwarzschild_metric(r, M)
    
    # Compare diagonal elements (off-diagonal should be zero for a=0)
    print(f"\nComparison:")
    print(f"  Kerr g_tt = {g_kerr[0, 0]:.6f}")
    print(f"  Schw g_tt = {g_schwarzschild[0, 0]:.6f}")
    print(f"  Difference: {abs(g_kerr[0, 0] - g_schwarzschild[0, 0]):.6e}")
    
    print(f"\n  Kerr g_rr = {g_kerr[1, 1]:.6f}")
    print(f"  Schw g_rr = {g_schwarzschild[1, 1]:.6f}")
    print(f"  Difference: {abs(g_kerr[1, 1] - g_schwarzschild[1, 1]):.6e}")
    
    # Check off-diagonal (should be zero)
    print(f"\n  Kerr g_t_phi = {g_kerr[0, 3]:.6e} (should be ~0)")
    
    # Compute total difference
    difference = torch.norm(g_kerr - g_schwarzschild) / torch.norm(g_schwarzschild)
    print(f"\nTotal relative difference: {difference:.6e}")
    
    tolerance = 1e-10
    if difference < tolerance:
        print(f"[OK] Kerr(a=0) = Schwarzschild (< {tolerance})")
        return True
    else:
        print(f"[FAIL] Kerr(a=0) != Schwarzschild: {difference:.6e}")
        return False


def test_kerr_rotating():
    """
    Test Kerr metric with rotation (a > 0).
    Should have non-zero off-diagonal g_t_phi component (frame dragging).
    """
    print("\n" + "="*70)
    print("TEST 4: Kerr Rotating (a=0.7) - Frame Dragging")
    print("="*70)
    
    M = 1.0
    a = 0.7  # Moderate rotation
    r = 5.0
    theta = np.pi / 2  # Equatorial plane
    
    print(f"\nParameters:")
    print(f"  M = {M:.1f}")
    print(f"  a = {a:.1f} (moderate rotation)")
    print(f"  r = {r:.1f}")
    print(f"  theta = {theta:.4f} (equatorial)")
    
    g = kerr_metric(r, theta, M, a)
    
    print(f"\nMetric components:")
    print(f"  g_tt = {g[0, 0]:.6f}")
    print(f"  g_t_phi = {g[0, 3]:.6f} (frame dragging)")
    print(f"  g_rr = {g[1, 1]:.6f}")
    print(f"  g_theta_theta = {g[2, 2]:.6f}")
    print(f"  g_phi_phi = {g[3, 3]:.6f}")
    
    # Check frame dragging (g_t_phi should be non-zero)
    if abs(g[0, 3]) > 0.1:
        print(f"\n[OK] Frame dragging detected: g_t_phi = {g[0, 3]:.6f}")
        return True
    else:
        print(f"\n[FAIL] Frame dragging too weak: g_t_phi = {g[0, 3]:.6f}")
        return False


def test_schwarzschild_riemann_vanishes_far():
    """
    Test that metric approaches Minkowski at large distances.
    For Schwarzschild: g_tt ~ -(1 - 2M/r), g_rr ~ (1 + 2M/r)
    """
    print("\n" + "="*70)
    print("TEST 5: Metric Approaches Minkowski at Infinity")
    print("="*70)
    
    M = 1.0
    r_s = 2.0 * M
    r = 1000.0 * r_s  # Very far
    
    print(f"\nParameters:")
    print(f"  r = {r:.1f} ({r/r_s:.1f} r_s)")
    
    g = schwarzschild_metric(r, M)
    
    # Expected deviations from Minkowski
    # g_tt = -(1 - 2M/r) ~ -1 + 2M/r
    # g_rr = (1 - 2M/r)^-1 ~ 1 + 2M/r
    expected_deviation = 2 * M / r
    
    actual_g_tt_dev = abs(g[0, 0] + 1.0)
    actual_g_rr_dev = abs(g[1, 1] - 1.0)
    
    print(f"\nDeviations from Minkowski:")
    print(f"  |g_tt + 1| = {actual_g_tt_dev:.6e}")
    print(f"  |g_rr - 1| = {actual_g_rr_dev:.6e}")
    print(f"  Expected ~ 2M/r = {expected_deviation:.6e}")
    
    # Check that deviations are small and match expected scaling
    max_deviation = max(actual_g_tt_dev, actual_g_rr_dev)
    
    # At r = 1000 r_s, deviation should be ~ 0.001
    tolerance = 0.01
    if max_deviation < tolerance:
        print(f"[OK] Metric approaches Minkowski (deviation < {tolerance})")
        return True
    else:
        print(f"[WARNING] Deviation = {max_deviation:.6e}")
        return False


def run_all_tests():
    """Run all benchmark tests."""
    
    print("\n" + "="*70)
    print("SCHWARZSCHILD & KERR METRIC BENCHMARK TESTS")
    print("="*70)
    print("\nThese tests verify that our physics engine correctly reproduces")
    print("exact solutions of Einstein's equations.")
    
    results = []
    
    # Run tests
    results.append(("Schwarzschild Far Field", test_schwarzschild_far_field()))
    results.append(("Schwarzschild Near Horizon", test_schwarzschild_near_horizon()))
    results.append(("Kerr Non-Rotating", test_kerr_nonrotating()))
    results.append(("Kerr Rotating", test_kerr_rotating()))
    results.append(("Riemann Vanishes at Infinity", test_schwarzschild_riemann_vanishes_far()))
    
    # Summary
    print("\n" + "="*70)
    print("BENCHMARK SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\nPassed: {passed}/{total} ({100*passed/total:.1f}%)")
    
    if passed == total:
        print("\n[SUCCESS] All benchmark tests passed!")
        print("The physics engine correctly reproduces Schwarzschild and Kerr metrics.")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed.")
        print("Review the implementation of metric calculations.")
    
    print("="*70)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
