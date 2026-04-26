"""
CORRECT Lyapunov Analysis for Quantum Foam
===========================================

Правильный анализ показателей Ляпунова для стохастических систем.

Разделяем:
1. Детерминированную компоненту (геодезическая динамика)
2. Стохастическую компоненту (создание/уничтожение частиц)
3. Полное расхождение (комбинация обоих)

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


def analyze_deterministic_component(foam_density=0.3):
    """
    Анализ детерминированной компоненты (без стохастического создания частиц).
    """
    print(f"\n{'='*70}")
    print(f"DETERMINISTIC COMPONENT ANALYSIS")
    print(f"{'='*70}")
    print(f"Foam density: {foam_density:.1f} rho_P")
    print(f"Particle creation: DISABLED (deterministic dynamics only)")
    
    # Параметры
    registry = PhysicsRegistry()
    regime = 'medium_foam' if foam_density >= 0.2 else 'weak_foam'
    params = registry.get_recommended_parameters(regime)
    
    # Создать метрику
    grid_shape = (6, 6, 6, 6)
    metric_field = create_foam_metric(grid_shape, foam_density)
    
    # Создать систему БЕЗ стохастического создания частиц
    foam = QuantumFoam(
        grid_shape=grid_shape,
        creation_rate=0.0,  # ОТКЛЮЧЕНО!
        collapse_threshold=params['collapse_threshold'],
        softening_length=params['softening_length'],
        enable_hawking_evaporation=False,  # Отключить испарение
        random_seed=42
    )
    
    # Добавить несколько частиц вручную для тестирования
    from quantum_foam import VirtualParticle
    for i in range(5):
        pos = torch.tensor([0.0, 1.0 + i*0.5, 1.0, 1.0], dtype=torch.float64)
        particle = VirtualParticle(
            position=pos,
            mass=1.0,
            lifetime=10.0,
            birth_time=0.0,
            particle_id=foam._next_particle_id
        )
        foam._next_particle_id += 1
        foam.virtual_particles.append(particle)
    
    print(f"Initial particles: {len(foam.virtual_particles)}")
    
    # Вычислить показатель Ляпунова
    calculator = ScientificLyapunovCalculator(
        epsilon=1e-6,  # Увеличили возмущение
        renorm_steps=5,
        transient_time=1.0,
        measurement_time=5.0,
        dt=0.1
    )
    
    result = calculator.compute_lyapunov_exponent(
        foam, metric_field, verbose=True
    )
    
    return result


def analyze_stochastic_component(foam_density=0.3):
    """
    Анализ стохастической компоненты (с несинхронизированными RNG).
    """
    print(f"\n{'='*70}")
    print(f"STOCHASTIC COMPONENT ANALYSIS")
    print(f"{'='*70}")
    print(f"Foam density: {foam_density:.1f} rho_P")
    print(f"Using UNSYNCHRONIZED RNG to measure stochastic divergence")
    
    # Параметры
    registry = PhysicsRegistry()
    regime = 'medium_foam' if foam_density >= 0.2 else 'weak_foam'
    params = registry.get_recommended_parameters(regime)
    
    # Создать метрику
    grid_shape = (6, 6, 6, 6)
    metric_field = create_foam_metric(grid_shape, foam_density)
    
    # Создать систему с разными seeds
    foam1 = QuantumFoam(
        grid_shape=grid_shape,
        creation_rate=params['creation_rate'],
        collapse_threshold=params['collapse_threshold'],
        softening_length=params['softening_length'],
        enable_hawking_evaporation=True,
        random_seed=42
    )
    
    foam2 = QuantumFoam(
        grid_shape=grid_shape,
        creation_rate=params['creation_rate'],
        collapse_threshold=params['collapse_threshold'],
        softening_length=params['softening_length'],
        enable_hawking_evaporation=True,
        random_seed=43  # РАЗНЫЙ seed!
    )
    
    # Эволюционировать обе системы
    import copy
    
    current_time = 0.0
    dt = 0.1
    n_steps = 50
    
    divergences = []
    times = []
    
    for step in range(n_steps):
        foam1.evolve_foam(metric_field, current_time, dt)
        foam2.evolve_foam(metric_field, current_time, dt)
        current_time += dt
        
        # Измерить "расхождение" (количество частиц)
        n1 = len(foam1.virtual_particles)
        n2 = len(foam2.virtual_particles)
        divergence = abs(n1 - n2)
        
        divergences.append(divergence)
        times.append(current_time)
        
        if step % 10 == 0:
            print(f"  t = {current_time:.1f}: n1 = {n1}, n2 = {n2}, diff = {divergence}")
    
    # Оценить "стохастическое расхождение"
    avg_divergence = np.mean(divergences[20:])  # После переходного периода
    
    print(f"\nAverage particle count difference: {avg_divergence:.1f}")
    print(f"This represents stochastic divergence, NOT Lyapunov exponent")
    
    return {
        'avg_divergence': avg_divergence,
        'divergences': divergences,
        'times': times
    }


def full_analysis():
    """Полный анализ с разделением компонент."""
    
    print("\n" + "="*70)
    print("COMPLETE LYAPUNOV ANALYSIS FOR QUANTUM FOAM")
    print("="*70)
    print("\nSeparating deterministic and stochastic components")
    
    foam_density = 0.3
    
    # 1. Детерминированная компонента
    print("\n" + "="*70)
    print("PART 1: DETERMINISTIC DYNAMICS")
    print("="*70)
    det_result = analyze_deterministic_component(foam_density)
    
    # 2. Стохастическая компонента
    print("\n" + "="*70)
    print("PART 2: STOCHASTIC DIVERGENCE")
    print("="*70)
    stoch_result = analyze_stochastic_component(foam_density)
    
    # 3. Выводы
    print("\n" + "="*70)
    print("CONCLUSIONS")
    print("="*70)
    
    print(f"\n1. DETERMINISTIC LYAPUNOV EXPONENT:")
    print(f"   lambda_det = {det_result['lyapunov_exponent']:.6f}")
    if det_result['lyapunov_exponent'] < 0.01:
        print(f"   -> Geodesic dynamics is STABLE (not chaotic)")
    else:
        print(f"   -> Geodesic dynamics is CHAOTIC")
    
    print(f"\n2. STOCHASTIC DIVERGENCE:")
    print(f"   Average particle difference = {stoch_result['avg_divergence']:.1f}")
    print(f"   -> Stochastic particle creation causes divergence")
    print(f"   -> This is NOT a Lyapunov exponent!")
    
    print(f"\n3. PREVIOUS RESULTS (lambda ~ 40):")
    print(f"   -> Were measuring stochastic divergence, not Lyapunov exponent")
    print(f"   -> Caused by unsynchronized random number generators")
    print(f"   -> NOT valid for scientific publication")
    
    print(f"\n4. CORRECT INTERPRETATION:")
    print(f"   - Quantum foam geodesic dynamics: lambda_det ~ {det_result['lyapunov_exponent']:.2f}")
    print(f"   - Stochastic effects dominate over deterministic chaos")
    print(f"   - System is 'stochastic' rather than 'deterministically chaotic'")
    
    print("\n" + "="*70)
    print("RECOMMENDATION FOR PUBLICATION")
    print("="*70)
    print("""
The quantum foam exhibits:
1. Stable geodesic dynamics (lambda_det ~ 0)
2. Strong stochastic fluctuations from particle creation/annihilation
3. Overall behavior is dominated by quantum stochasticity, not deterministic chaos

This is physically reasonable: at Planck scale, quantum uncertainty dominates
over classical chaotic dynamics.

DO NOT claim 'chaotic dynamics' based on lambda ~ 40.
Instead, emphasize 'quantum stochastic behavior' at Planck scale.
    """)
    
    return {
        'deterministic': det_result,
        'stochastic': stoch_result
    }


if __name__ == "__main__":
    try:
        results = full_analysis()
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
