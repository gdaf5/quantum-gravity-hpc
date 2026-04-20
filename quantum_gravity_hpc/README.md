# Quantum Gravity HPC Simulation

High-performance simulation of quantum gravity at Planck scale.

## Overview

Numerical simulation of quantum-metric fluctuations in 4D spacetime, modeling virtual singularities and non-local quantum states.

## Quick Start

### Installation

```bash
pip install torch numpy h5py matplotlib scipy
```

For GPU acceleration:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### Basic Usage

```bash
# Run basic simulation (100 particles, 5 steps)
python main.py

# Run ensemble simulation (1000 particles, 100 steps)
python ensemble_simulator.py ensemble

# Analyze results
python advanced_analysis.py cluster_experiment.h5
```

## Project Structure

```
quantum_gravity_hpc/
├── engine.py                      # Differentiable engine with Christoffel symbols
├── main.py                        # Basic HPC simulation
├── ensemble_simulator.py          # Ensemble simulation + back-reaction
├── advanced_analysis.py           # Advanced analysis with metrics
├── adm_metric_evolution.py        # ADM formalism implementation
├── quantum_entanglement_geometry.py  # Entanglement entropy analysis
├── quantum_thermodynamics.py      # Thermodynamic properties
├── self_consistent_gravity.py     # Self-consistent gravity solver
├── theoretical_comparison.py      # Comparison with theoretical models
└── run_all_experiments.py         # Run complete experiment suite
```

## Key Features

### Physics Implementation

- **Geodesic integration** in stochastic spacetime using Velocity Verlet
- **Christoffel symbols** computed via automatic differentiation
- **Back-reaction effects** through simplified Einstein equations
- **ADM formalism** for metric evolution
- **Quantum entanglement** geometry analysis

### Analysis Metrics

1. **Fractal Dimension (D2)**: Measures non-local quantum effects
   - D2 ≈ 3.0: classical behavior
   - D2 > 3.0: non-local quantum effects
   
2. **Lyapunov Exponent (λ)**: Chaotic dynamics indicator
   - λ > 0: chaotic dynamics
   - λ ≈ 0: regular motion

3. **Quantum Diffusion**: Velocity dispersion growth
4. **Energy Conservation**: Numerical stability check
5. **Phase Space Volume**: Liouville theorem verification

## Simulation Modes

| Mode | Particles | Steps | Back-reaction | Time (CPU) |
|------|-----------|-------|---------------|------------|
| Basic | 100 | 5 | No | ~1 sec |
| Ensemble | 1000 | 100 | No | ~30 sec |
| Back-reaction | 500 | 50 | Yes | ~60 sec |

## Physical Parameters

- **Planck length**: l_P = 1.616 × 10⁻³⁵ m
- **Planck time**: t_P = 5.39 × 10⁻⁴⁴ s
- **Integration step**: dt = 10⁻⁴⁵ s (0.1 t_P)
- **Grid size**: 8×8×8×8 (4096 cells)
- **Fluctuation amplitude**: 0.05 (5% of Minkowski metric)

## Advanced Experiments

```bash
# Run all experiments
python run_all_experiments.py

# Individual experiments
python ensemble_simulator.py ensemble
python ensemble_simulator.py backreaction
python ensemble_simulator.py compare

# Theoretical comparisons
python theoretical_comparison.py
python quantum_thermodynamics.py
```

## Output Files

- `*.h5` - Simulation data (HDF5 format)
- `analysis_results/*.png` - Visualization plots
- `analysis_report.json` - Numerical metrics

## License

Academic use. For publications, coordination required.
