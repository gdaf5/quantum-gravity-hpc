"""
Performance Benchmark: Python vs Numba vs C++
Compare different backend implementations
"""

import numpy as np
import time
import sys

print("="*70)
print("QUANTUM GRAVITY ENGINE - PERFORMANCE BENCHMARK")
print("="*70)

# Test Numba availability
try:
    from numba import njit
    NUMBA_AVAILABLE = True
    print("[+] Numba available")
except ImportError:
    NUMBA_AVAILABLE = False
    print("[-] Numba not available")

# Test C++ backend availability
try:
    import geodesic_cpp
    CPP_AVAILABLE = True
    print("[+] C++ backend available")
except ImportError:
    CPP_AVAILABLE = False
    print("[-] C++ backend not available (run: python setup.py build_ext --inplace)")

print()

# Create test data
N = 100  # particles
print(f"Test configuration: {N} particles")
print()

# Generate random metric tensors
g_batch = np.random.randn(N, 4, 4)
for n in range(N):
    g_batch[n] = (g_batch[n] + g_batch[n].T) / 2  # Make symmetric
    g_batch[n] += np.eye(4) * 5  # Make positive definite

# Generate random metric derivatives
dg_batch = np.random.randn(N, 4, 4, 4) * 0.01

print("Testing Christoffel symbol computation...")
print("-" * 70)

# Pure Python implementation
def compute_christoffel_python(g_batch, dg_batch):
    N = g_batch.shape[0]
    Gamma = np.zeros((N, 4, 4, 4))
    
    for n in range(N):
        g_inv = np.linalg.inv(g_batch[n])
        
        for sigma in range(4):
            for mu in range(4):
                for nu in range(4):
                    for rho in range(4):
                        Gamma[n, sigma, mu, nu] += 0.5 * g_inv[sigma, rho] * \
                            (dg_batch[n, mu, rho, nu] + dg_batch[n, nu, rho, mu] - dg_batch[n, rho, mu, nu])
    
    return Gamma

# Benchmark Python
print("\n1. Pure Python:")
start = time.time()
for _ in range(5):
    result_python = compute_christoffel_python(g_batch, dg_batch)
python_time = (time.time() - start) / 5
print(f"   Time: {python_time:.4f} seconds")
print(f"   Speed: 1.0x (baseline)")

# Benchmark Numba
if NUMBA_AVAILABLE:
    from engine import _compute_christoffel_numba
    
    print("\n2. Numba JIT:")
    # Warm up
    _ = _compute_christoffel_numba(g_batch[:10], dg_batch[:10])
    
    start = time.time()
    for _ in range(5):
        result_numba = _compute_christoffel_numba(g_batch, dg_batch)
    numba_time = (time.time() - start) / 5
    speedup = python_time / numba_time
    print(f"   Time: {numba_time:.4f} seconds")
    print(f"   Speed: {speedup:.1f}x faster")
    
    # Verify correctness
    error = np.max(np.abs(result_python - result_numba))
    print(f"   Error vs Python: {error:.2e}")

# Benchmark C++
if CPP_AVAILABLE:
    print("\n3. C++ Backend:")
    start = time.time()
    for _ in range(5):
        result_cpp = geodesic_cpp.compute_christoffel_batch(g_batch, dg_batch)
    cpp_time = (time.time() - start) / 5
    speedup = python_time / cpp_time
    print(f"   Time: {cpp_time:.4f} seconds")
    print(f"   Speed: {speedup:.1f}x faster")
    
    # Verify correctness
    error = np.max(np.abs(result_python - result_cpp))
    print(f"   Error vs Python: {error:.2e}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)

if NUMBA_AVAILABLE:
    numba_speedup = python_time / numba_time
    print(f"Numba speedup: {numba_speedup:.1f}x")

if CPP_AVAILABLE:
    cpp_speedup = python_time / cpp_time
    print(f"C++ speedup: {cpp_speedup:.1f}x")

print("\nProjected performance for 1000 particles, 500 steps:")
print("-" * 70)

# Estimate total time
steps = 500
particles = 1000
scale_factor = (particles / N) ** 2  # Roughly quadratic scaling

python_total = python_time * steps * scale_factor
print(f"Pure Python: {python_total/3600:.1f} hours")

if NUMBA_AVAILABLE:
    numba_total = numba_time * steps * scale_factor
    print(f"Numba: {numba_total/60:.1f} minutes ({numba_total/3600:.1f} hours)")

if CPP_AVAILABLE:
    cpp_total = cpp_time * steps * scale_factor
    print(f"C++: {cpp_total/60:.1f} minutes ({cpp_total/3600:.1f} hours)")

print("\n" + "="*70)
print("RECOMMENDATION")
print("="*70)

if CPP_AVAILABLE:
    print("[+] Use C++ backend for maximum performance (20-50x speedup)")
elif NUMBA_AVAILABLE:
    print("[+] Use Numba for good performance (5-10x speedup)")
    print("  Install C++ backend for even better performance:")
    print("  pip install pybind11")
    print("  python setup.py build_ext --inplace")
else:
    print("[!] Install Numba for 5-10x speedup:")
    print("  pip install numba")
    print("  Or install C++ backend for 20-50x speedup:")
    print("  pip install pybind11")
    print("  python setup.py build_ext --inplace")

print("="*70)
