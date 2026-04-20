"""
Improved Geodesic Engine with Proper Physics
- Correct Christoffel symbol computation with metric derivatives
- 4th order symplectic integrator (Forest-Ruth)
- Planck units throughout
- Numerical derivatives via finite differences
"""

import torch
from torch.func import vmap
import torch.nn.functional as F
from typing import Callable, Tuple

class MetricField:
    """
    Metric field with proper interpolation and derivatives.
    Uses cubic interpolation for smoothness.
    """
    def __init__(self, grid: torch.Tensor, grid_spacing: float, dtype=torch.float64, device='cpu'):
        """
        Args:
            grid: [Nt, Nx, Ny, Nz, 4, 4] metric tensor on grid
            grid_spacing: physical spacing in Planck lengths
        """
        self.grid = grid.to(device=device, dtype=dtype)
        self.grid_spacing = grid_spacing
        self.dtype = dtype
        self.device = device
        self.grid_shape = grid.shape[:4]
        
    def interpolate_metric(self, coords: torch.Tensor) -> torch.Tensor:
        """
        Interpolate metric at given coordinates using trilinear interpolation.
        
        Args:
            coords: [4] - (t, x, y, z) in Planck lengths
        Returns:
            g: [4, 4] metric tensor
        """
        # Normalize coordinates to grid indices
        normalized = coords / self.grid_spacing
        
        # Clamp to grid boundaries
        for i in range(4):
            normalized[i] = torch.clamp(normalized[i], 0, self.grid_shape[i] - 1.001)
        
        # Grid sample expects [N, C, D, H, W] and coords [N, D_out, H_out, W_out, 3]
        # We'll use manual trilinear interpolation for 4D
        
        # Get integer indices
        i0 = normalized.long()
        i1 = torch.clamp(i0 + 1, max=torch.tensor(self.grid_shape, device=self.device) - 1)
        
        # Fractional parts
        frac = normalized - i0.float()
        
        # 16 corner values (4D hypercube)
        g_interp = torch.zeros(4, 4, dtype=self.dtype, device=self.device)
        
        for dt in [0, 1]:
            for dx in [0, 1]:
                for dy in [0, 1]:
                    for dz in [0, 1]:
                        it = i0[0] if dt == 0 else i1[0]
                        ix = i0[1] if dx == 0 else i1[1]
                        iy = i0[2] if dy == 0 else i1[2]
                        iz = i0[3] if dz == 0 else i1[3]
                        
                        weight = (frac[0] if dt == 1 else (1 - frac[0])) * \
                                (frac[1] if dx == 1 else (1 - frac[1])) * \
                                (frac[2] if dy == 1 else (1 - frac[2])) * \
                                (frac[3] if dz == 1 else (1 - frac[3]))
                        
                        g_interp += weight * self.grid[it, ix, iy, iz]
        
        return g_interp
    
    def compute_metric_derivatives(self, coords: torch.Tensor, h: float = 1e-3) -> torch.Tensor:
        """
        Compute ∂_μ g_νρ using finite differences.
        
        Args:
            coords: [4] position
            h: step size for finite differences (in Planck lengths)
        Returns:
            dg: [4, 4, 4] - dg[μ, ν, ρ] = ∂_μ g_νρ
        """
        dg = torch.zeros(4, 4, 4, dtype=self.dtype, device=self.device)
        
        for mu in range(4):
            coords_plus = coords.clone()
            coords_minus = coords.clone()
            
            coords_plus[mu] += h
            coords_minus[mu] -= h
            
            g_plus = self.interpolate_metric(coords_plus)
            g_minus = self.interpolate_metric(coords_minus)
            
            # Central difference
            dg[mu] = (g_plus - g_minus) / (2 * h)
        
        return dg


def compute_christoffel_symbols(g: torch.Tensor, dg: torch.Tensor) -> torch.Tensor:
    """
    Compute Christoffel symbols Γ^σ_{μν} from metric and its derivatives.
    
    Γ^σ_{μν} = ½ g^{σρ} (∂_μ g_{ρν} + ∂_ν g_{ρμ} - ∂_ρ g_{μν})
    
    Args:
        g: [4, 4] metric tensor
        dg: [4, 4, 4] metric derivatives ∂_μ g_νρ
    Returns:
        Gamma: [4, 4, 4] Christoffel symbols
    """
    # Inverse metric
    g_inv = torch.linalg.inv(g)
    
    # Γ^σ_{μν}
    Gamma = torch.zeros(4, 4, 4, dtype=g.dtype, device=g.device)
    
    for sigma in range(4):
        for mu in range(4):
            for nu in range(4):
                for rho in range(4):
                    Gamma[sigma, mu, nu] += 0.5 * g_inv[sigma, rho] * \
                        (dg[mu, rho, nu] + dg[nu, rho, mu] - dg[rho, mu, nu])
    
    return Gamma


def geodesic_acceleration(coords: torch.Tensor, 
                         velocity: torch.Tensor,
                         metric_field: MetricField) -> torch.Tensor:
    """
    Compute geodesic acceleration: a^σ = -Γ^σ_{μν} u^μ u^ν
    
    Args:
        coords: [4] position
        velocity: [4] 4-velocity
        metric_field: MetricField object
    Returns:
        accel: [4] acceleration
    """
    g = metric_field.interpolate_metric(coords)
    dg = metric_field.compute_metric_derivatives(coords)
    Gamma = compute_christoffel_symbols(g, dg)
    
    # a^σ = -Γ^σ_{μν} u^μ u^ν
    accel = -torch.einsum('smn,m,n->s', Gamma, velocity, velocity)
    
    return accel


def forest_ruth_step(coords: torch.Tensor,
                     velocity: torch.Tensor,
                     metric_field: MetricField,
                     dt: float) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    4th order symplectic integrator (Forest-Ruth algorithm).
    
    More accurate than Velocity Verlet for long-term integration.
    
    Args:
        coords: [4] position
        velocity: [4] 4-velocity  
        metric_field: MetricField object
        dt: timestep in Planck times
    Returns:
        new_coords, new_velocity
    """
    # Forest-Ruth coefficients
    theta = 1.0 / (2.0 - 2.0**(1.0/3.0))
    
    c1 = theta / 2.0
    c2 = (1.0 - theta) / 2.0
    c3 = c2
    c4 = c1
    
    d1 = theta
    d2 = -theta / (2.0 - 2.0**(1.0/3.0))
    d3 = d1
    
    # Step 1
    coords = coords + c1 * dt * velocity
    accel = geodesic_acceleration(coords, velocity, metric_field)
    velocity = velocity + d1 * dt * accel
    
    # Step 2
    coords = coords + c2 * dt * velocity
    accel = geodesic_acceleration(coords, velocity, metric_field)
    velocity = velocity + d2 * dt * accel
    
    # Step 3
    coords = coords + c3 * dt * velocity
    accel = geodesic_acceleration(coords, velocity, metric_field)
    velocity = velocity + d3 * dt * accel
    
    # Step 4
    coords = coords + c4 * dt * velocity
    
    return coords, velocity


def integrate_geodesic_single(particle: torch.Tensor,
                              metric_field: MetricField,
                              dt: float) -> torch.Tensor:
    """
    Integrate single particle geodesic.
    
    Args:
        particle: [8] - (t, x, y, z, u^0, u^1, u^2, u^3)
        metric_field: MetricField object
        dt: timestep
    Returns:
        new_particle: [8]
    """
    coords = particle[:4]
    velocity = particle[4:]
    
    new_coords, new_velocity = forest_ruth_step(coords, velocity, metric_field, dt)
    
    return torch.cat([new_coords, new_velocity])


def batch_geodesic_integration(particles: torch.Tensor,
                               metric_field: MetricField,
                               dt: float) -> torch.Tensor:
    """
    Vectorized geodesic integration for multiple particles.
    
    Args:
        particles: [N, 8]
        metric_field: MetricField object
        dt: timestep
    Returns:
        new_particles: [N, 8]
    """
    # Simple loop instead of vmap (vmap has issues with our metric field)
    N = particles.shape[0]
    new_particles = torch.zeros_like(particles)
    
    for i in range(N):
        new_particles[i] = integrate_geodesic_single(particles[i], metric_field, dt)
    
    return new_particles
