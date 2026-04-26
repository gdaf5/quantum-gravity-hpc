"""
BETA: Lyapunov Analysis for Quantum Foam (Geodesic Only)
=======================================================
Фиксирует количество частиц для корректного измерения Ляпунова.

Author: wosky021@gmail.com
Date: April 21, 2026
"""

import numpy as np
import torch
import sys
from quantum_foam import QuantumFoam, VirtualParticle
from engine import MetricField
from physics_registry import PhysicsRegistry
from lyapunov_scientific import ScientificLyapunovCalculator


def create_static_foam(grid_shape=(6, 6, 6, 6), foam_density=0.3):
    """Создать метрику с флуктуациями и регуляризацией."""
    g_metric = torch.zeros(grid_shape + (4, 4), dtype=torch.float64)
    for i in range(grid_shape[0]):
        for j in range(grid_shape[1]):
            for k in range(grid_shape[2]):
                for l in range(grid_shape[3]):
                    # Минковский + регуляризация (ε=0.01)
                    g_metric[i, j, k, l, 0, 0] = -1.0 + 0.01
                    g_metric[i, j, k, l, 1, 1] = 1.0 + 0.01
                    g_metric[i, j, k, l, 2, 2] = 1.0 + 0.01
                    g_metric[i, j, k, l, 3, 3] = 1.0 + 0.01
                    
                    if foam_density > 0:
                        phase = (i + j*10 + k*100 + l*1000) * 0.1
                        amplitude = 0.01 * foam_density
                        for mu in range(4):
                            for nu in range(mu, 4):
                                fluct = amplitude * np.sin(phase + mu + nu)
                                g_metric[i, j, k, l, mu, nu] += fluct
                                if mu != nu:
                                    g_metric[i, j, k, l, nu, mu] += fluct
    return MetricField(g_metric, grid_spacing=1.0)


def run_beta_analysis():
    print("\n" + "="*70)
    print("BETA ANALYSIS: GEODESIC DYNAMICS ONLY")
    print("="*70)
    
    # 1. Параметры системы
    grid_shape = (6, 6, 6, 6)
    
    # 2. Инициализация Foam в "замороженном" режиме
    foam = QuantumFoam(
        grid_shape=grid_shape,
        creation_rate=0.0,
        collapse_threshold=0.0,  # Отключено
        enable_hawking_evaporation=False,  # Отключено
        random_seed=42
    )
    
    # 3. Добавление фиксированного количества частиц (5)
    for i in range(5):
        pos = torch.tensor([0.0, 1.0 + i*0.1, 1.0, 1.0], dtype=torch.float64)
        particle = VirtualParticle(
            position=pos, mass=1.0, lifetime=1e6, birth_time=0.0,
            particle_id=foam._next_particle_id
        )
        foam._next_particle_id += 1
        foam.virtual_particles.append(particle)
    
    # 4. Метрика
    metric_field = create_static_foam(grid_shape, foam_density=0.3)
    
    # 5. Анализ Ляпунова
    calculator = ScientificLyapunovCalculator(
        epsilon=1e-8,
        renorm_steps=5,
        transient_time=2.0,
        measurement_time=10.0,
        dt=0.1
    )
    
    # Переопределяем evolve_foam для чисто геодезического движения
    def frozen_evolve(self, metric_field, current_time, dt):
        """Только движение частиц по геодезическим."""
        from engine import batch_geodesic_integration
        
        # Подготовка данных для batch_geodesic_integration
        # [N, 8] - (t, x, y, z, u0, u1, u2, u3)
        # Предполагаем u0=1, ui=0 (покой в системе отсчета)
        particles_tensor = []
        for p in self.virtual_particles:
            u = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=torch.float64)
            particles_tensor.append(torch.cat([p.position, u]))
        
        particles_tensor = torch.stack(particles_tensor)
        
        # Интеграция
        new_particles = batch_geodesic_integration(particles_tensor, metric_field, dt)
        
        # Обновление позиций
        for i, p in enumerate(self.virtual_particles):
            p.position = new_particles[i, :4]
            
        return {'total_particles': len(self.virtual_particles)}

    # Monkey patch
    QuantumFoam.evolve_foam = frozen_evolve
    
    result = calculator.compute_lyapunov_exponent(foam, metric_field, verbose=True)
    
    print(f"\nFinal Interpretation:")
    print(f"  lambda_det = {result['lyapunov_exponent']:.6f}")
    if result['lyapunov_exponent'] < 0.01:
        print("  -> Stable geodesic motion (No classical chaos)")
    else:
        print("  -> Chaotic geodesic motion")

if __name__ == "__main__":
    run_beta_analysis()
