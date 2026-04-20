# Testing and Validation Guide

## Quick Safety Check

**BEFORE running any simulations, run this:**

```bash
python safe_demo.py
```

This runs 6 minimal demos (~30 seconds total) to verify:
- ✓ Code works correctly
- ✓ Physics formulas are right
- ✓ Won't crash your computer

## Performance Benchmark

**To check how heavy the code is:**

```bash
python benchmark.py
```

This will:
- Test different configurations (tiny → medium)
- Measure time and memory usage
- Give safety recommendations
- Estimate large simulations WITHOUT running them

Expected results on average laptop:
- Tiny (10 particles): ~1-2 seconds, ~50 MB
- Small (50 particles): ~5-10 seconds, ~100 MB
- Medium (100 particles): ~20-30 seconds, ~200 MB

## Unit Tests

**To verify physics correctness:**

```bash
python test_physics.py
```

Tests include:
- ✓ Flat space → zero Christoffel symbols
- ✓ Minkowski metric → zero acceleration
- ✓ Schwarzschild radius r_s = 2M
- ✓ Hawking temperature T_H = 1/(8πM)
- ✓ Entropy scales as M² (area law)
- ✓ Evaporation time scales as M³

## What Each Test Does

### 1. safe_demo.py (RECOMMENDED FIRST)
**Purpose:** Verify code works without stress-testing your system

**What it does:**
- Creates tiny test cases (4x4x4x4 grid, 5-10 particles)
- Checks physics formulas match theory
- Takes ~30 seconds total
- Uses ~100 MB RAM

**Run this if:** You want to make sure everything works before running real simulations

### 2. test_physics.py
**Purpose:** Validate physics implementation against known solutions

**What it tests:**
- Geodesic equations in flat space
- Schwarzschild metric properties
- Hawking radiation formulas
- Quantum field vacuum fluctuations
- Testable predictions generation

**Run this if:** You want to verify the physics is implemented correctly

### 3. benchmark.py
**Purpose:** Measure performance and resource usage

**What it does:**
- Runs simulations of increasing size
- Monitors CPU and memory
- Estimates time for large runs
- Gives safety warnings

**Run this if:** You want to know if your computer can handle larger simulations

## Safety Levels

### 🟢 SAFE (Won't hurt your computer)
```bash
python safe_demo.py          # 30 seconds, 100 MB
python test_physics.py       # 1 minute, 200 MB
python hawking_radiation.py  # 5 seconds, 50 MB
python testable_predictions.py  # 10 seconds, 100 MB
```

### 🟡 MODERATE (May take a few minutes)
```bash
python main.py  # Default: 100 particles, 50 steps
                # ~1-2 minutes, ~500 MB
```

### 🔴 HEAVY (Only if you have time and resources)
```python
# Edit main.py and change parameters:
run_physical_simulation(
    n_particles=500,      # More particles
    n_steps=100,          # More steps
    use_einstein_solver=True  # VERY SLOW (30x slower)
)
# Estimated: 10-30 minutes, 2-4 GB RAM
```

## Understanding the Output

### Geodesic Integration
```
Step 10/50: <r> = 45.23 l_P, <v> = 0.0234 c
```
- `<r>`: Average distance from center in Planck lengths
- `<v>`: Average velocity as fraction of light speed

### Hawking Radiation
```
Temperature: 1.417e32 K
Evaporation time: 2.75e-39 s
```
- Temperature in Kelvin (extremely hot for small black holes)
- Evaporation time in seconds (very fast for Planck-mass BH)

### Testable Predictions
```
Cross-section modification: 0.0234%
Observable at LHC: YES ✓
```
- Shows if quantum gravity effects are detectable
- Compares with LHC, LIGO, CMB, EHT observations

## Troubleshooting

### "Out of memory"
**Solution:** Reduce parameters
```python
n_particles=10    # Instead of 100
grid_shape=(4,4,4,4)  # Instead of (8,8,8,8)
```

### "Taking too long"
**Solution:** Reduce steps or disable Einstein solver
```python
n_steps=10  # Instead of 50
use_einstein_solver=False  # Much faster
```

### "Tests failing"
**Possible causes:**
1. Missing dependencies: `pip install torch numpy h5py matplotlib scipy psutil`
2. Old PyTorch version: `pip install --upgrade torch`
3. Actual bug: Report to GitHub issues

## Validation Checklist

Before trusting results, verify:

- [ ] `safe_demo.py` passes all 6 demos
- [ ] `test_physics.py` passes all unit tests
- [ ] Hawking temperature matches T_H = 1/(8πM)
- [ ] Schwarzschild radius matches r_s = 2M
- [ ] Energy conservation < 1% drift
- [ ] ADM constraints satisfied (if using Einstein solver)

## Performance Tips

1. **Start small:** Always test with tiny parameters first
2. **Monitor resources:** Use `benchmark.py` to check before scaling up
3. **Disable Einstein solver:** Set `use_einstein_solver=False` for 30x speedup
4. **Use GPU:** If available, code will automatically use CUDA
5. **Reduce grid size:** (8,8,8,8) → (6,6,6,6) saves ~50% memory

## Expected Results

### Fractal Dimension
- Classical: D2 ≈ 3.0
- Quantum effects: D2 > 3.0 (typically 4-6)
- Strong quantum: D2 > 5.0

### Hawking Temperature (M = 1 m_P)
- T_H = 0.0398 T_P = 1.417 × 10³² K
- Extremely hot!

### Evaporation Time (M = 1 m_P)
- t_evap = 5120π ≈ 16,085 t_P
- ≈ 8.67 × 10⁻⁴⁰ seconds

### LHC Predictions
- Cross-section change: ~0.01-0.1% (if D2 ≈ 5)
- Mini-BH production: Only if E > E_Planck (not at LHC)

## Next Steps

After validation:

1. ✓ Run `safe_demo.py` - verify code works
2. ✓ Run `test_physics.py` - verify physics correct
3. ✓ Run `benchmark.py` - check performance
4. → Run `python main.py` - basic simulation
5. → Run `python hawking_radiation.py` - analyze black holes
6. → Run `python testable_predictions.py` - generate predictions
7. → Analyze results with `python advanced_analysis.py`

## Questions?

- Code not working? Run `safe_demo.py` first
- Too slow? Check `benchmark.py` recommendations
- Results look wrong? Verify with `test_physics.py`
- Want to scale up? Start small and monitor resources
