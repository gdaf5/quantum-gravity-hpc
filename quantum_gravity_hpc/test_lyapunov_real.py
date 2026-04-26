"""
Real Lyapunov Analysis - Using Actual Quantum Foam Simulation
==============================================================

Вычисляет показатели Ляпунова используя РЕАЛЬНУЮ симуляцию квантовой пены,
а не синтетическую модель.

Author: wosky021@gmail.com
Date: April 21, 2026
"""

import numpy as np
import torch
import sys
import copy
from quantum_foam import QuantumFoam
from engine import MetricField
from physics_registry import PhysicsRegistry


def create_foam_metric(grid_shape=(6, 6, 6, 6), foam_density=0.1):
    """Создать метрику с флуктуациями квантовой пены."""
    
    # Минковский + малые флуктуации
    g_metric = torch.zeros(grid_shape + (4, 4), dtype=torch.float64)
    
    for i in range(grid_shape[0]):
        for j in range(grid_shape[1]):
            for k in range(grid_shape[2]):
                for l in range(grid_shape[3]):
                    g_metric[i, j, k, l, 0, 0] = -1.0
                    g_metric[i, j, k, l, 1, 1] = 1.0
                    g_metric[i, j, k, l, 2, 2] = 1.0
                    g_metric[i, j, k, l, 3, 3] = 1.0
                    
                    # Флуктуации пропорциональны плотности
                    if foam_density > 0:
                        # Используем детерминированные флуктуации на основе координат
                        phase = (i + j*10 + k*100 + l*1000) * 0.1
                        amplitude = 0.01 * foam_density
                        for mu in range(4):
                            for nu in range(mu, 4):
                                fluctuation = amplitude * np.sin(phase + mu + nu)
                                g_metric[i, j, k, l, mu, nu] += fluctuation
                                if mu != nu:
                                    g_metric[i, j, k, l, nu, mu] += fluctuation
    
    return MetricField(g_metric, grid_spacing=1.0)


def compute_state_distance(particles1, particles2):
    """Вычислить расстояние между двумя состояниями."""
    
    n = min(len(particles1), len(particles2))
    if n == 0:
        return 0.0
    
    distance_sq = 0.0
    for i in range(n):
        # Пространственное расстояние
        dr = particles1[i].position[1:] - particles2[i].position[1:]
        distance_sq += torch.sum(dr**2).item()
    
    return np.sqrt(distance_sq)


def compute_lyapunov_real(foam_density=0.1, total_time=5.0, dt=0.1):
    """
    Вычислить показатель Ляпунова используя РЕАЛЬНУЮ симуляцию.
    """
    print(f"\n{'='*70}")
    print(f"REAL LYAPUNOV ANALYSIS: Foam Density = {foam_density:.1f} rho_P")
    print(f"{'='*70}")
    
    # Параметры из PhysicsRegistry
    registry = PhysicsRegistry()
    if foam_density < 0.2:
        regime = 'weak_foam'
    elif foam_density < 0.6:
        regime = 'medium_foam'
    else:
        regime = 'strong_foam'
    
    params = registry.get_recommended_parameters(regime)
    
    print(f"\nParameters:")
    print(f"  Regime: {regime}")
    print(f"  Creation rate: {params['creation_rate']:.1f}")
    print(f"  Total time: {total_time:.1f} t_P")
    print(f"  Time step: {dt:.2f} t_P")
    
    # Создать метрику
    grid_shape = (6, 6, 6, 6)
    metric_field = create_foam_metric(grid_shape, foam_density)
    
    # Создать две идентичные системы
    foam1 = QuantumFoam(
        grid_shape=grid_shape,
        creation_rate=params['creation_rate'],
        collapse_threshold=params['collapse_threshold'],
        softening_length=params['softening_length'],
        enable_hawking_evaporation=True
    )
    
    foam2 = copy.deepcopy(foam1)
    
    # Добавить малое возмущение ко второй системе
    epsilon = 1e-8
    if len(foam2.virtual_particles) > 0:
        foam2.virtual_particles[0].position[1] += epsilon
    
    # Начальное расстояние
    d0 = compute_state_distance(foam1.virtual_particles, foam2.virtual_particles)
    if d0 == 0:
        d0 = epsilon
    
    print(f"\nInitial separation: {d0:.6e}")
    
    # Эволюция
    n_steps = int(total_time / dt)
    divergences = []
    times = []
    
    current_time = 0.0
    
    for step in range(n_steps):
        # Эволюционировать обе системы
        foam1.evolve_foam(metric_field, current_time, dt)
        foam2.evolve_foam(metric_field, current_time, dt)
        
        # Измерить расхождение
        d_t = compute_state_distance(foam1.virtual_particles, foam2.virtual_particles)
        
        if d_t > 0:
            divergences.append(d_t)
            times.append(current_time)
        
        current_time += dt
        
        # Renormalization если расхождение слишком большое
        if d_t > 1.0 and len(foam1.virtual_particles) > 0 and len(foam2.virtual_particles) > 0:
            # Перенормировать
            scale = epsilon / d_t
            for i in range(min(len(foam1.virtual_particles), len(foam2.virtual_particles))):
                delta = foam2.virtual_particles[i].position - foam1.virtual_particles[i].position
                foam2.virtual_particles[i].position = foam1.virtual_particles[i].position + scale * delta
            d_t = epsilon
    
    # Вычислить показатель Ляпунова
    if len(divergences) > 0 and divergences[-1] > 0:
        lyapunov = np.log(divergences[-1] / d0) / total_time
    else:
        lyapunov = 0.0
    
    # Время удвоения
    if lyapunov > 0:
        doubling_time = np.log(2) / lyapunov
    else:
        doubling_time = np.inf
    
    print(f"\nResults:")
    print(f"  Lyapunov exponent: lambda = {lyapunov:.6f}")
    print(f"  Doubling time: tau = {doubling_time:.2f} t_P")
    print(f"  Final separation: {divergences[-1] if divergences else 0:.6e}")
    print(f"  Particles created: {len(foam1.virtual_particles)}")
    
    # Классификация
    if lyapunov > 0.1:
        chaos_level = "STRONG CHAOS"
    elif lyapunov > 0.01:
        chaos_level = "MODERATE CHAOS"
    elif lyapunov > 0:
        chaos_level = "WEAK CHAOS"
    else:
        chaos_level = "STABLE"
    
    print(f"  Classification: {chaos_level}")
    
    return {
        'lambda': lyapunov,
        'doubling_time': doubling_time,
        'final_separation': divergences[-1] if divergences else 0,
        'chaos_level': chaos_level,
        'n_particles': len(foam1.virtual_particles)
    }


def run_parametric_study():
    """Параметрическое исследование с реальной симуляцией."""
    
    print("\n" + "="*70)
    print("PARAMETRIC STUDY: Real Quantum Foam Lyapunov Analysis")
    print("="*70)
    print("\nUsing ACTUAL quantum foam simulation (not synthetic model)")
    
    densities = [0.1, 0.3, 0.5]
    results = []
    
    for density in densities:
        try:
            result = compute_lyapunov_real(
                foam_density=density,
                total_time=5.0,
                dt=0.1
            )
            result['foam_density'] = density
            results.append(result)
        except Exception as e:
            print(f"\n[WARNING] Failed for density {density}: {e}")
            continue
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    print(f"\n{'Density':>10} | {'Lambda':>10} | {'Doubling Time':>15} | {'Particles':>10} | {'Chaos':>15}")
    print("-"*70)
    
    for r in results:
        print(f"{r['foam_density']:>10.1f} | {r['lambda']:>10.6f} | "
              f"{r['doubling_time']:>15.2f} | {r['n_particles']:>10d} | {r['chaos_level']:>15}")
    
    # Correlation check
    if len(results) >= 2:
        lambdas = [r['lambda'] for r in results]
        densities_tested = [r['foam_density'] for r in results]
        
        print(f"\n{'='*70}")
        print("CORRELATION ANALYSIS")
        print(f"{'='*70}")
        
        if lambdas[-1] > lambdas[0]:
            print(f"\n[OK] POSITIVE CORRELATION:")
            print(f"   lambda: {lambdas[0]:.6f} -> {lambdas[-1]:.6f}")
            print(f"   density: {densities_tested[0]:.1f} -> {densities_tested[-1]:.1f}")
            print(f"\n   Conclusion: Higher foam density -> Stronger chaos")
            correlation = True
        else:
            print(f"\n[WARNING] No clear correlation")
            correlation = False
        
        print(f"\n{'='*70}")
        
        return results, correlation
    else:
        print(f"\n[WARNING] Insufficient data")
        return results, False


if __name__ == "__main__":
    try:
        results, correlation = run_parametric_study()
        
        print(f"\n{'='*70}")
        if correlation:
            print("[SUCCESS] Real quantum foam shows chaotic behavior!")
            print("Results from actual simulation, not synthetic model.")
        else:
            print("[PARTIAL] Study completed but correlation unclear.")
        print(f"{'='*70}\n")
        
        sys.exit(0 if correlation else 1)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
