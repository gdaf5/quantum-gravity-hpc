# Quick Start Guide

## ⚠️ IMPORTANT: Before Running Anything

### Step 1: Check Your Python Environment

Open a **regular Windows Command Prompt** (not PowerShell, not Git Bash) and run:

```cmd
python --version
python -m pip list
```

You should see:
- Python 3.8 or higher
- torch, numpy, h5py, scipy, matplotlib installed

### Step 2: Install Dependencies (if needed)

```cmd
pip install torch numpy h5py matplotlib scipy psutil
```

### Step 3: Run Safety Check

```cmd
cd quantum_gravity_hpc
python safe_demo.py
```

**Expected output:** 6 demos pass in ~30 seconds

## What to Expect

### Safe Demo (safe_demo.py)
- **Time:** ~30 seconds
- **Memory:** ~100 MB
- **CPU:** Low
- **Safe:** ✓ YES - Won't hurt your computer

### Unit Tests (test_physics.py)
- **Time:** ~1 minute
- **Memory:** ~200 MB
- **CPU:** Low-Medium
- **Safe:** ✓ YES

### Benchmark (benchmark.py)
- **Time:** ~2-5 minutes
- **Memory:** ~500 MB peak
- **CPU:** Medium
- **Safe:** ✓ YES - Monitors resources

### Basic Simulation (main.py)
- **Time:** ~1-2 minutes (default settings)
- **Memory:** ~500 MB
- **CPU:** Medium-High
- **Safe:** ⚠️ MODERATE - Monitor your system

## Performance Estimates

### Your Computer Can Handle:

**🟢 SAFE (Recommended to start):**
```python
# In main.py, use these settings:
n_particles=10
n_steps=5
grid_shape=(4, 4, 4, 4)
use_einstein_solver=False
# Time: ~5 seconds, Memory: ~50 MB
```

**🟡 MODERATE (Default):**
```python
n_particles=100
n_steps=50
grid_shape=(8, 8, 8, 8)
use_einstein_solver=False
# Time: ~1-2 minutes, Memory: ~500 MB
```

**🔴 HEAVY (Only if you have time):**
```python
n_particles=500
n_steps=100
grid_shape=(10, 10, 10, 10)
use_einstein_solver=False
# Time: ~10-20 minutes, Memory: ~2 GB
```

**🔴🔴 VERY HEAVY (Research-grade):**
```python
n_particles=100
n_steps=50
grid_shape=(8, 8, 8, 8)
use_einstein_solver=True  # ← This makes it 30x slower!
# Time: ~30-60 minutes, Memory: ~2-4 GB
```

## Understanding Results

### When You Run safe_demo.py

You should see:
```
✓ Particles moved in straight lines (flat space)
✓ Schwarzschild metric looks correct
✓ Hawking radiation formulas correct
✓ Predictions generated
✓ Quantum field initialized with vacuum fluctuations
✓ Simulation completed successfully

DEMO SUMMARY
Passed: 6/6
✓ ALL DEMOS PASSED - Code is working!
```

### When You Run main.py

You'll see output like:
```
PHYSICAL QUANTUM GRAVITY SIMULATION
Particles: 100
Steps: 50
Grid: (8, 8, 8, 8)

Starting integration...
  Step 0/50: <r> = 50.23 l_P, <v> = 0.0123 c
  Step 10/50: <r> = 52.45 l_P, <v> = 0.0145 c
  ...
  Step 50/50: <r> = 67.89 l_P, <v> = 0.0234 c

SIMULATION COMPLETE
Output: physical_simulation.h5
```

**What this means:**
- `<r>`: Average distance of particles from center (in Planck lengths)
- `<v>`: Average velocity (as fraction of speed of light)
- Particles are spreading out due to quantum effects

### When You Run hawking_radiation.py

```
Black Hole: M = 1.0 m_P
  Schwarzschild radius: 2.00 l_P
  Hawking temperature: 1.417e+32 K
  Evaporation time: 8.67e-40 s
  Entropy: 50.27 k_B
```

**What this means:**
- Small black holes are EXTREMELY hot
- They evaporate VERY quickly
- Entropy follows Bekenstein-Hawking formula S = A/4

## Troubleshooting

### "ModuleNotFoundError: No module named 'torch'"

**Solution:** Install dependencies
```cmd
pip install torch numpy h5py matplotlib scipy psutil
```

### "Out of memory"

**Solution:** Reduce parameters in main.py
```python
n_particles=10  # Instead of 100
grid_shape=(4,4,4,4)  # Instead of (8,8,8,8)
```

### "Process taking too long"

**Solution:** 
1. Reduce `n_steps` (50 → 10)
2. Make sure `use_einstein_solver=False`
3. Use smaller grid

### "Results look wrong"

**Check:**
1. Did `safe_demo.py` pass all tests?
2. Are you using Planck units correctly?
3. Is fractal dimension D2 > 3? (Expected for quantum effects)

## What Each File Does

| File | Purpose | Time | Safe? |
|------|---------|------|-------|
| `safe_demo.py` | Verify code works | 30s | ✓ |
| `test_physics.py` | Test physics formulas | 1min | ✓ |
| `benchmark.py` | Measure performance | 2-5min | ✓ |
| `main.py` | Run simulation | 1-60min | ⚠️ |
| `hawking_radiation.py` | Analyze black holes | 5s | ✓ |
| `testable_predictions.py` | Generate predictions | 10s | ✓ |
| `advanced_analysis.py` | Analyze results | 30s | ✓ |

## Recommended Workflow

1. **First time:**
   ```cmd
   python safe_demo.py
   ```
   Make sure all 6 demos pass!

2. **Check performance:**
   ```cmd
   python benchmark.py
   ```
   See how long things take on your computer.

3. **Run basic simulation:**
   ```cmd
   python main.py
   ```
   Uses default safe settings.

4. **Analyze black holes:**
   ```cmd
   python hawking_radiation.py
   ```
   Fast and interesting!

5. **Get predictions:**
   ```cmd
   python testable_predictions.py
   ```
   Compare with experiments.

## Summary

✅ **Start with:** `safe_demo.py` (30 seconds, totally safe)

✅ **Then try:** `hawking_radiation.py` (5 seconds, very cool results)

✅ **Then try:** `testable_predictions.py` (10 seconds, see LHC/LIGO predictions)

⚠️ **Finally:** `main.py` (1-2 minutes, monitor your system)

🔴 **Advanced:** Edit `main.py` to use Einstein solver (30-60 minutes!)

---

**Questions?** Check TESTING.md for detailed guide.

**Problems?** Make sure dependencies are installed and you're using regular Windows Command Prompt.
