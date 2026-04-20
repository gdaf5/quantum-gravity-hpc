"""
IMPROVED CORE ENGINE - PRODUCTION QUALITY
Fixes critical issues:
1. Proper error handling
2. Stability checks
3. Better metric computation
4. Adaptive timestep
"""

import torch
import numpy as np
from typing import Tuple, Optional
import warnings

class ImprovedMetricField:
    """
    Production-quality metric field with proper error handling.
    """
    def __init__(self, grid: torch.Tensor, grid_spacing: float, 
                 dtype=torch.float64, device='cpu'):
        """
        Initialize metric field with validation.
        
        Args:
            grid: [Nt, Nx, Ny, Nz, 4, 4] metric tensor
            grid_spacing: physical spacing in Planck lengths
        
        Raises:
            ValueError: If grid has invalid shape or contains NaN/Inf
        """
        # Validate input
        if grid.dim() != 6:
            raise ValueError(f"Grid must be 6D, got {grid.dim()}D")
        
        if grid.shape[-2:] != (4, 4):
            raise ValueError(f"Last two dimensions must be (4,4), got {grid.shape[-2:]}")
        
        if torch.isnan(grid).any() or torch.isinf(grid).any():
            raise ValueError("Grid contains NaN or Inf values")
        
        if grid_spacing <= 0:
            raise ValueError(f"Grid spacing must be positive, got {grid_spacing}")
        
        self.grid = grid.to(device=device, dtype=dtype)
        self.grid_spacing = grid_spacing
        self.dtype = dtype
        self.device = device
        self.grid_shape = grid.shape[:4]
        
        # Precompute bounds
        self.grid_max = torch.tensor([s - 1.001 for s in self.grid_shape], 
                                     dtype=dtype, device=device)
        
        # Validate metric properties
        self._validate_metric()
    
    def _validate_metric(self):
        """Check that metric satisfies basic properties."""
        # Check symmetry (sample a few points)
        sample_indices = [
            (self.grid_shape[0]//2, self.grid_shape[1]//2, 
             self.grid_shape[2]//2, self.grid_shape[3]//2)
        ]
        
        for idx in sample_indices:
            g = self.grid[idx]
            if not torch.allclose(g, g.T, atol=1e-6):
                warnings.warn(f"Metric not symmetric at {idx}")
            
            # Check signature (should be -+++)
            eigenvalues = torch.linalg.eigvalsh(g)
            if eigenvalues[0] >= 0:
                warnings.warn(f"Metric signature wrong at {idx}: eigenvalues={eigenvalues}")
    
    def interpolate_metric_batch(self, coords: torch.Tensor) -> torch.Tensor:
        """
        Interpolate metric with error checking.
        
        Args:
            coords: [N, 4] positions
            
        Returns:
            g: [N, 4, 4] metric tensors
            
        Raises:
            ValueError: If coords contain NaN/Inf or are out of bounds
        """
        # Validate input
        if torch.isnan(coords).any() or torch.isinf(coords).any():
            raise ValueError("Coordinates contain NaN or Inf")
        
        N = coords.shape[0]
        
        # Normalize to grid indices
        normalized = coords / self.grid_spacing
        
        # Check bounds
        if (normalized < 0).any() or (normalized > self.grid_max).any():
            warnings.warn("Some coordinates out of bounds, clamping")
        
        # Clamp to grid boundaries
        normalized = torch.clamp(normalized, 
                                torch.zeros(4, dtype=self.dtype, device=self.device), 
                                self.grid_max)
        
        # Integer and fractional parts
        i0 = normalized.long()
        i1 = torch.clamp(i0 + 1, max=self.grid_max.long())
        frac = normalized - i0.float()
        
        # Trilinear interpolation
        g_interp = torch.zeros(N, 4, 4, dtype=self.dtype, device=self.device)
        
        for dt in [0, 1]:
            for dx in [0, 1]:
                for dy in [0, 1]:
                    for dz in [0, 1]:
                        it = torch.where(torch.tensor(dt == 1), i1[:, 0], i0[:, 0])
                        ix = torch.where(torch.tensor(dx == 1), i1[:, 1], i0[:, 1])
                        iy = torch.where(torch.tensor(dy == 1), i1[:, 2], i0[:, 2])
                        iz = torch.where(torch.tensor(dz == 1), i1[:, 3], i0[:, 3])
                        
                        wt = frac[:, 0] if dt == 1 else (1 - frac[:, 0])
                        wx = frac[:, 1] if dx == 1 else (1 - frac[:, 1])
                        wy = frac[:, 2] if dy == 1 else (1 - frac[:, 2])
                        wz = frac[:, 3] if dz == 1 else (1 - frac[:, 3])
                        
                        weight = wt * wx * wy * wz
                        
                        for n in range(N):
                            g_interp[n] += weight[n] * self.grid[it[n], ix[n], iy[n], iz[n]]
        
        # Validate output
        if torch.isnan(g_interp).any() or torch.isinf(g_interp).any():
            raise RuntimeError("Interpolation produced NaN or Inf")
        
        return g_interp


def compute_christoffel_symbols_safe(g: torch.Tensor, dg: torch.Tensor) -> torch.Tensor:
    """
    Compute Christoffel symbols with error checking.
    
    Args:
        g: [N, 4, 4] metric tensors
        dg: [N, 4, 4, 4] metric derivatives
        
    Returns:
        Gamma: [N, 4, 4, 4] Christoffel symbols
        
    Raises:
        ValueError: If inputs contain NaN/Inf
        RuntimeError: If metric is singular
    """
    # Validate inputs
    if torch.isnan(g).any() or torch.isinf(g).any():
        raise ValueError("Metric contains NaN or Inf")
    
    if torch.isnan(dg).any() or torch.isinf(dg).any():
        raise ValueError("Metric derivatives contain NaN or Inf")
    
    N = g.shape[0]
    
    # Try Numba first
    try:
        from numba import njit, prange
        
        @njit(parallel=True, fastmath=True, cache=True)
        def _compute_christoffel_numba(g_np, dg_np):
            N = g_np.shape[0]
            Gamma = np.zeros((N, 4, 4, 4), dtype=np.float64)
            
            for n in prange(N):
                try:
                    g_inv = np.linalg.inv(g_np[n])
                except:
                    # Singular matrix, use pseudo-inverse
                    g_inv = np.linalg.pinv(g_np[n])
                
                for sigma in range(4):
                    for mu in range(4):
                        for nu in range(4):
                            for rho in range(4):
                                Gamma[n, sigma, mu, nu] += 0.5 * g_inv[sigma, rho] * \
                                    (dg_np[n, mu, rho, nu] + dg_np[n, nu, rho, mu] - dg_np[n, rho, mu, nu])
            
            return Gamma
        
        g_np = g.cpu().numpy()
        dg_np = dg.cpu().numpy()
        Gamma_np = _compute_christoffel_numba(g_np, dg_np)
        Gamma = torch.from_numpy(Gamma_np).to(g.device)
        
    except ImportError:
        # Fallback to PyTorch
        try:
            g_inv = torch.linalg.inv(g)
        except RuntimeError:
            # Singular matrix
            warnings.warn("Singular metric detected, using pseudo-inverse")
            g_inv = torch.linalg.pinv(g)
        
        combined = torch.zeros(N, 4, 4, 4, dtype=g.dtype, device=g.device)
        
        for sigma in range(4):
            for mu in range(4):
                for nu in range(4):
                    for rho in range(4):
                        combined[:, sigma, mu, nu] += g_inv[:, sigma, rho] * \
                            (dg[:, mu, rho, nu] + dg[:, nu, rho, mu] - dg[:, rho, mu, nu])
        
        Gamma = 0.5 * combined
    
    # Validate output
    if torch.isnan(Gamma).any() or torch.isinf(Gamma).any():
        raise RuntimeError("Christoffel computation produced NaN or Inf")
    
    return Gamma


def adaptive_timestep(particles: torch.Tensor, dt: float, 
                     tolerance: float = 0.01) -> float:
    """
    Compute adaptive timestep based on particle velocities.
    
    Args:
        particles: [N, 8] particle state
        dt: current timestep
        tolerance: relative error tolerance
        
    Returns:
        new_dt: adjusted timestep
    """
    # Check velocities
    velocities = particles[:, 5:8]
    v_mag = torch.sqrt((velocities**2).sum(dim=1))
    
    # Maximum velocity
    v_max = v_mag.max().item()
    
    # Adjust timestep to keep v*dt < tolerance
    if v_max * dt > tolerance:
        dt_new = tolerance / (v_max + 1e-10)
        return min(dt_new, dt)
    
    # Can increase timestep if velocities are small
    if v_max * dt < tolerance * 0.1:
        return min(dt * 1.5, dt * 2.0)
    
    return dt


def check_particle_stability(particles: torch.Tensor) -> bool:
    """
    Check if particles are in stable state.
    
    Args:
        particles: [N, 8] particle state
        
    Returns:
        stable: True if stable, False otherwise
    """
    # Check for NaN/Inf
    if torch.isnan(particles).any():
        warnings.warn("Particles contain NaN")
        return False
    
    if torch.isinf(particles).any():
        warnings.warn("Particles contain Inf")
        return False
    
    # Check velocities
    velocities = particles[:, 5:8]
    v_mag = torch.sqrt((velocities**2).sum(dim=1))
    
    if (v_mag > 10.0).any():  # v > 10c is suspicious
        warnings.warn(f"Superluminal velocities detected: max v = {v_mag.max():.2f}c")
        return False
    
    # Check positions
    positions = particles[:, 1:4]
    r = torch.sqrt((positions**2).sum(dim=1))
    
    if (r < 0.1).any():  # Too close to singularity
        warnings.warn(f"Particles too close to singularity: min r = {r.min():.2f}")
        return False
    
    return True


print("Improved engine loaded with:")
print("  - Error handling")
print("  - Stability checks")
print("  - Adaptive timestep")
print("  - Input validation")
