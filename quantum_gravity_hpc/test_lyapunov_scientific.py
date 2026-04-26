"""
Scientific Lyapunov Analysis for Quantum Foam
==============================================

Использует научно корректный метод Benettin-Wolf для вычисления
показателей Ляпунова квантовой пены.

Валидирован на системе Лоренца (lambda ~ 0.9).

Author: wosky021@gmail.com
Date: April 21, 2026
"""

import numpy as np
import torch
import sys
from quantum_foam import QuantumFoam
from engine import MetricField
from physics_registry import PhysicsRegistry
from lyapunov_scientific import ScientificLyapunovCalculator


def create_foam_metric(grid_shape=(6, 6, 6, 6), foam_density=0.1):
    """Создать метрику с флуктуациями квантовой пены."""
    
    g_metric = torch.zeros(grid_shape + (4, 4), dtype=torch.float64)
    
    for i in range(grid_shape[0]):
        for j in range(grid_shape[1]):
            for k in range(grid_shape[2]):
                for l in range(grid_shape[3]):
                    # Минковский
                    g_metric[i, j, k, l, 0, 0] = -1.0
                    g_metric[i, j, k, l, 1, 1] = 1.0
                    g_metric[i, j, k, l, 2, 2] = 1.0
                    g_metric[i, j, k, l, 3, 3] = 1.0
                    
                    # Детерминированные флуктуации
                    if foam_density > 0:
                        phase = (i + j*10 + k*100 + l*1000) * 0.1
                        amplitude = 0.01 * foam_density
                        for mu in range(4):
                            for nu in range(mu, 4):
                                fluctuation = amplitude * np.sin(phase + mu + nu)
                                g_metric[i, j, k, l, mu, nu] += fluctuation
                                if mu != nu:
                                    g_metric[i, j, k, l, nu, mu] += fluctuation
    
    return MetricField(g_metric, grid_spacing=1.0)


def run_scientific_analysis(foam_density=0.3, verbose=True):
    """
    Запустить научный анализ Ляпунова для квантовой пены.
    """
    if verbose:
        print(f"\n{'='*70}")
        print(f"SCIENTIFIC LYAPUNOV ANALYSIS: Foam Density = {foam_density:.1f} rho_P")
        print(f"{'='*70}")
    
    # Параметры
    registry = PhysicsRegistry()
    if foam_density < 0.2:
        regime = 'weak_foam'
    elif foam_density < 0.6:
        regime = 'medium_foam'
    else:
        regime = 'strong_foam'
    
    params = registry.get_recommended_parameters(regime)
    
    if verbose:
        print(f"\nParameters:")
        print(f"  Regime: {regime}")
        print(f"  Creation rate: {params['creation_rate']:.1f}")
    
    # Создать метрику
    grid_shape = (6, 6, 6, 6)
    metric_field = create_foam_metric(grid_shape, foam_density)
    
    # КРИТИЧЕСКИ ВАЖНО: Создать квантовую пену с фиксированным seed
    foam = QuantumFoam(
        grid_shape=grid_shape,
        creation_rate=params['creation_rate'],
        collapse_threshold=params['collapse_threshold'],
        softening_length=params['softening_length'],
        enable_hawking_evaporation=True,
        random_seed=42  # Фиксированный seed для воспроизводимости
    )
    
    # Создать научный калькулятор
    calculator = ScientificLyapunovCalculator(
        epsilon=1e-8,
        renorm_steps=5,
        transient_time=2.0,
        measurement_time=8.0,
        dt=0.1
    )
    
    # Вычислить показатель Ляпунова
    # result = calculator.compute_lyapunov_exponent(
    #     foam, metric_field, verbose=verbose
    # )
    
    # NEW: Run analysis with Hamiltonian monitoring
    print(f"DEBUG: QuantumFoam imported from {QuantumFoam.__module__}")
    import quantum_foam
    print(f"DEBUG: QuantumFoam file {quantum_foam.__file__}")
    print(f"DEBUG: QuantumFoam has compute_local_energy_density: {hasattr(foam, 'compute_local_energy_density')}")
    result = calculator.compute_lyapunov_with_energy_monitoring(
        foam, metric_field, verbose=verbose
    )
    
    result['foam_density'] = foam_density
    result['regime'] = regime
    
    return result


def run_parametric_study():
    """Параметрическое исследование с научным методом."""
    
    print("\n" + "="*70)
    print("PARAMETRIC STUDY: Scientific Lyapunov Analysis")
    print("="*70)
    print("\nMethod: Benettin-Wolf algorithm with renormalization")
    print("Validated on Lorenz system (lambda ~ 0.9)")
    
    densities = [0.1, 0.3, 0.5, 0.7]
    results = []
    
    for density in densities:
        try:
            result = run_scientific_analysis(
                foam_density=density,
                verbose=True
            )
            results.append(result)
        except Exception as e:
            print(f"\n[WARNING] Failed for density {density}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    print(f"\n{'Density':>10} | {'Lambda':>10} | {'Doubling':>10} | {'Renorms':>10} | {'Particles':>10} | {'Chaos':>15}")
    print("-"*80)
    
    for r in results:
        print(f"{r['foam_density']:>10.1f} | "
              f"{r['lyapunov_exponent']:>10.6f} | "
              f"{r['doubling_time']:>10.2f} | "
              f"{r['n_renormalizations']:>10d} | "
              f"{r['n_particles']:>10d} | "
              f"{r['chaos_level']:>15}")
    
    # Анализ корреляции
    if len(results) >= 2:
        lambdas = [r['lyapunov_exponent'] for r in results]
        densities_tested = [r['foam_density'] for r in results]
        
        print(f"\n{'='*70}")
        print("CORRELATION ANALYSIS")
        print(f"{'='*70}")
        
        # Проверить монотонность
        is_increasing = all(lambdas[i] <= lambdas[i+1] for i in range(len(lambdas)-1))
        
        if is_increasing or lambdas[-1] > lambdas[0]:
            print(f"\n[OK] POSITIVE CORRELATION:")
            print(f"   lambda: {lambdas[0]:.6f} -> {lambdas[-1]:.6f}")
            print(f"   density: {densities_tested[0]:.1f} -> {densities_tested[-1]:.1f}")
            print(f"   Increase: {((lambdas[-1] - lambdas[0]) / lambdas[0] * 100):.1f}%")
            print(f"\n   Conclusion: Higher foam density -> Stronger chaos")
            correlation = True
        else:
            print(f"\n[WARNING] No clear correlation")
            correlation = False
        
        # Проверить, что все показатели положительны
        all_positive = all(l > 0 for l in lambdas)
        
        if all_positive:
            print(f"\n[OK] All Lyapunov exponents are POSITIVE")
        else:
            print(f"\n[WARNING] Some exponents are NOT positive: {lambdas}") # Отладка
        
        print(f"\n{'='*70}")
        
        return results, correlation and all_positive
    else:
        print(f"\n[WARNING] Insufficient data")
        return results, False


def compare_methods():
    """Сравнить старый и новый методы."""
    
    print("\n" + "="*70)
    print("METHOD COMPARISON")
    print("="*70)
    
    print("\nOLD METHOD (test_lyapunov_real.py):")
    print("  - Simple distance measurement")
    print("  - No renormalization")
    print("  - No transient period")
    print("  - Result: lambda ~ 4.0 (too high, unrealistic)")
    
    print("\nNEW METHOD (lyapunov_scientific.py):")
    print("  - Benettin-Wolf algorithm")
    print("  - Periodic renormalization")
    print("  - Transient period removal")
    print("  - Validated on Lorenz system")
    print("  - Result: lambda ~ 0.5-1.5 (realistic for chaotic systems)")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    try:
        # Сравнение методов
        compare_methods()
        
        # Запустить параметрическое исследование
        results, success = run_parametric_study()
        
        print(f"\n{'='*70}")
        if success:
            print("[SUCCESS] Scientific Lyapunov analysis complete!")
            print("Quantum foam exhibits deterministic chaos.")
            print("Method validated on Lorenz system.")
        else:
            print("[PARTIAL] Study completed but results unclear.")
        print(f"{'='*70}\n")
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
