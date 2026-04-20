# Quantum Gravity HPC - Build Instructions

## Quick Start (Numba - 5-10x speedup)

Already integrated! Just install:
```bash
pip install numba
```

The engine will automatically use Numba acceleration.

## C++ Backend (20-50x speedup)

### Windows

1. Install Visual Studio Build Tools or Visual Studio with C++ support
2. Install dependencies:
```bash
pip install pybind11
```

3. Build:
```bash
python setup.py build_ext --inplace
```

### Linux/Mac

1. Install compiler:
```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# Mac
xcode-select --install
```

2. Install dependencies:
```bash
pip install pybind11
```

3. Build:
```bash
python setup.py build_ext --inplace
```

## Performance Comparison

Run benchmark:
```bash
python test_performance.py
```

Expected results:
- Pure Python: 1.0x (baseline)
- Numba: 5-10x faster
- C++: 20-50x faster

## Usage

The engine automatically selects the fastest available backend:
1. C++ (if compiled)
2. Numba (if installed)
3. Pure Python (fallback)

No code changes needed!
