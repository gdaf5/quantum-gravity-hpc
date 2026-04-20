"""
Performance Benchmark and Resource Monitor
Measures CPU, memory usage, and execution time for different configurations.
"""

import torch
import numpy as np
import time
import psutil
import os
from typing import Dict, Tuple

class PerformanceBenchmark:
    """Monitor system resources and benchmark performance"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.results = []
    
    def get_memory_usage(self) -> Dict:
        """Get current memory usage in MB"""
        mem_info = self.process.memory_info()
        return {
            'rss_mb': mem_info.rss / 1024 / 1024,  # Resident Set Size
            'vms_mb': mem_info.vms / 1024 / 1024,  # Virtual Memory Size
        }
    
    def get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        return self.process.cpu_percent(interval=0.1)
    
    def benchmark_configuration(self, name: str, func, *args, **kwargs) -> Dict:
        """
        Benchmark a specific configuration.
        
        Args:
            name: configuration name
            func: function to benchmark
            *args, **kwargs: function arguments
        Returns:
            dict with timing and resource usage
        """
        print(f"\n{'='*70}")
        print(f"BENCHMARKING: {name}")
        print(f"{'='*70}")
        
        # Initial state
        mem_before = self.get_memory_usage()
        
        # Run and time
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Final state
        mem_after = self.get_memory_usage()
        cpu_usage = self.get_cpu_usage()
        
        # Memory delta
        mem_delta = mem_after['rss_mb'] - mem_before['rss_mb']
        
        benchmark_result = {
            'name': name,
            'success': success,
            'error': error,
            'time_seconds': elapsed,
            'memory_before_mb': mem_before['rss_mb'],
            'memory_after_mb': mem_after['rss_mb'],
            'memory_delta_mb': mem_delta,
            'cpu_percent': cpu_usage
        }
        
        self.results.append(benchmark_result)
        
        # Print results
        print(f"  Time: {elapsed:.2f} seconds")
        print(f"  Memory: {mem_after['rss_mb']:.1f} MB (Δ {mem_delta:+.1f} MB)")
        print(f"  CPU: {cpu_usage:.1f}%")
        print(f"  Status: {'✓ SUCCESS' if success else f'✗ FAILED: {error}'}")
        
        return benchmark_result
    
    def print_summary(self):
        """Print benchmark summary"""
        print("\n" + "="*70)
        print("PERFORMANCE SUMMARY")
        print("="*70)
        
        print(f"\n{'Configuration':<40} {'Time':<12} {'Memory':<15} {'Status'}")
        print("-"*70)
        
        for r in self.results:
            status = "✓" if r['success'] else "✗"
            print(f"{r['name']:<40} {r['time_seconds']:>8.2f}s   {r['memory_delta_mb']:>+8.1f} MB    {status}")
        
        # Safety recommendations
        print("\n" + "="*70)
        print("SAFETY RECOMMENDATIONS")
        print("="*70)
        
        max_time = max(r['time_seconds'] for r in self.results if r['success'])
        max_mem = max(r['memory_delta_mb'] for r in self.results if r['success'])
        
        if max_time < 10:
            print("  ✓ All configurations run quickly (< 10s)")
        elif max_time < 60:
            print("  ⚠️  Some configurations take 10-60s")
        else:
            print("  ⚠️  WARNING: Some configurations take > 1 minute")
        
        if max_mem < 500:
            print("  ✓ Memory usage is safe (< 500 MB)")
        elif max_mem < 2000:
            print("  ⚠️  Moderate memory usage (500-2000 MB)")
        else:
            print("  ⚠️  WARNING: High memory usage (> 2 GB)")
        
        print("\n  Safe to run on most computers: ", end="")
        if max_time < 60 and max_mem < 2000:
            print("YES ✓")
        else:
            print("NO ✗ - Use smaller configurations")


def benchmark_all_configurations():
    """Benchmark different simulation configurations"""
    
    print("="*70)
    print("QUANTUM GRAVITY PERFORMANCE BENCHMARK")
    print("="*70)
    print(f"System: {psutil.cpu_count()} CPUs, {psutil.virtual_memory().total / 1024**3:.1f} GB RAM")
    print("="*70)
    
    benchmark = PerformanceBenchmark()
    
    # Configuration 1: Tiny (safe for any computer)
    def tiny_simulation():
        from main import run_physical_simulation
        return run_physical_simulation(
            n_particles=10,
            n_steps=5,
            grid_shape=(4, 4, 4, 4),
            central_mass=0.1,
            use_einstein_solver=False
        )
    
    benchmark.benchmark_configuration(
        "Tiny (10 particles, 5 steps, 4x4x4x4)",
        tiny_simulation
    )
    
    # Configuration 2: Small (safe)
    def small_simulation():
        from main import run_physical_simulation
        return run_physical_simulation(
            n_particles=50,
            n_steps=10,
            grid_shape=(6, 6, 6, 6),
            central_mass=0.1,
            use_einstein_solver=False
        )
    
    benchmark.benchmark_configuration(
        "Small (50 particles, 10 steps, 6x6x6x6)",
        small_simulation
    )
    
    # Configuration 3: Medium (default)
    def medium_simulation():
        from main import run_physical_simulation
        return run_physical_simulation(
            n_particles=100,
            n_steps=20,
            grid_shape=(8, 8, 8, 8),
            central_mass=0.1,
            use_einstein_solver=False
        )
    
    benchmark.benchmark_configuration(
        "Medium (100 particles, 20 steps, 8x8x8x8)",
        medium_simulation
    )
    
    # Configuration 4: Hawking radiation (fast)
    def hawking_test():
        from hawking_radiation import HawkingRadiation
        hawking = HawkingRadiation()
        results = []
        for M in [0.1, 1.0, 10.0]:
            results.append(hawking.analyze_black_hole(M))
        return results
    
    benchmark.benchmark_configuration(
        "Hawking Radiation Analysis",
        hawking_test
    )
    
    # Configuration 5: Testable predictions (fast)
    def predictions_test():
        from testable_predictions import TestablePredictions
        predictor = TestablePredictions()
        return predictor.generate_full_report({
            'fractal_dimension': 5.752,
            'vacuum_energy': 1e-120
        })
    
    benchmark.benchmark_configuration(
        "Testable Predictions Generation",
        predictions_test
    )
    
    # Configuration 6: Quantum field (moderate)
    def quantum_field_test():
        from quantum_field import QuantumFieldCurvedSpace
        field = QuantumFieldCurvedSpace(grid_shape=(6, 6, 6, 6), field_mass=1.0)
        
        # Compute vacuum expectation
        vev = field.compute_vacuum_expectation_value()
        return vev
    
    benchmark.benchmark_configuration(
        "Quantum Field VEV Calculation",
        quantum_field_test
    )
    
    # Print summary
    benchmark.print_summary()
    
    return benchmark


def estimate_large_simulation():
    """Estimate resources for large simulation WITHOUT running it"""
    print("\n" + "="*70)
    print("LARGE SIMULATION ESTIMATES (NOT RUN)")
    print("="*70)
    
    configs = [
        ("Large", 500, 50, (10, 10, 10, 10), False),
        ("Very Large", 1000, 100, (12, 12, 12, 12), False),
        ("With Einstein Solver", 100, 20, (8, 8, 8, 8), True),
    ]
    
    print(f"\n{'Configuration':<30} {'Est. Time':<15} {'Est. Memory':<15} {'Safe?'}")
    print("-"*70)
    
    for name, n_particles, n_steps, grid_shape, use_solver in configs:
        # Rough estimates based on complexity
        grid_size = np.prod(grid_shape)
        
        # Time estimate (very rough)
        base_time = 0.1  # seconds per step per 100 particles
        time_est = base_time * n_steps * (n_particles / 100)
        
        if use_solver:
            time_est *= 30  # Einstein solver is ~30x slower
        
        # Memory estimate
        base_mem = 50  # MB base
        particle_mem = n_particles * 0.001  # ~1 KB per particle
        grid_mem = grid_size * 16 * 8 / 1024 / 1024  # 16 floats (4x4 metric) * 8 bytes
        
        mem_est = base_mem + particle_mem + grid_mem
        
        # Safety check
        safe = time_est < 300 and mem_est < 4000  # 5 min, 4 GB
        
        print(f"{name:<30} {time_est:>10.1f}s      {mem_est:>10.1f} MB      {'✓' if safe else '✗ RISKY'}")
    
    print("\n⚠️  These are ESTIMATES. Actual performance may vary.")
    print("    Start with small configurations and scale up gradually.")


if __name__ == "__main__":
    # Run benchmarks
    benchmark = benchmark_all_configurations()
    
    # Show estimates for large configs
    estimate_large_simulation()
    
    print("\n" + "="*70)
    print("BENCHMARK COMPLETE")
    print("="*70)
    print("\nRecommendation: Start with 'Tiny' or 'Small' configuration")
    print("and monitor your system resources before scaling up.")
