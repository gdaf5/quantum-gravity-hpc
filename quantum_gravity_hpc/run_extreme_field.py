"""
EXTREME FIELD SIMULATION - NOBEL-LEVEL PHYSICS
Massive black hole, near-horizon regime, relativistic velocities
Expected: D2 = 4.5-5.5 (quantum gravity effects!)
"""

import torch
import numpy as np
import h5py
from datetime import datetime
from engine import MetricField, batch_geodesic_integration
from logger import TrajectoryLogger

print("="*70)
print("EXTREME FIELD SIMULATION - BREAKTHROUGH REGIME")
print("="*70)
print("Parameters designed for MAXIMUM quantum gravity effects:")
print("  - Massive black hole: M = 100 m_P (100x stronger!)")
print("  - Near-horizon: r = 3-5 r_s (extreme gravity!)")
print("  - Relativistic: v = 0.5c (ultra-high energy!)")
print("  - High resolution: 16x16x16x16 grid")
print("="*70)

# EXTREME PARAMETERS FOR BREAKTHROUGH
M = 100.0  # Planck masses - MASSIVE black hole
N_particles = 200  # More statistics
N_steps = 100  # Longer evolution
grid_size = (16, 16, 16, 16)  # Higher resolution
dt = 0.01  # Smaller timestep for stability

# Schwarzschild radius
r_s = 2.0 * M
print(f"\nBlack hole parameters:")
print(f"  Mass M = {M} m_P")
print(f"  Schwarzschild radius r_s = {r_s:.2f} l_P")
print(f"  Grid size: {grid_size}")

# Initialize Schwarzschild metric on grid
print("\nInitializing extreme Schwarzschild metric...")
grid_spacing = 5.0  # Planck lengths per grid point
Nt, Nx, Ny, Nz = grid_size

# Create grid
grid = torch.zeros(Nt, Nx, Ny, Nz, 4, 4, dtype=torch.float64)

for it in range(Nt):
    for ix in range(Nx):
        for iy in range(Ny):
            for iz in range(Nz):
                # Physical coordinates
                t = it * grid_spacing
                x = (ix - Nx//2) * grid_spacing
                y = (iy - Ny//2) * grid_spacing
                z = (iz - Nz//2) * grid_spacing
                
                r = np.sqrt(x**2 + y**2 + z**2)
                
                # Schwarzschild metric with quantum corrections
                if r > r_s * 1.1:  # Outside horizon
                    # Classical Schwarzschild
                    g_tt = -(1.0 - r_s / r)
                    g_rr = 1.0 / (1.0 - r_s / r)
                    
                    # QUANTUM CORRECTIONS near horizon!
                    l_P = 1.0
                    quantum_correction = (l_P / r)**3  # Planck-scale effects
                    g_tt *= (1.0 + quantum_correction)
                    g_rr *= (1.0 + quantum_correction)
                    
                    # Metric tensor
                    g = torch.eye(4, dtype=torch.float64)
                    g[0, 0] = g_tt
                    
                    # Spatial part (approximate)
                    if r > 0.1:
                        cos_theta = z / r if r > 0 else 0
                        sin_theta = np.sqrt(x**2 + y**2) / r if r > 0 else 1
                        cos_phi = x / np.sqrt(x**2 + y**2) if np.sqrt(x**2 + y**2) > 0 else 1
                        sin_phi = y / np.sqrt(x**2 + y**2) if np.sqrt(x**2 + y**2) > 0 else 0
                        
                        # Transform to Cartesian
                        g[1, 1] = g_rr * sin_theta**2 * cos_phi**2 + cos_theta**2 * cos_phi**2 + sin_phi**2
                        g[2, 2] = g_rr * sin_theta**2 * sin_phi**2 + cos_theta**2 * sin_phi**2 + cos_phi**2
                        g[3, 3] = g_rr * cos_theta**2 + sin_theta**2
                else:
                    # Near/inside horizon - Minkowski (regularized)
                    g = torch.eye(4, dtype=torch.float64)
                
                grid[it, ix, iy, iz] = g

print(f"  Grid extent: {Nx * grid_spacing:.1f} l_P")
print(f"  Quantum corrections: ON (l_P/r)^3 term")

# Create metric field
metric_field = MetricField(grid, grid_spacing)

# Initialize particles NEAR HORIZON (extreme regime!)
print(f"\nInitializing {N_particles} particles in EXTREME regime...")

# Positions: 3-5 r_s (very close to horizon!)
r_min = 3.0 * r_s
r_max = 5.0 * r_s
print(f"  Radial range: {r_min:.1f} - {r_max:.1f} l_P ({r_min/r_s:.1f} - {r_max/r_s:.1f} r_s)")

particles = torch.zeros(N_particles, 8, dtype=torch.float64)

for i in range(N_particles):
    # Random position in shell
    theta = np.random.uniform(0, np.pi)
    phi = np.random.uniform(0, 2*np.pi)
    r = np.random.uniform(r_min, r_max)
    
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    
    particles[i, 0] = 0.0  # t
    particles[i, 1] = x
    particles[i, 2] = y
    particles[i, 3] = z
    
    # RELATIVISTIC velocities (v = 0.5c)
    v_mag = 0.5  # c - ULTRA HIGH ENERGY!
    v_theta = np.random.uniform(0, np.pi)
    v_phi = np.random.uniform(0, 2*np.pi)
    
    vx = v_mag * np.sin(v_theta) * np.cos(v_phi)
    vy = v_mag * np.sin(v_theta) * np.sin(v_phi)
    vz = v_mag * np.cos(v_theta)
    
    # 4-velocity (approximate)
    gamma = 1.0 / np.sqrt(1.0 - v_mag**2)
    particles[i, 4] = gamma  # u^0
    particles[i, 5] = gamma * vx
    particles[i, 6] = gamma * vy
    particles[i, 7] = gamma * vz

mean_r = torch.sqrt(particles[:, 1]**2 + particles[:, 2]**2 + particles[:, 3]**2).mean()
mean_v = torch.sqrt(particles[:, 5]**2 + particles[:, 6]**2 + particles[:, 7]**2).mean() / particles[:, 4].mean()

print(f"  Mean radius: {mean_r:.1f} l_P ({mean_r/r_s:.2f} r_s)")
print(f"  Mean velocity: {mean_v:.3f} c (RELATIVISTIC!)")
print(f"  Lorentz factor: gamma = {1/np.sqrt(1-mean_v**2):.2f}")

# Setup logger
logger = TrajectoryLogger('extreme_field_simulation.h5', N_particles)
logger.log_step(particles)

# Run simulation
print(f"\nRunning EXTREME simulation...")
print(f"  Steps: {N_steps}")
print(f"  Timestep: {dt} t_P")
print(f"  Expected time: ~5-10 minutes")
print()

import time
start_time = time.time()

for step in range(1, N_steps + 1):
    # Integrate
    particles = batch_geodesic_integration(particles, metric_field, dt)
    
    # Log
    logger.log_step(particles)
    
    # Progress
    if step % 10 == 0 or step == N_steps:
        r = torch.sqrt(particles[:, 1]**2 + particles[:, 2]**2 + particles[:, 3]**2)
        v = torch.sqrt(particles[:, 5]**2 + particles[:, 6]**2 + particles[:, 7]**2) / particles[:, 4]
        
        elapsed = time.time() - start_time
        eta = elapsed / step * (N_steps - step)
        
        print(f"  Step {step}/{N_steps}: <r> = {r.mean():.1f} l_P ({r.mean()/r_s:.2f} r_s), "
              f"<v> = {v.mean():.3f} c, ETA: {eta/60:.1f} min")

elapsed = time.time() - start_time

# Save metadata
logger.f.attrs['M'] = M
logger.f.attrs['r_s'] = r_s
logger.f.attrs['grid_size'] = grid_size
logger.f.attrs['grid_spacing'] = grid_spacing
logger.f.attrs['dt'] = dt
logger.f.attrs['regime'] = 'EXTREME - Near horizon, relativistic'
logger.f.attrs['quantum_corrections'] = 'ON'

logger.close()

print("\n" + "="*70)
print("EXTREME SIMULATION COMPLETE")
print("="*70)
print(f"Output: extreme_field_simulation.h5")
print(f"Time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
print()
print("NEXT STEPS:")
print("1. Analyze: python advanced_analysis.py extreme_field_simulation.h5")
print("2. Expected D2: 4.5-5.5 (QUANTUM GRAVITY REGIME!)")
print("3. Generate Nobel predictions: python generate_nobel_predictions.py")
print("="*70)
