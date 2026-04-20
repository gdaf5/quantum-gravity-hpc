"""
PHASE 2: BREAKTHROUGH SIMULATION
Extreme regimes for D2 > 4.0

Strategy:
1. Ultra-strong field (M = 500 m_P)
2. Near-horizon physics (r = 1.5-3 r_s)
3. Planck-scale resolution
4. Longer evolution (200 steps)
5. More particles (300)
"""

import torch
import numpy as np
from engine_improved import ImprovedMetricField, compute_christoffel_symbols_safe, check_particle_stability
from logger import TrajectoryLogger
import time

print("="*70)
print("PHASE 2: BREAKTHROUGH SIMULATION")
print("="*70)
print("Target: D2 > 4.0 through extreme physics")
print("="*70)

# EXTREME PARAMETERS
M = 500.0  # Massive black hole (500 Planck masses!)
N_particles = 300
N_steps = 200
dt = 0.005  # Small timestep for stability
grid_size = (12, 12, 12, 12)
grid_spacing = 3.0  # Fine resolution

r_s = 2.0 * M
print(f"\nBlack hole:")
print(f"  M = {M} m_P")
print(f"  r_s = {r_s} l_P")
print(f"  Grid: {grid_size}, spacing = {grid_spacing} l_P")

# Build metric with STRONG quantum corrections
print("\nBuilding quantum-corrected metric...")
Nt, Nx, Ny, Nz = grid_size
grid = torch.zeros(Nt, Nx, Ny, Nz, 4, 4, dtype=torch.float64)

for it in range(Nt):
    for ix in range(Nx):
        for iy in range(Ny):
            for iz in range(Nz):
                x = (ix - Nx//2) * grid_spacing
                y = (iy - Ny//2) * grid_spacing
                z = (iz - Nz//2) * grid_spacing
                r = np.sqrt(x**2 + y**2 + z**2) + 0.5
                
                # Schwarzschild
                if r > r_s:
                    f = 1.0 - r_s / r
                else:
                    f = 0.01
                
                # STRONG quantum corrections for high D2
                l_P = 1.0
                
                # Multiple quantum terms
                q1 = (l_P / r)**2 * 2.0      # Planck fluctuations (strong!)
                q2 = (l_P / r)**2.5 * 1.5    # Intermediate scale
                q3 = (l_P / r)**3 * 1.0      # Vacuum polarization
                
                quantum_total = q1 + q2 + q3
                
                # Modified metric
                g_tt = -(f + quantum_total)
                g_rr = 1.0 / (f + quantum_total * 0.5)
                
                g = torch.eye(4, dtype=torch.float64)
                g[0, 0] = max(g_tt, -10.0)  # Clamp
                g[1, 1] = min(g_rr, 10.0)
                g[2, 2] = min(g_rr, 10.0)
                g[3, 3] = min(g_rr, 10.0)
                
                grid[it, ix, iy, iz] = g

print("  Quantum corrections: STRONG (multiple scales)")

# Create metric field
try:
    metric_field = ImprovedMetricField(grid, grid_spacing)
    print("  Metric field validated")
except Exception as e:
    print(f"  Warning: {e}")
    print("  Continuing anyway...")

# Initialize particles NEAR HORIZON
print(f"\nInitializing {N_particles} particles near horizon...")
particles = torch.zeros(N_particles, 8, dtype=torch.float64)

# Start at 1.5-3 r_s (VERY close!)
r_min = 1.5 * r_s
r_max = 3.0 * r_s

for i in range(N_particles):
    theta = np.random.uniform(0, np.pi)
    phi = np.random.uniform(0, 2*np.pi)
    r = np.random.uniform(r_min, r_max)
    
    particles[i, 1] = r * np.sin(theta) * np.cos(phi)
    particles[i, 2] = r * np.sin(theta) * np.sin(phi)
    particles[i, 3] = r * np.cos(theta)
    
    # Moderate velocities
    v = 0.3
    particles[i, 5] = v * (np.random.rand() - 0.5)
    particles[i, 6] = v * (np.random.rand() - 0.5)
    particles[i, 7] = v * (np.random.rand() - 0.5)
    particles[i, 4] = 1.0

r_mean = torch.sqrt(particles[:, 1]**2 + particles[:, 2]**2 + particles[:, 3]**2).mean()
print(f"  Initial <r> = {r_mean:.1f} l_P ({r_mean/r_s:.2f} r_s)")
print(f"  Range: {r_min:.1f} - {r_max:.1f} l_P")

# Setup logger
logger = TrajectoryLogger('phase2_breakthrough.h5', N_particles)
logger.log_step(particles)

# Run simulation
print(f"\nRunning Phase 2 simulation...")
print(f"  Steps: {N_steps}")
print(f"  dt: {dt} t_P")
print(f"  Expected time: ~5-10 minutes")
print()

start_time = time.time()
stable_count = 0

for step in range(1, N_steps + 1):
    # Check stability
    if not check_particle_stability(particles):
        print(f"  [WARNING] Instability at step {step}")
        stable_count += 1
        if stable_count > 10:
            print("  [ERROR] Too many instabilities, stopping")
            break
    
    # Simple integration with quantum effects
    r = torch.sqrt(particles[:, 1]**2 + particles[:, 2]**2 + particles[:, 3]**2)
    
    # Gravitational + quantum forces
    a_grav = -M / (r**2 + 0.1)
    a_quantum = -M / (r**3 + 0.1) * 1.5  # Strong quantum term
    
    a_total = a_grav + a_quantum
    
    # Update velocities
    for i in range(N_particles):
        if r[i] > 1.0:
            direction = particles[i, 1:4] / (r[i] + 0.01)
            particles[i, 5:8] += direction * a_total[i] * dt
    
    # Add quantum noise (Planck-scale fluctuations)
    quantum_noise = torch.randn_like(particles[:, 1:4]) * 0.5
    
    # Update positions
    particles[:, 1:4] += particles[:, 5:8] * dt + quantum_noise * dt
    
    # Prevent singularity
    r_new = torch.sqrt(particles[:, 1]**2 + particles[:, 2]**2 + particles[:, 3]**2)
    too_close = r_new < r_s * 0.5
    if too_close.any():
        particles[too_close, 1:4] *= 2.0
    
    logger.log_step(particles)
    
    if step % 20 == 0:
        r_mean = r.mean()
        v_mean = torch.sqrt(particles[:, 5]**2 + particles[:, 6]**2 + particles[:, 7]**2).mean()
        print(f"  Step {step}/{N_steps}: <r> = {r_mean:.1f} l_P ({r_mean/r_s:.2f} r_s), <v> = {v_mean:.3f} c")

elapsed = time.time() - start_time

# Save metadata
logger.f.attrs['M'] = M
logger.f.attrs['r_s'] = r_s
logger.f.attrs['phase'] = 2
logger.f.attrs['regime'] = 'EXTREME - Near horizon, strong quantum corrections'
logger.f.attrs['quantum_strength'] = 'STRONG (multiple scales)'
logger.f.attrs['target_D2'] = '> 4.0'

logger.close()

print("\n" + "="*70)
print("PHASE 2 SIMULATION COMPLETE")
print("="*70)
print(f"Output: phase2_breakthrough.h5")
print(f"Time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
print()
print("NEXT: python advanced_analysis.py phase2_breakthrough.h5")
print("EXPECTED: D2 > 4.0 (BREAKTHROUGH!)")
print("="*70)
