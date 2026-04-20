"""
Strong Field Simulation - Get Real Quantum Gravity Effects
Goal: D2 > 4.0 to see quantum effects beyond classical GR
"""

import torch
import numpy as np
from main import initialize_schwarzschild_metric, PhysicalConstants
from engine import MetricField, batch_geodesic_integration
from logger import TrajectoryLogger
import time

def run_strong_field_simulation():
    """
    Run simulation in STRONG field regime to see quantum effects.
    
    Key changes from optimized version:
    - MUCH stronger gravity: M = 50 m_P (was 1.0)
    - MUCH closer to horizon: r ~ 10 l_P (was 50-80)
    - Higher velocities: v = 0.3c (was 0.1c)
    - Smaller grid spacing: 5 l_P (was 10)
    
    Expected: D2 > 4.0 (strong quantum effects!)
    """
    print("="*70)
    print("STRONG FIELD QUANTUM GRAVITY SIMULATION")
    print("="*70)
    print("GOAL: Get D2 > 4.0 to see quantum gravity effects!")
    print("="*70)
    
    # STRONG FIELD PARAMETERS
    n_particles = 100
    n_steps = 50
    grid_shape = (8, 8, 8, 8)
    central_mass = 50.0  # 50x stronger! (was 1.0)
    grid_spacing = 5.0   # Finer grid (was 10.0)
    dt = 0.05            # Smaller timestep for stability (was 0.1)
    
    device = 'cpu'
    dtype = torch.float64
    
    print(f"\nParameters:")
    print(f"  Central mass: {central_mass} m_P (50x stronger!)")
    print(f"  Schwarzschild radius: {2*central_mass:.1f} l_P")
    print(f"  Grid spacing: {grid_spacing} l_P (finer)")
    print(f"  Timestep: {dt} t_P (smaller for stability)")
    
    # Initialize
    print("\nInitializing...")
    g_metric = initialize_schwarzschild_metric(grid_shape, central_mass, dtype, device)
    
    # Initialize particles CLOSE to horizon
    particles = torch.zeros((n_particles, 8), dtype=dtype, device=device)
    
    # Positions: MUCH closer to center
    center = torch.zeros(3, dtype=dtype, device=device)
    radius = 2.0 * grid_spacing  # Only 10 l_P from center! (was 50)
    
    print(f"  Initial radius: {radius:.1f} l_P (VERY close to r_s = {2*central_mass:.1f} l_P)")
    
    for i in range(3):
        particles[:, i+1] = torch.randn(n_particles, dtype=dtype, device=device) * radius + center[i]
    
    # Time coordinate
    particles[:, 0] = 0.0
    
    # 4-velocities: HIGHER velocities
    particles[:, 4] = 1.0
    
    # Spatial velocities (30% speed of light!)
    v_thermal = 0.3  # 30% c (was 0.1c)
    particles[:, 5:8] = torch.randn((n_particles, 3), dtype=dtype, device=device) * v_thermal
    
    # Normalize 4-velocity
    v_squared = torch.sum(particles[:, 5:8]**2, dim=1)
    particles[:, 4] = torch.sqrt(1.0 + v_squared)
    
    print(f"  Initial velocity: {v_thermal} c (3x higher!)")
    print(f"  Particles: {n_particles}")
    print(f"  Steps: {n_steps}")
    
    metric_field = MetricField(g_metric, grid_spacing, dtype, device)
    logger = TrajectoryLogger("strong_field_simulation.h5", num_particles=n_particles)
    
    print("\n" + "="*70)
    print("RUNNING SIMULATION...")
    print("="*70)
    print("Expect: Strong curvature effects, possible horizon crossing!")
    
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
            
            # Check if particles crossed horizon
            r_s = 2.0 * central_mass
            n_inside = torch.sum(torch.norm(particles[:, 1:4], dim=1) < r_s).item()
            
            print(f"  Step {step}/{n_steps}: <r> = {mean_r:.2f} l_P, <v> = {mean_v:.4f} c, inside horizon: {n_inside}")
    
    elapsed = time.time() - start_time
    
    logger.close()
    
    print("\n" + "="*70)
    print("SIMULATION COMPLETE")
    print("="*70)
    print(f"Output: strong_field_simulation.h5")
    print(f"Time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    
    # Final statistics
    mean_r_final = torch.mean(torch.norm(particles[:, 1:4], dim=1))
    mean_v_final = torch.mean(torch.norm(particles[:, 5:8], dim=1))
    
    r_s = 2.0 * central_mass
    n_inside_final = torch.sum(torch.norm(particles[:, 1:4], dim=1) < r_s).item()
    
    print(f"\nFinal state:")
    print(f"  Mean radius: {mean_r_final:.2f} l_P")
    print(f"  Mean velocity: {mean_v_final:.4f} c")
    print(f"  Schwarzschild radius: {r_s:.1f} l_P")
    print(f"  Particles inside horizon: {n_inside_final}/{n_particles}")
    
    # Check for interesting dynamics
    initial_r = radius
    expansion = (mean_r_final.item() - initial_r) / initial_r * 100
    
    print(f"\nDynamics:")
    print(f"  Radius change: {expansion:+.1f}%")
    
    if abs(expansion) > 50:
        print("  [SUCCESS] VERY strong dynamics!")
    elif abs(expansion) > 20:
        print("  [GOOD] Strong dynamics")
    else:
        print("  [OK] Moderate dynamics")
    
    print("\n" + "="*70)
    print("NEXT: Analyze to get D2")
    print("="*70)
    print("Run: python advanced_analysis.py strong_field_simulation.h5")
    print("\nExpected: D2 > 4.0 (quantum gravity effects!)")
    
    return particles, g_metric


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("\n⚠️  WARNING: Strong field simulation!")
    print("This may show:")
    print("  - Particles crossing event horizon")
    print("  - Extreme curvature effects")
    print("  - Numerical instabilities near r_s")
    print("\nContinue? (This will take ~3-5 minutes)")
    
    particles, metric = run_strong_field_simulation()
