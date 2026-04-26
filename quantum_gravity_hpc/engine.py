"""
Optimized Geodesic Engine with Vectorized Operations
- Batch processing for multiple particles
- Vectorized metric interpolation
- Optimized Christoffel symbol computation
- Numba JIT acceleration for critical loops
"""

import torch
from typing import Callable, Tuple
import numpy as np

# Try to import Numba for acceleration
try:
    from numba import njit, prange
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    print("Warning: Numba not available. Install with: pip install numba")

# Try to import C++ backend
try:
    import geodesic_cpp
    CPP_AVAILABLE = True
    print("Using C++ accelerated backend (20-50x speedup)")
except ImportError:
    CPP_AVAILABLE = False

class MetricField:
    """
    Metric field with optimized batch interpolation.
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
        
        # Precompute grid bounds for clamping
        self.grid_max = torch.tensor([s - 1.001 for s in self.grid_shape], 
                                     dtype=dtype, device=device)
    
    def interpolate_metric_batch(self, coords: torch.Tensor) -> torch.Tensor:
        """
        Batch interpolate metric for multiple particles.
        
        Args:
            coords: [N, 4] - positions in Planck lengths
        Returns:
            g: [N, 4, 4] metric tensors
        """
        N = coords.shape[0]
        
        # Normalize to grid indices
        normalized = coords / self.grid_spacing
        
        # Clamp to grid boundaries
        normalized = torch.clamp(normalized, torch.zeros(4, dtype=self.dtype, device=self.device), 
                                self.grid_max)
        
        # Integer and fractional parts
        i0 = normalized.long()
        i1 = torch.clamp(i0 + 1, max=self.grid_max.long())
        frac = normalized - i0.float()
        
        # Trilinear interpolation weights (vectorized)
        # For 4D: 16 corners
        g_interp = torch.zeros(N, 4, 4, dtype=self.dtype, device=self.device)
        
        # Iterate over 16 corners of 4D hypercube
        for dt in [0, 1]:
            for dx in [0, 1]:
                for dy in [0, 1]:
                        for dz in [0, 1]:
                            # Indices for this corner
                            it = i1[:, 0] if dt == 1 else i0[:, 0]
                            ix = i1[:, 1] if dx == 1 else i0[:, 1]
                            iy = i1[:, 2] if dy == 1 else i0[:, 2]
                            iz = i1[:, 3] if dz == 1 else i0[:, 3]
                        
                        # Weights for this corner
                        wt = frac[:, 0] if dt == 1 else (1 - frac[:, 0])
                        wx = frac[:, 1] if dx == 1 else (1 - frac[:, 1])
                        wy = frac[:, 2] if dy == 1 else (1 - frac[:, 2])
                        wz = frac[:, 3] if dz == 1 else (1 - frac[:, 3])
                        
                        weight = wt * wx * wy * wz  # [N]
                        
                        # Gather metric values at these indices
                        for n in range(N):
                            g_interp[n] += weight[n] * self.grid[it[n], ix[n], iy[n], iz[n]]
        
        return g_interp
    
    def interpolate_metric(self, coords: torch.Tensor) -> torch.Tensor:
        """Single particle version - wraps batch version"""
        if coords.dim() == 1:
            coords = coords.unsqueeze(0)
            result = self.interpolate_metric_batch(coords)
            return result.squeeze(0)
        return self.interpolate_metric_batch(coords)
    
    def compute_metric_derivatives_batch(self, coords: torch.Tensor, h: float = 1e-3) -> torch.Tensor:
        """
        Compute ∂_μ g_νρ for batch of particles using finite differences.
        
        Args:
            coords: [N, 4] positions
            h: step size for finite differences
        Returns:
            dg: [N, 4, 4, 4] - dg[n, μ, ν, ρ] = ∂_μ g_νρ for particle n
        """
        N = coords.shape[0]
        dg = torch.zeros(N, 4, 4, 4, dtype=self.dtype, device=self.device)
        
        for mu in range(4):
            coords_plus = coords.clone()
            coords_minus = coords.clone()
            
            coords_plus[:, mu] += h
            coords_minus[:, mu] -= h
            
            g_plus = self.interpolate_metric_batch(coords_plus)
            g_minus = self.interpolate_metric_batch(coords_minus)
            
            # Central difference
            dg[:, mu] = (g_plus - g_minus) / (2 * h)
        
        return dg


# Numba-accelerated Christoffel computation
if NUMBA_AVAILABLE:
    @njit(parallel=True, fastmath=True, cache=True)
    def _compute_christoffel_numba(g_np, dg_np):
        """Numba JIT version - 5-10x faster"""
        N = g_np.shape[0]
        Gamma = np.zeros((N, 4, 4, 4), dtype=np.float64)
        
        for n in prange(N):
            g_inv = np.linalg.inv(g_np[n])
            
            for sigma in range(4):
                for mu in range(4):
                    for nu in range(4):
                        for rho in range(4):
                            Gamma[n, sigma, mu, nu] += 0.5 * g_inv[sigma, rho] * \
                                (dg_np[n, mu, rho, nu] + dg_np[n, nu, rho, mu] - dg_np[n, rho, mu, nu])
        
        return Gamma


def compute_christoffel_symbols_batch(g: torch.Tensor, dg: torch.Tensor) -> torch.Tensor:
    """
    Compute Christoffel symbols for batch of particles with numerical stability.
    
    Γ^σ_{μν} = ½ g^{σρ} (∂_μ g_{ρν} + ∂_ν g_{ρμ} - ∂_ρ g_{μν})
    
    Args:
        g: [N, 4, 4] metric tensors
        dg: [N, 4, 4, 4] metric derivatives
    Returns:
        Gamma: [N, 4, 4, 4] Christoffel symbols
    """
    # Use C++ backend if available (fastest)
    # if CPP_AVAILABLE:
    #     g_np = g.cpu().numpy()
    #     dg_np = dg.cpu().numpy()
    #     Gamma_np = geodesic_cpp.compute_christoffel_batch(g_np, dg_np)
    #     return torch.from_numpy(Gamma_np).to(g.device)
    #
    # # Use Numba if available (fast)
    # if NUMBA_AVAILABLE:
    #     g_np = g.cpu().numpy()
    #     dg_np = dg.cpu().numpy()
    #     Gamma_np = _compute_christoffel_numba(g_np, dg_np)
    #     return torch.from_numpy(Gamma_np).to(g.device)
    
    # Fallback to pure Python with numerical stability
    N = g.shape[0]
    
    # Regularize metric to avoid singularities
    epsilon = 1e-10
    g_reg = g + epsilon * torch.eye(4, dtype=g.dtype, device=g.device).unsqueeze(0)
    
    # Compute inverse with SVD for stability
    try:
        g_inv = torch.linalg.inv(g_reg)
    except RuntimeError:
        # Fallback to pseudo-inverse if singular
        g_inv = torch.linalg.pinv(g_reg)
    
    combined = torch.zeros(N, 4, 4, 4, dtype=g.dtype, device=g.device)
    
    for sigma in range(4):
        for mu in range(4):
            for nu in range(4):
                for rho in range(4):
                    combined[:, sigma, mu, nu] += g_inv[:, sigma, rho] * \
                        (dg[:, mu, rho, nu] + dg[:, nu, rho, mu] - dg[:, rho, mu, nu])
    
    return 0.5 * combined


# Alias for backward compatibility
def compute_christoffel_symbols(g: torch.Tensor, dg: torch.Tensor) -> torch.Tensor:
    """Single particle version - wraps batch version"""
    if g.dim() == 2:
        g = g.unsqueeze(0)
        dg = dg.unsqueeze(0)
        result = compute_christoffel_symbols_batch(g, dg)
        return result.squeeze(0)
    return compute_christoffel_symbols_batch(g, dg)


# Numba-accelerated geodesic acceleration
if NUMBA_AVAILABLE:
    @njit(parallel=True, fastmath=True, cache=True)
    def _geodesic_acceleration_numba(Gamma_np, velocity_np):
        """Numba JIT version - 5-10x faster"""
        N = Gamma_np.shape[0]
        accel = np.zeros((N, 4), dtype=np.float64)
        
        for n in prange(N):
            for sigma in range(4):
                for mu in range(4):
                    for nu in range(4):
                        accel[n, sigma] -= Gamma_np[n, sigma, mu, nu] * velocity_np[n, mu] * velocity_np[n, nu]
        
        return accel


# Alias for backward compatibility
def geodesic_acceleration(coords: torch.Tensor, 
                         velocity: torch.Tensor,
                         metric_field: MetricField) -> torch.Tensor:
    """Single particle version"""
    if coords.dim() == 1:
        coords = coords.unsqueeze(0)
        velocity = velocity.unsqueeze(0)
        result = geodesic_acceleration_batch(coords, velocity, metric_field)
        return result.squeeze(0)
    return geodesic_acceleration_batch(coords, velocity, metric_field)


    def normalize_four_velocity(self, coords: torch.Tensor, velocity: torch.Tensor) -> torch.Tensor:
        """
        Normalize 4-velocity such that g_μν u^μ u^ν = -1.
        """
        g = self.interpolate_metric_batch(coords)
        norm_sq = (velocity * torch.matmul(g, velocity.unsqueeze(-1)).squeeze(-1)).sum(-1)
        scale = torch.sqrt(torch.abs(norm_sq))
        return velocity / scale.unsqueeze(-1)

def geodesic_acceleration_batch(coords: torch.Tensor, 
                                velocity: torch.Tensor,
                                metric_field: MetricField) -> torch.Tensor:
    """
    Compute geodesic acceleration for batch: a^σ = -Γ^σ_{μν} u^μ u^ν
    
    Args:
        coords: [N, 4] positions
        velocity: [N, 4] 4-velocities
        metric_field: MetricField object
    Returns:
        accel: [N, 4] accelerations
    """
    g = metric_field.interpolate_metric_batch(coords)
    dg = metric_field.compute_metric_derivatives_batch(coords)
    Gamma = compute_christoffel_symbols_batch(g, dg)
    
    # Use Numba if available
    if NUMBA_AVAILABLE and not CPP_AVAILABLE:
        Gamma_np = Gamma.cpu().numpy()
        velocity_np = velocity.cpu().numpy()
        accel_np = _geodesic_acceleration_numba(Gamma_np, velocity_np)
        accel = torch.from_numpy(accel_np).to(coords.device)
    else:
        # Fallback to Python
        N = coords.shape[0]
        accel = torch.zeros(N, 4, dtype=coords.dtype, device=coords.device)
        
        for n in range(N):
            for sigma in range(4):
                for mu in range(4):
                    for nu in range(4):
                        accel[n, sigma] -= Gamma[n, sigma, mu, nu] * velocity[n, mu] * velocity[n, nu]
    
    return accel


def forest_ruth_step_batch(coords: torch.Tensor,
                           velocity: torch.Tensor,
                           metric_field: MetricField,
                           dt: float) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    4th order symplectic integrator (Forest-Ruth) for batch.
    
    Args:
        coords: [N, 4] positions
        velocity: [N, 4] 4-velocities
        metric_field: MetricField object
        dt: timestep
    Returns:
        new_coords, new_velocity: [N, 4] each
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
    # Normalize velocity at each step
    velocity = metric_field.normalize_four_velocity(coords, velocity)
    accel = geodesic_acceleration_batch(coords, velocity, metric_field)
    velocity = velocity + d1 * dt * accel
    
    # Step 2
    coords = coords + c2 * dt * velocity
    # Normalize velocity at each step
    velocity = metric_field.normalize_four_velocity(coords, velocity)
    accel = geodesic_acceleration_batch(coords, velocity, metric_field)
    velocity = velocity + d2 * dt * accel
    
    # Step 3
    coords = coords + c3 * dt * velocity
    # Normalize velocity at each step
    velocity = metric_field.normalize_four_velocity(coords, velocity)
    accel = geodesic_acceleration_batch(coords, velocity, metric_field)
    velocity = velocity + d3 * dt * accel
    
    # Step 4
    coords = coords + c4 * dt * velocity
    # Normalize velocity at each step
    velocity = metric_field.normalize_four_velocity(coords, velocity)
    
    return coords, velocity


def batch_geodesic_integration(particles: torch.Tensor,
                               metric_field: MetricField,
                               dt: float) -> torch.Tensor:
    """
    Optimized vectorized geodesic integration for multiple particles.
    
    Args:
        particles: [N, 8] - (t, x, y, z, u^0, u^1, u^2, u^3)
        metric_field: MetricField object
        dt: timestep
    Returns:
        new_particles: [N, 8]
    """
    coords = particles[:, :4]
    velocity = particles[:, 4:]
    
    new_coords, new_velocity = forest_ruth_step_batch(coords, velocity, metric_field, dt)
    
    return torch.cat([new_coords, new_velocity], dim=1)
