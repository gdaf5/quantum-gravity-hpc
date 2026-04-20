"""
Numba-Accelerated Engine - Quick 5-10x Speedup
Just add @njit decorators to hot loops
"""

import torch
import numpy as np
from numba import njit, prange

# Numba-accelerated Christoffel symbols computation
@njit(parallel=True, fastmath=True, cache=True)
def compute_christoffel_numba(g_batch, dg_batch):
    """
    Compute Christoffel symbols with Numba JIT.
    
    Args:
        g_batch: [N, 4, 4] numpy array
        dg_batch: [N, 4, 4, 4] numpy array
    Returns:
        Gamma: [N, 4, 4, 4] numpy array
    """
    N = g_batch.shape[0]
    Gamma = np.zeros((N, 4, 4, 4), dtype=np.float64)
    
    for n in prange(N):  # Parallel loop
        # Compute inverse
        g_inv = np.linalg.inv(g_batch[n])
        
        # Compute Christoffel symbols
        for sigma in range(4):
            for mu in range(4):
                for nu in range(4):
                    for rho in range(4):
                        Gamma[n, sigma, mu, nu] += 0.5 * g_inv[sigma, rho] * \
                            (dg_batch[n, mu, rho, nu] + 
                             dg_batch[n, nu, rho, mu] - 
                             dg_batch[n, rho, mu, nu])
    
    return Gamma


# Numba-accelerated geodesic acceleration
@njit(parallel=True, fastmath=True, cache=True)
def geodesic_acceleration_numba(Gamma, velocity):
    """
    Compute geodesic acceleration with Numba JIT.
    
    Args:
        Gamma: [N, 4, 4, 4] numpy array
        velocity: [N, 4] numpy array
    Returns:
        accel: [N, 4] numpy array
    """
    N = Gamma.shape[0]
    accel = np.zeros((N, 4), dtype=np.float64)
    
    for n in prange(N):  # Parallel loop
        for sigma in range(4):
            for mu in range(4):
                for nu in range(4):
                    accel[n, sigma] -= Gamma[n, sigma, mu, nu] * \
                                      velocity[n, mu] * velocity[n, nu]
    
    return accel


# Test function
def test_numba_speedup():
    """Test Numba speedup vs pure Python"""
    import time
    
    print("="*70)
    print("NUMBA SPEEDUP TEST")
    print("="*70)
    
    # Create test data
    N = 100
    g_batch = np.random.randn(N, 4, 4)
    # Make symmetric
    for n in range(N):
        g_batch[n] = (g_batch[n] + g_batch[n].T) / 2
        g_batch[n] += np.eye(4) * 5  # Make positive definite
    
    dg_batch = np.random.randn(N, 4, 4, 4) * 0.01
    
    print(f"\nTest data: {N} particles")
    
    # Warm up Numba (first call compiles)
    print("\nWarming up Numba (compiling)...")
    _ = compute_christoffel_numba(g_batch[:10], dg_batch[:10])
    print("Compilation done!")
    
    # Benchmark Numba
    print("\nBenchmarking Numba version...")
    start = time.time()
    for _ in range(10):
        Gamma_numba = compute_christoffel_numba(g_batch, dg_batch)
    numba_time = (time.time() - start) / 10
    
    print(f"Numba time: {numba_time:.4f} seconds per iteration")
    
    # Benchmark Python (from engine.py)
    print("\nBenchmarking Python version...")
    from engine import compute_christoffel_symbols_batch
    
    g_torch = torch.from_numpy(g_batch)
    dg_torch = torch.from_numpy(dg_batch)
    
    start = time.time()
    for _ in range(10):
        Gamma_python = compute_christoffel_symbols_batch(g_torch, dg_torch)
    python_time = (time.time() - start) / 10
    
    print(f"Python time: {python_time:.4f} seconds per iteration")
    
    # Compare
    speedup = python_time / numba_time
    
    print("\n" + "="*70)
    print(f"SPEEDUP: {speedup:.1f}x faster with Numba!")
    print("="*70)
    
    if speedup > 3:
        print("\n[SUCCESS] Significant speedup achieved!")
    else:
        print("\n[WARNING] Speedup lower than expected")
    
    return speedup


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    speedup = test_numba_speedup()
    
    print(f"\n\nEstimated simulation time with Numba:")
    print(f"  100 particles, 50 steps: {3.7 * 60 / speedup:.1f} seconds")
    print(f"  1000 particles, 500 steps: {3.7 * 60 * 100 / speedup / 60:.1f} minutes")
