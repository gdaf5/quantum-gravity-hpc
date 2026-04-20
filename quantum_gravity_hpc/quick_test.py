"""
Quick Test Simulation - Lightweight version for testing
"""

import torch
import numpy as np
from main import (initialize_schwarzschild_metric, initialize_particles, 
                  compute_stress_energy_tensor, PhysicalConstants)
from engine import MetricField, batch_geodesic_integration
from logger import TrajectoryLogger

def run_quick_test():
    """Run minimal simulation for testing"""
    print("="*70)
    print("QUICK TEST SIMULATION")
    print("="*70)
    print("Parameters: 10 particles, 10 steps, 4x4x4x4 grid")
    print("Expected time: ~30 seconds")
    print("="*70)
    
    # Minimal parameters
    n_particles = 10
    n_steps = 10
    grid_shape = (4, 4, 4, 4)
    central_mass = 0.1
    grid_spacing = 10.0
    dt = 0.1
    
    device = 'cpu'
    dtype = torch.float64
    
    # Initialize
    print("\nInitializing...")
    g_metric = initialize_schwarzschild_metric(grid_shape, central_mass, dtype, device)
    particles = initialize_particles(n_particles, grid_spacing, dtype, device)
    metric_field = MetricField(g_metric, grid_spacing, dtype, device)
    
    logger = TrajectoryLogger("quick_test.h5", num_particles=n_particles)
    
    print("\nRunning simulation...")
    
    for step in range(n_steps):
        # Integrate
        particles = batch_geodesic_integration(particles, metric_field, dt)
        
        # Log
        logger.log_step(particles)
        
        # Progress
        mean_r = torch.mean(torch.norm(particles[:, 1:4], dim=1))
        mean_v = torch.mean(torch.norm(particles[:, 5:8], dim=1))
        print(f"  Step {step+1}/{n_steps}: <r> = {mean_r:.2f} l_P, <v> = {mean_v:.4f} c")
    
    logger.close()
    
    print("\n" + "="*70)
    print("SIMULATION COMPLETE")
    print("="*70)
    print(f"Output: quick_test.h5")
    print(f"Final mean radius: {mean_r:.2f} l_P")
    print(f"Final mean velocity: {mean_v:.4f} c")
    
    # Basic analysis
    print("\n" + "="*70)
    print("BASIC ANALYSIS")
    print("="*70)
    
    # Check if particles moved
    initial_r = 50.0  # Initial spread
    expansion = (mean_r.item() - initial_r) / initial_r * 100
    
    print(f"Radius change: {expansion:+.1f}%")
    
    if abs(expansion) > 1:
        print("✓ Particles are moving (quantum effects or gravity)")
    else:
        print("⚠ Particles barely moved (may need more steps)")
    
    # Energy check (rough)
    kinetic_energy = 0.5 * torch.sum(particles[:, 5:8]**2)
    print(f"Total kinetic energy: {kinetic_energy:.6e}")
    
    return particles, g_metric


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    particles, metric = run_quick_test()
