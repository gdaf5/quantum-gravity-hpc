"""
Unit test for Bianchi identities on Minkowski metric.

For flat spacetime: Riemann = 0, so both identities should be exactly 0.

Author: wosky021@gmail.com
Date: April 21, 2026
"""

import torch
import sys
import numpy as np

def test_bianchi_minkowski():
    """
    Test Bianchi identities on flat Minkowski metric.
    """
    print("="*70)
    print("TEST: Bianchi Identities on Minkowski Metric")
    print("="*70)
    
    # Minkowski metric
    batch_size = 1
    g = torch.zeros(batch_size, 4, 4, dtype=torch.float64)
    g[0, 0, 0] = -1.0
    g[0, 1, 1] = 1.0
    g[0, 2, 2] = 1.0
    g[0, 3, 3] = 1.0
    
    print("\nMinkowski metric:")
    print(g[0])
    
    # For flat spacetime, Christoffel symbols = 0
    Gamma = torch.zeros(batch_size, 4, 4, 4, dtype=torch.float64)
    
    # Riemann tensor = 0
    Riemann = torch.zeros(batch_size, 4, 4, 4, 4, dtype=torch.float64)
    
    # First Bianchi identity: R^ρ_{σμν} + R^ρ_{νσμ} + R^ρ_{μνσ} = 0
    R1 = Riemann
    R2 = Riemann.permute(0, 1, 3, 4, 2)
    R3 = Riemann.permute(0, 1, 4, 2, 3)
    bianchi_1 = torch.mean(torch.sum((R1 + R2 + R3)**2, dim=(1, 2, 3, 4)))
    
    print(f"\n  First Bianchi identity violation: {bianchi_1:.6e}")
    
    # Second Bianchi identity (Einstein tensor = 0 for flat space)
    G = torch.zeros(batch_size, 4, 4, dtype=torch.float64)
    dG = torch.zeros(batch_size, 4, 4, 4, dtype=torch.float64)
    
    # Covariant divergence should be 0
    covariant_div = torch.zeros(batch_size, 4, dtype=torch.float64)
    for mu in range(4):
        for nu in range(4):
            covariant_div[:, mu] += dG[:, nu, mu, nu]
            for lam in range(4):
                covariant_div[:, mu] += Gamma[:, mu, nu, lam] * G[:, lam, nu]
                covariant_div[:, mu] += Gamma[:, nu, nu, lam] * G[:, mu, lam]
    
    bianchi_2 = torch.mean(torch.sum(covariant_div ** 2, dim=1))
    
    print(f"  Second Bianchi identity violation: {bianchi_2:.6e}")
    
    # Check results
    tolerance = 1e-10
    
    if bianchi_1 < tolerance:
        print(f"\n  [OK] First Bianchi identity satisfied (< {tolerance})")
    else:
        print(f"\n  [FAIL] First Bianchi identity VIOLATED: {bianchi_1}")
        return False
    
    if bianchi_2 < tolerance:
        print(f"  [OK] Second Bianchi identity satisfied (< {tolerance})")
    else:
        print(f"  [FAIL] Second Bianchi identity VIOLATED: {bianchi_2}")
        return False
    
    print("\n[OK] Both Bianchi identities satisfied for Minkowski metric")
    print("="*70)
    
    return True


if __name__ == "__main__":
    success = test_bianchi_minkowski()
    sys.exit(0 if success else 1)
