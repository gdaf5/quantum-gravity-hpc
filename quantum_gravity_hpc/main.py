"""
Main Simulation with Physical Metric
- Uses Schwarzschild metric as initial condition
- Solves Einstein equations with matter back-reaction
- Proper Planck units throughout
"""

import torch
import numpy as np
from engine import MetricField, batch_geodesic_integration
from einstein_solver import EinsteinSolver
from logger import TrajectoryLogger

class PhysicalConstants:
    """Physical constants in Planck units (G = c = hbar = 1)"""
    def __init__(self):
        # In Planck units, everything is 1
        self.c = 1.0
        self.G = 1.0
        self.hbar = 1.0
        self.l_P = 1.0  # Planck length
        self.t_P = 1.0  # Planck time
        self.m_P = 1.0  # Planck mass
        
        # For reference: SI values
        self.l_P_SI = 1.616e-35  # meters
        self.t_P_SI = 5.39e-44   # seconds
        self.m_P_SI = 2.176e-8   # kg


def initialize_schwarzschild_metric(grid_shape=(8, 8, 8, 8), 
                                    M=0.1,  # mass in Planck masses
                                    dtype=torch.float64,
                                    device='cpu') -> torch.Tensor:
    """
    Initialize Schwarzschild metric as starting point.
    
    ds² = -(1 - 2M/r) dt² + (1 - 2M/r)⁻¹ dr² + r² dΩ²
    
    Args:
        grid_shape: grid dimensions
        M: central mass in Planck masses
        dtype, device: torch parameters
    Returns:
        g: [Nt, Nx, Ny, Nz, 4, 4] metric tensor
    """
    print(f"Initializing Schwarzschild metric with M = {M} m_P")
    
    g = torch.zeros((*grid_shape, 4, 4), dtype=dtype, device=device)
    
    # Schwarzschild radius
    r_s = 2.0 * M
    
    # Grid spacing (in Planck lengths)
    grid_spacing = 10.0  # each cell is 10 l_P
    
    for it in range(grid_shape[0]):
        for ix in range(grid_shape[1]):
            for iy in range(grid_shape[2]):
                for iz in range(grid_shape[3]):
                    # Physical coordinates (centered at grid center)
                    x = (ix - grid_shape[1] / 2) * grid_spacing
                    y = (iy - grid_shape[2] / 2) * grid_spacing
                    z = (iz - grid_shape[3] / 2) * grid_spacing
                    
                    r = np.sqrt(x**2 + y**2 + z**2)
                    
                    # Avoid singularity
                    if r < r_s * 1.1:
                        r = r_s * 1.1
                    
                    # Schwarzschild metric components
                    f = 1.0 - r_s / r
                    
                    # g_tt
                    g[it, ix, iy, iz, 0, 0] = -f
                    
                    # g_rr (in Cartesian coordinates, approximate)
                    # For simplicity, use diagonal spatial metric
                    g[it, ix, iy, iz, 1, 1] = 1.0 / f
                    g[it, ix, iy, iz, 2, 2] = 1.0 / f
                    g[it, ix, iy, iz, 3, 3] = 1.0 / f
                    
                    # Add small quantum fluctuations
                    fluctuation = 0.01
                    for mu in range(4):
                        for nu in range(mu, 4):
                            noise = torch.randn(1, dtype=dtype, device=device).item() * fluctuation
                            g[it, ix, iy, iz, mu, nu] += noise
                            if mu != nu:
                                g[it, ix, iy, iz, nu, mu] += noise
    
    print(f"  Grid spacing: {grid_spacing} l_P")
    print(f"  Schwarzschild radius: {r_s:.2f} l_P")
    print(f"  Grid extent: {grid_shape[1] * grid_spacing:.1f} l_P")
    
    return g


def initialize_particles(n_particles=100, 
                        grid_spacing=10.0,
                        dtype=torch.float64,
                        device='cpu') -> torch.Tensor:
    """
    Initialize particle cloud in Planck units.
    
    Args:
        n_particles: number of particles
        grid_spacing: grid spacing in Planck lengths
        dtype, device: torch parameters
    Returns:
        particles: [N, 8] - (t, x, y, z, u^0, u^1, u^2, u^3)
    """
    particles = torch.zeros((n_particles, 8), dtype=dtype, device=device)
    
    # Positions: Gaussian distribution around center
    center = torch.zeros(3, dtype=dtype, device=device)
    radius = 5.0 * grid_spacing  # 5 cells radius
    
    for i in range(3):
        particles[:, i+1] = torch.randn(n_particles, dtype=dtype, device=device) * radius + center[i]
    
    # Time coordinate
    particles[:, 0] = 0.0
    
    # 4-velocities: mostly at rest, small random velocities
    # u^0 ≈ 1 (timelike)
    particles[:, 4] = 1.0
    
    # Spatial velocities (small, in Planck units)
    v_thermal = 0.01  # thermal velocity ~ 0.01 c
    particles[:, 5:8] = torch.randn((n_particles, 3), dtype=dtype, device=device) * v_thermal
    
    # Normalize 4-velocity: g_μν u^μ u^ν = -1
    # For Minkowski approximation: -(u^0)² + (u^i)² = -1
    # u^0 = sqrt(1 + v²)
    v_squared = torch.sum(particles[:, 5:8]**2, dim=1)
    particles[:, 4] = torch.sqrt(1.0 + v_squared)
    
    print(f"Initialized {n_particles} particles")
    print(f"  Position spread: {radius:.1f} l_P")
    print(f"  Velocity scale: {v_thermal} c")
    
    return particles


def compute_stress_energy_tensor(particles: torch.Tensor,
                                 grid_shape=(8, 8, 8, 8),
                                 grid_spacing=10.0,
                                 particle_mass=1e-10,  # in Planck masses
                                 dtype=torch.float64,
                                 device='cpu') -> torch.Tensor:
    """
    Compute stress-energy tensor T^μν from particles using PIC method.
    
    T^μν = ρ u^μ u^ν for dust
    
    Args:
        particles: [N, 8] particle data
        grid_shape: grid dimensions
        grid_spacing: spacing in Planck lengths
        particle_mass: mass per particle in Planck masses
        dtype, device: torch parameters
    Returns:
        T: [Nt, Nx, Ny, Nz, 4, 4] stress-energy tensor
    """
    T = torch.zeros((*grid_shape, 4, 4), dtype=dtype, device=device)
    
    N = particles.shape[0]
    
    for p_idx in range(N):
        pos = particles[p_idx, 1:4]  # spatial position
        vel = particles[p_idx, 4:8]  # 4-velocity
        
        # Convert to grid indices
        grid_pos = pos / grid_spacing + torch.tensor([grid_shape[1]/2, grid_shape[2]/2, grid_shape[3]/2], 
                                                     dtype=dtype, device=device)
        
        # Trilinear interpolation weights
        i0 = torch.clamp(grid_pos[0].long(), 0, grid_shape[1] - 2)
        j0 = torch.clamp(grid_pos[1].long(), 0, grid_shape[2] - 2)
        k0 = torch.clamp(grid_pos[2].long(), 0, grid_shape[3] - 2)
        
        dx = grid_pos[0] - i0.float()
        dy = grid_pos[1] - j0.float()
        dz = grid_pos[2] - k0.float()
        
        # 8 neighboring cells
        weights = [
            (1-dx)*(1-dy)*(1-dz), dx*(1-dy)*(1-dz),
            (1-dx)*dy*(1-dz), dx*dy*(1-dz),
            (1-dx)*(1-dy)*dz, dx*(1-dy)*dz,
            (1-dx)*dy*dz, dx*dy*dz
        ]
        
        nodes = [
            (0, i0, j0, k0), (0, i0+1, j0, k0),
            (0, i0, j0+1, k0), (0, i0+1, j0+1, k0),
            (0, i0, j0, k0+1), (0, i0+1, j0, k0+1),
            (0, i0, j0+1, k0+1), (0, i0+1, j0+1, k0+1)
        ]
        
        # Deposit T^μν = m u^μ u^ν
        for weight, node in zip(weights, nodes):
            for mu in range(4):
                for nu in range(4):
                    T[node][mu, nu] += weight * particle_mass * vel[mu] * vel[nu]
    
    # Normalize by cell volume
    cell_volume = grid_spacing**3
    T = T / cell_volume
    
    return T


def run_physical_simulation(n_particles=100, 
                           n_steps=50,
                           grid_shape=(8, 8, 8, 8),
                           central_mass=0.1,
                           use_einstein_solver=False):
    """
    Run simulation with physical metric.
    
    Args:
        n_particles: number of particles
        n_steps: integration steps
        grid_shape: grid dimensions
        central_mass: central mass in Planck masses
        use_einstein_solver: whether to solve Einstein equations (slow!)
    """
    print("="*70)
    print("PHYSICAL QUANTUM GRAVITY SIMULATION")
    print("="*70)
    print(f"Particles: {n_particles}")
    print(f"Steps: {n_steps}")
    print(f"Grid: {grid_shape}")
    print(f"Central mass: {central_mass} m_P")
    print(f"Einstein solver: {'ON' if use_einstein_solver else 'OFF'}")
    print("="*70)
    
    device = 'cpu'
    dtype = torch.float64
    grid_spacing = 10.0  # Planck lengths
    
    # Initialize metric (Schwarzschild)
    g_metric = initialize_schwarzschild_metric(grid_shape, central_mass, dtype, device)
    
    # Initialize particles
    particles = initialize_particles(n_particles, grid_spacing, dtype, device)
    
    # Create metric field object
    metric_field = MetricField(g_metric, grid_spacing, dtype, device)
    
    # Logger
    logger = TrajectoryLogger("physical_simulation.h5", num_particles=n_particles)
    
    # Einstein solver (optional)
    if use_einstein_solver:
        einstein_solver = EinsteinSolver(grid_shape, dtype, device)
    
    # Time step
    dt = 0.1  # in Planck times
    
    print("\nStarting integration...")
    
    for step in range(n_steps):
        # Integrate geodesics
        particles = batch_geodesic_integration(particles, metric_field, dt)
        
        # Log
        logger.log_step(particles)
        
        # Update metric with back-reaction (every 10 steps)
        if use_einstein_solver and step % 10 == 0 and step > 0:
            print(f"\n  Step {step}: Updating metric with back-reaction...")
            
            # Compute stress-energy tensor
            T = compute_stress_energy_tensor(particles, grid_shape, grid_spacing, 
                                            particle_mass=1e-10, dtype=dtype, device=device)
            
            # Solve Einstein equations
            g_metric, diag = einstein_solver.solve_einstein_equations(
                T, g_metric, max_iterations=20, tolerance=1e-4, relaxation_param=0.05
            )
            
            # Update metric field
            metric_field = MetricField(g_metric, grid_spacing, dtype, device)
        
        # Progress
        if step % 10 == 0:
            mean_r = torch.mean(torch.norm(particles[:, 1:4], dim=1))
            mean_v = torch.mean(torch.norm(particles[:, 5:8], dim=1))
            print(f"  Step {step}/{n_steps}: <r> = {mean_r:.2f} l_P, <v> = {mean_v:.4f} c")
    
    logger.close()
    
    print("\n" + "="*70)
    print("SIMULATION COMPLETE")
    print("="*70)
    print(f"Output: physical_simulation.h5")
    
    return particles, g_metric


if __name__ == "__main__":
    # Run with Einstein solver OFF for speed (can enable for full physics)
    particles, metric = run_physical_simulation(
        n_particles=100,
        n_steps=50,
        grid_shape=(8, 8, 8, 8),
        central_mass=0.1,
        use_einstein_solver=False  # Set True for full back-reaction
    )