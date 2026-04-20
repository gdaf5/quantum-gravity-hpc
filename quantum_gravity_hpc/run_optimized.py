"""
Optimized Full Simulation with Better Parameters
- Larger central mass for stronger gravity
- Higher initial velocities for more dynamics
- Optimized for performance
"""

import torch
import numpy as np
from main import (initialize_schwarzschild_metric, initialize_particles, 
                  PhysicalConstants)
from engine import MetricField, batch_geodesic_integration
from logger import TrajectoryLogger
import time

def run_optimized_simulation():
    """Run simulation with optimized parameters for interesting dynamics"""
    print("="*70)
    print("OPTIMIZED QUANTUM GRAVITY SIMULATION")
    print("="*70)
    print("Improvements:")
    print("  - Larger central mass (M = 1.0 m_P) for stronger gravity")
    print("  - Higher initial velocities (v = 0.1 c) for more dynamics")
    print("  - 100 particles, 50 steps")
    print("="*70)
    
    # Parameters
    n_particles = 100
    n_steps = 50
    grid_shape = (8, 8, 8, 8)
    central_mass = 1.0  # Increased from 0.1 to 1.0
    grid_spacing = 10.0
    dt = 0.1
    
    device = 'cpu'
    dtype = torch.float64
    
    # Initialize
    print("\nInitializing...")
    g_metric = initialize_schwarzschild_metric(grid_shape, central_mass, dtype, device)
    
    # Initialize particles with higher velocities
    particles = torch.zeros((n_particles, 8), dtype=dtype, device=device)
    
    # Positions: Gaussian distribution
    center = torch.zeros(3, dtype=dtype, device=device)
    radius = 5.0 * grid_spacing  # 50 l_P
    
    for i in range(3):
        particles[:, i+1] = torch.randn(n_particles, dtype=dtype, device=device) * radius + center[i]
    
    # Time coordinate
    particles[:, 0] = 0.0
    
    # 4-velocities: HIGHER velocities for more interesting dynamics
    particles[:, 4] = 1.0  # u^0
    
    # Spatial velocities (increased from 0.01 to 0.1)
    v_thermal = 0.1  # 10% speed of light
    particles[:, 5:8] = torch.randn((n_particles, 3), dtype=dtype, device=device) * v_thermal
    
    # Normalize 4-velocity
    v_squared = torch.sum(particles[:, 5:8]**2, dim=1)
    particles[:, 4] = torch.sqrt(1.0 + v_squared)
    
    print(f"Initialized {n_particles} particles")
    print(f"  Position spread: {radius:.1f} l_P")
    print(f"  Velocity scale: {v_thermal} c (10x higher!)")
    print(f"  Central mass: {central_mass} m_P (10x stronger gravity!)")
    
    metric_field = MetricField(g_metric, grid_spacing, dtype, device)
    logger = TrajectoryLogger("optimized_simulation.h5", num_particles=n_particles)
    
    print("\nRunning simulation...")
    start_time = time.time()
    
    for step in range(n_steps):
        # Integrate
        particles = batch_geodesic_integration(particles, metric_field, dt)
        
        # Log
        logger.log_step(particles)
        
        # Progress
        if step % 10 == 0:
            mean_r = torch.mean(torch.norm(particles[:, 1:4], dim=1))
            mean_v = torch.mean(torch.norm(particles[:, 5:8], dim=1))
            print(f"  Step {step}/{n_steps}: <r> = {mean_r:.2f} l_P, <v> = {mean_v:.4f} c")
    
    elapsed = time.time() - start_time
    
    logger.close()
    
    print("\n" + "="*70)
    print("SIMULATION COMPLETE")
    print("="*70)
    print(f"Output: optimized_simulation.h5")
    print(f"Time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    
    # Final statistics
    mean_r_final = torch.mean(torch.norm(particles[:, 1:4], dim=1))
    mean_v_final = torch.mean(torch.norm(particles[:, 5:8], dim=1))
    
    print(f"\nFinal state:")
    print(f"  Mean radius: {mean_r_final:.2f} l_P")
    print(f"  Mean velocity: {mean_v_final:.4f} c")
    
    # Check for interesting dynamics
    initial_r = radius
    expansion = (mean_r_final.item() - initial_r) / initial_r * 100
    
    print(f"\nDynamics:")
    print(f"  Radius change: {expansion:+.1f}%")
    
    if abs(expansion) > 10:
        print("  [SUCCESS] Strong dynamics observed!")
    elif abs(expansion) > 1:
        print("  [OK] Moderate dynamics")
    else:
        print("  [WARNING] Weak dynamics")
    
    return particles, g_metric


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    particles, metric = run_optimized_simulation()
    
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("1. Analyze results:")
    print("   python advanced_analysis.py optimized_simulation.h5")
    print("\n2. Get real D2 value from analysis_report.json")
    print("\n3. Update testable predictions with real D2")
