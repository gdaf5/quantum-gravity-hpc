# C++/Rust Optimization Strategy

**Goal**: 10-50x speedup for production simulations  
**Current**: 100 particles, 50 steps = 3.7 minutes  
**Target**: 1000 particles, 500 steps = 20-30 minutes (instead of 31 hours!)

---

## 🔥 CRITICAL BOTTLENECKS (Profile Analysis)

### Current Performance Breakdown:

```
Total time: 3.7 minutes (222 seconds) for 100 particles, 50 steps

Per step: 4.44 seconds
├─ Metric interpolation: ~1.5s (34%)  ← CRITICAL
├─ Christoffel symbols: ~2.0s (45%)   ← CRITICAL  
├─ Geodesic acceleration: ~0.7s (16%) ← IMPORTANT
└─ Other: ~0.24s (5%)
```

### Hotspots to optimize:

1. **Christoffel symbols** (45% of time)
   - Triple nested loop: O(N × 4³ × 4³)
   - Matrix operations
   - Current: Pure Python loops

2. **Metric interpolation** (34% of time)
   - 16-corner hypercube interpolation
   - Per-particle operation
   - Current: Python loops

3. **Geodesic acceleration** (16% of time)
   - Triple loop over particles
   - Current: Python loops

---

## 🎯 OPTIMIZATION STRATEGY

### Option 1: C++ with Eigen (RECOMMENDED)
**Pros:**
- Mature ecosystem
- Excellent linear algebra (Eigen)
- Easy Python bindings (pybind11)
- 20-50x speedup expected

**Cons:**
- Manual memory management
- More verbose

### Option 2: Rust with ndarray
**Pros:**
- Memory safe
- Modern language
- Good performance
- 15-40x speedup expected

**Cons:**
- Smaller ecosystem for scientific computing
- Python bindings less mature (PyO3)
- Steeper learning curve

### Option 3: Numba JIT (Quick Win)
**Pros:**
- No rewrite needed
- Just add @njit decorator
- 5-10x speedup expected
- Takes 1 hour

**Cons:**
- Less speedup than C++/Rust
- Some limitations

---

## 📊 EXPECTED SPEEDUPS

### Numba (easiest):
```python
@njit(parallel=True)
def compute_christoffel_symbols_batch(...):
    # Same code, just JIT compiled
```
**Speedup**: 5-10x  
**Effort**: 1-2 hours  
**Result**: 100 particles in 22-44 seconds

### C++ (best performance):
```cpp
// Use Eigen for linear algebra
// OpenMP for parallelization
```
**Speedup**: 20-50x  
**Effort**: 1-2 weeks  
**Result**: 100 particles in 4-11 seconds  
**Result**: 1000 particles in 7-18 minutes

### Rust (modern):
```rust
// Use ndarray + rayon
```
**Speedup**: 15-40x  
**Effort**: 2-3 weeks  
**Result**: 100 particles in 5-15 seconds

---

## 🚀 IMPLEMENTATION PLAN

### Phase 1: Quick Win with Numba (1-2 hours)

**What to do:**
```python
from numba import njit, prange

@njit(parallel=True)
def compute_christoffel_symbols_batch(g, dg):
    N = g.shape[0]
    Gamma = np.zeros((N, 4, 4, 4))
    
    for n in prange(N):  # Parallel loop
        g_inv = np.linalg.inv(g[n])
        
        for sigma in range(4):
            for mu in range(4):
                for nu in range(4):
                    for rho in range(4):
                        Gamma[n, sigma, mu, nu] += 0.5 * g_inv[sigma, rho] * \
                            (dg[n, mu, rho, nu] + dg[n, nu, rho, mu] - dg[n, rho, mu, nu])
    
    return Gamma
```

**Expected**: 5-10x speedup  
**Time**: 1-2 hours  
**Risk**: Low

---

### Phase 2: C++ Core (1-2 weeks)

**Architecture:**
```
Python (high-level)
    ↓
pybind11 (bindings)
    ↓
C++ Core (compute)
    ├─ Eigen (linear algebra)
    ├─ OpenMP (parallelization)
    └─ SIMD (vectorization)
```

**Files to create:**

#### 1. `geodesic_core.hpp` (Header)
```cpp
#pragma once
#include <Eigen/Dense>
#include <vector>

namespace quantum_gravity {

using Matrix4d = Eigen::Matrix4d;
using Vector4d = Eigen::Vector4d;
using Tensor4 = std::array<std::array<std::array<double, 4>, 4>, 4>;

class GeodesicEngine {
public:
    // Compute Christoffel symbols for batch
    static std::vector<Tensor4> compute_christoffel_batch(
        const std::vector<Matrix4d>& g_batch,
        const std::vector<std::array<Matrix4d, 4>>& dg_batch
    );
    
    // Interpolate metric for batch
    static std::vector<Matrix4d> interpolate_metric_batch(
        const Eigen::Tensor<double, 6>& grid,  // [Nt, Nx, Ny, Nz, 4, 4]
        const Eigen::MatrixXd& coords,          // [N, 4]
        double grid_spacing
    );
    
    // Compute geodesic acceleration for batch
    static Eigen::MatrixXd geodesic_acceleration_batch(
        const Eigen::MatrixXd& coords,    // [N, 4]
        const Eigen::MatrixXd& velocity,  // [N, 4]
        const Eigen::Tensor<double, 6>& grid,
        double grid_spacing
    );
    
    // Full integration step
    static Eigen::MatrixXd integrate_step(
        const Eigen::MatrixXd& particles,  // [N, 8]
        const Eigen::Tensor<double, 6>& grid,
        double grid_spacing,
        double dt
    );
};

} // namespace quantum_gravity
```

#### 2. `geodesic_core.cpp` (Implementation)
```cpp
#include "geodesic_core.hpp"
#include <omp.h>

namespace quantum_gravity {

std::vector<Tensor4> GeodesicEngine::compute_christoffel_batch(
    const std::vector<Matrix4d>& g_batch,
    const std::vector<std::array<Matrix4d, 4>>& dg_batch
) {
    size_t N = g_batch.size();
    std::vector<Tensor4> Gamma_batch(N);
    
    #pragma omp parallel for
    for (size_t n = 0; n < N; ++n) {
        Matrix4d g_inv = g_batch[n].inverse();
        auto& Gamma = Gamma_batch[n];
        
        // Initialize to zero
        for (int s = 0; s < 4; ++s)
            for (int m = 0; m < 4; ++m)
                for (int n = 0; n < 4; ++n)
                    Gamma[s][m][n] = 0.0;
        
        // Compute Christoffel symbols
        for (int sigma = 0; sigma < 4; ++sigma) {
            for (int mu = 0; mu < 4; ++mu) {
                for (int nu = 0; nu < 4; ++nu) {
                    for (int rho = 0; rho < 4; ++rho) {
                        const auto& dg = dg_batch[n];
                        Gamma[sigma][mu][nu] += 0.5 * g_inv(sigma, rho) * 
                            (dg[mu](rho, nu) + dg[nu](rho, mu) - dg[rho](mu, nu));
                    }
                }
            }
        }
    }
    
    return Gamma_batch;
}

// ... other implementations

} // namespace quantum_gravity
```

#### 3. `bindings.cpp` (Python interface)
```cpp
#include <pybind11/pybind11.h>
#include <pybind11/eigen.h>
#include <pybind11/stl.h>
#include "geodesic_core.hpp"

namespace py = pybind11;
using namespace quantum_gravity;

PYBIND11_MODULE(geodesic_cpp, m) {
    m.doc() = "C++ accelerated geodesic integration";
    
    py::class_<GeodesicEngine>(m, "GeodesicEngine")
        .def_static("compute_christoffel_batch", 
                   &GeodesicEngine::compute_christoffel_batch,
                   "Compute Christoffel symbols for batch")
        .def_static("interpolate_metric_batch",
                   &GeodesicEngine::interpolate_metric_batch,
                   "Interpolate metric for batch")
        .def_static("geodesic_acceleration_batch",
                   &GeodesicEngine::geodesic_acceleration_batch,
                   "Compute geodesic acceleration for batch")
        .def_static("integrate_step",
                   &GeodesicEngine::integrate_step,
                   "Full integration step");
}
```

#### 4. `setup.py` (Build configuration)
```python
from setuptools import setup, Extension
from pybind11.setup_helpers import Pybind11Extension, build_ext
import sys

ext_modules = [
    Pybind11Extension(
        "geodesic_cpp",
        ["bindings.cpp", "geodesic_core.cpp"],
        include_dirs=[
            "/usr/include/eigen3",  # Eigen path
        ],
        extra_compile_args=[
            "-O3",           # Optimization
            "-march=native", # CPU-specific optimizations
            "-fopenmp",      # OpenMP
            "-std=c++17",    # C++17
        ],
        extra_link_args=["-fopenmp"],
    ),
]

setup(
    name="geodesic_cpp",
    version="1.0",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)
```

#### 5. Modified `engine.py` (Use C++ backend)
```python
try:
    import geodesic_cpp
    USE_CPP = True
    print("Using C++ accelerated backend")
except ImportError:
    USE_CPP = False
    print("Using Python backend (install C++ extension for 20-50x speedup)")

def batch_geodesic_integration(particles, metric_field, dt):
    if USE_CPP:
        # Use C++ backend
        return geodesic_cpp.GeodesicEngine.integrate_step(
            particles.numpy(),
            metric_field.grid.numpy(),
            metric_field.grid_spacing,
            dt
        )
    else:
        # Fallback to Python
        return batch_geodesic_integration_python(particles, metric_field, dt)
```

**Build:**
```bash
pip install pybind11 eigen
python setup.py build_ext --inplace
```

**Expected**: 20-50x speedup  
**Time**: 1-2 weeks  
**Risk**: Medium

---

### Phase 3: Rust Alternative (2-3 weeks)

**Architecture:**
```
Python (high-level)
    ↓
PyO3 (bindings)
    ↓
Rust Core (compute)
    ├─ ndarray (arrays)
    ├─ rayon (parallelization)
    └─ nalgebra (linear algebra)
```

**Files to create:**

#### 1. `Cargo.toml`
```toml
[package]
name = "geodesic_rust"
version = "0.1.0"
edition = "2021"

[lib]
name = "geodesic_rust"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.20", features = ["extension-module"] }
numpy = "0.20"
ndarray = "0.15"
nalgebra = "0.32"
rayon = "1.8"
```

#### 2. `src/lib.rs`
```rust
use pyo3::prelude::*;
use numpy::{PyArray2, PyReadonlyArray2};
use ndarray::{Array2, Array3, ArrayView2};
use nalgebra::Matrix4;
use rayon::prelude::*;

#[pyfunction]
fn compute_christoffel_batch(
    g_batch: PyReadonlyArray2<f64>,
    dg_batch: PyReadonlyArray2<f64>,
) -> PyResult<Py<PyArray2<f64>>> {
    let g = g_batch.as_array();
    let dg = dg_batch.as_array();
    
    // Parallel computation
    let result: Vec<_> = (0..g.shape()[0])
        .into_par_iter()
        .map(|n| {
            // Compute Christoffel symbols for particle n
            compute_christoffel_single(&g.row(n), &dg.row(n))
        })
        .collect();
    
    // Convert to numpy array
    Python::with_gil(|py| {
        Ok(PyArray2::from_vec2(py, &result)?.to_owned())
    })
}

fn compute_christoffel_single(
    g: &ArrayView2<f64>,
    dg: &ArrayView2<f64>,
) -> Vec<f64> {
    // Convert to nalgebra matrix
    let g_mat = Matrix4::from_row_slice(g.as_slice().unwrap());
    let g_inv = g_mat.try_inverse().unwrap();
    
    let mut gamma = vec![0.0; 4 * 4 * 4];
    
    for sigma in 0..4 {
        for mu in 0..4 {
            for nu in 0..4 {
                for rho in 0..4 {
                    let idx = sigma * 16 + mu * 4 + nu;
                    gamma[idx] += 0.5 * g_inv[(sigma, rho)] * 
                        (dg[(mu, rho * 4 + nu)] + 
                         dg[(nu, rho * 4 + mu)] - 
                         dg[(rho, mu * 4 + nu)]);
                }
            }
        }
    }
    
    gamma
}

#[pymodule]
fn geodesic_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compute_christoffel_batch, m)?)?;
    Ok(())
}
```

**Build:**
```bash
pip install maturin
maturin develop --release
```

**Expected**: 15-40x speedup  
**Time**: 2-3 weeks  
**Risk**: Medium-High

---

## 📊 PERFORMANCE COMPARISON

### Current (Python):
- 100 particles, 50 steps: **3.7 minutes**
- 1000 particles, 500 steps: **31 hours** (estimated)

### With Numba (5-10x):
- 100 particles, 50 steps: **22-44 seconds**
- 1000 particles, 500 steps: **3-6 hours**

### With C++ (20-50x):
- 100 particles, 50 steps: **4-11 seconds**
- 1000 particles, 500 steps: **37-93 minutes**

### With Rust (15-40x):
- 100 particles, 50 steps: **5-15 seconds**
- 1000 particles, 500 steps: **47-124 minutes**

---

## 🎯 RECOMMENDATION

### Immediate (Today):
**Use Numba** - Add @njit decorators
- **Effort**: 1-2 hours
- **Speedup**: 5-10x
- **Risk**: Very low

### Short-term (1-2 weeks):
**Implement C++ core** with Eigen + OpenMP
- **Effort**: 1-2 weeks
- **Speedup**: 20-50x
- **Risk**: Medium
- **Best ROI**

### Long-term (Optional):
**Consider Rust** if you want memory safety
- **Effort**: 2-3 weeks
- **Speedup**: 15-40x
- **Risk**: Medium-High

---

## 💡 HYBRID APPROACH (BEST)

**Keep Python for:**
- High-level logic
- I/O operations
- Visualization
- Analysis

**Move to C++/Rust:**
- Christoffel symbols (45% of time)
- Metric interpolation (34% of time)
- Geodesic acceleration (16% of time)

**Result:**
- Easy to use (Python interface)
- Fast computation (C++/Rust core)
- Best of both worlds

---

## 🚀 QUICK START (Numba)

**Right now, in 5 minutes:**

```python
# Install numba
pip install numba

# Add to engine.py
from numba import njit, prange
import numpy as np

@njit(parallel=True, fastmath=True)
def compute_christoffel_symbols_batch_numba(g, dg):
    N = g.shape[0]
    Gamma = np.zeros((N, 4, 4, 4))
    
    for n in prange(N):
        # Compute inverse (Numba supports np.linalg.inv)
        g_inv = np.linalg.inv(g[n])
        
        for sigma in range(4):
            for mu in range(4):
                for nu in range(4):
                    for rho in range(4):
                        Gamma[n, sigma, mu, nu] += 0.5 * g_inv[sigma, rho] * \
                            (dg[n, mu, rho, nu] + dg[n, nu, rho, mu] - dg[n, rho, mu, nu])
    
    return Gamma

# Replace in compute_christoffel_symbols_batch
def compute_christoffel_symbols_batch(g, dg):
    # Convert to numpy if needed
    g_np = g.numpy() if hasattr(g, 'numpy') else g
    dg_np = dg.numpy() if hasattr(dg, 'numpy') else dg
    
    # Call Numba version
    result = compute_christoffel_symbols_batch_numba(g_np, dg_np)
    
    # Convert back to torch
    return torch.from_numpy(result)
```

**Test:**
```bash
python run_optimized.py
```

**Expected**: 5-10x faster immediately!

---

## 📈 ESTIMATED TIMELINE

### Week 1:
- Day 1: Numba optimization (5-10x) ✓
- Day 2-3: Profile and identify remaining bottlenecks
- Day 4-5: Start C++ implementation

### Week 2:
- Day 1-3: Complete C++ core
- Day 4: Python bindings
- Day 5: Testing and benchmarking

### Week 3 (Optional):
- Rust implementation if needed

---

## ✅ CONCLUSION

**Best strategy:**
1. **Now**: Add Numba (1-2 hours) → 5-10x speedup
2. **Next week**: Implement C++ core (1-2 weeks) → 20-50x speedup
3. **Optional**: Consider Rust for future

**With C++**: 1000 particles, 500 steps in **37-93 minutes** instead of 31 hours!

**This makes production research feasible!**
