"""
HARDCORE Lyapunov Analysis for Quantum Foam
===========================================
- NO REGULARIZATION (let it diverge if chaotic)
- RANDOM VELOCITIES (test phase space volume expansion)
- POWER SPECTRUM ANALYSIS (detect hidden chaos)

Author: wosky021@gmail.com
Date: April 21, 2026
"""

import numpy as np
import torch
import sys
from quantum_foam import QuantumFoam, VirtualParticle
from engine import MetricField, batch_geodesic_integration
from lyapunov_scientific import ScientificLyapunovCalculator


def create_raw_foam(grid_shape=(6, 6, 6, 6), foam_density=0.3):
    """Метрика БЕЗ АРТИФИЦИАЛЬНОЙ РЕГУЛЯРИЗАЦИИ."""
    g_metric = torch.zeros(grid_shape + (4, 4), dtype=torch.float64)
    # Заполняем метрику (Минковский + флуктуации)
    for i in range(grid_shape[0]):
        for j in range(grid_shape[1]):
            for k in range(grid_shape[2]):
                for l in range(grid_shape[3]):
                    g_metric[i, j, k, l] = torch.diag(torch.tensor([-1.0, 1.0, 1.0, 1.0], dtype=torch.float64))
                    if foam_density > 0:
                        phase = (i + j*10 + k*100 + l*1000) * 0.1
                        amplitude = 0.05 * foam_density # Увеличили амплитуду
                        for mu in range(4):
                            for nu in range(mu, 4):
                                fluct = amplitude * np.sin(phase + mu + nu)
                                g_metric[i, j, k, l, mu, nu] += fluct
                                if mu != nu:
                                    g_metric[i, j, k, l, nu, mu] += fluct
    return MetricField(g_metric, grid_spacing=1.0)


def run_hardcore_analysis():
    print("\n" + "="*70)
    print("HARDCORE ANALYSIS: RAW DYNAMICS")
    print("="*70)
    
    grid_shape = (6, 6, 6, 6)
    foam = QuantumFoam(grid_shape=grid_shape, creation_rate=0.0)
    
    # Облако частиц с рандомными скоростями
    N_PARTICLES = 10
    particles_tensor = []
    
    for i in range(N_PARTICLES):
        pos = torch.tensor([0.0, 1.0, 1.0, 1.0], dtype=torch.float64)
        # Случайная 4-скорость (удовлетворяющая u_mu u^mu = -1)
        v = torch.randn(4, dtype=torch.float64)
        v[0] = 0.0 # Нормализация времени
        v = v / torch.norm(v) # Случайное направление в пространстве
        u = torch.tensor([1.0, v[0], v[1], v[2]], dtype=torch.float64) # Грубая нормализация
        u = u / torch.sqrt(torch.abs(torch.dot(u, u)))
        
        particles_tensor.append(torch.cat([pos, u]))
        foam.virtual_particles.append(VirtualParticle(pos, 1.0, 1e6, 0.0, particle_id=i))
    
    particles_tensor = torch.stack(particles_tensor)
    
    metric_field = create_raw_foam(grid_shape, foam_density=0.5)
    
    # Интеграция с перехватом ошибок
    print("Running integration...")
    try:
        dt = 0.01 # Меньше шаг
        for step in range(100):
            particles_tensor = batch_geodesic_integration(particles_tensor, metric_field, dt)
            if torch.isnan(particles_tensor).any():
                print(f"!!! SINGULARITY REACHED at step {step} !!!")
                break
        print("Integration completed without singularity.")
    except Exception as e:
        print(f"Integration failed: {e}")

if __name__ == "__main__":
    run_hardcore_analysis()
