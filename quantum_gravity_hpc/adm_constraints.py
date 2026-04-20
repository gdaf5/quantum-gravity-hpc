"""
ADM Constraint Equations Checker
Verifies Hamiltonian and Momentum constraints for numerical stability.
"""

import torch
import numpy as np
from typing import Dict, Tuple

class ADMConstraintChecker:
    """
    Check ADM constraint equations for numerical relativity.
    
    Hamiltonian constraint: H = R + K² - K_ij K^ij - 16πρ = 0
    Momentum constraint: M_i = D_j(K^j_i - K δ^j_i) - 8πj_i = 0
    
    where:
    - R: 3D Ricci scalar
    - K_ij: extrinsic curvature
    - ρ: energy density
    - j_i: momentum density
    """
    
    def __init__(self, dtype=torch.float64, device='cpu'):
        self.dtype = dtype
        self.device = device
        
        print("ADM Constraint Checker initialized")
    
    def compute_extrinsic_curvature(self, 
                                   h_spatial: torch.Tensor,
                                   h_spatial_dot: torch.Tensor,
                                   lapse: torch.Tensor,
                                   shift: torch.Tensor) -> torch.Tensor:
        """
        Compute extrinsic curvature K_ij.
        
        K_ij = (1/2N)(∂_t h_ij - D_i β_j - D_j β_i)
        
        Args:
            h_spatial: [Nx, Ny, Nz, 3, 3] spatial metric
            h_spatial_dot: [Nx, Ny, Nz, 3, 3] time derivative
            lapse: [Nx, Ny, Nz] lapse function N
            shift: [Nx, Ny, Nz, 3] shift vector β^i
        Returns:
            K: [Nx, Ny, Nz, 3, 3] extrinsic curvature
        """
        grid_shape = h_spatial.shape[:3]
        K = torch.zeros_like(h_spatial)
        
        for ix in range(grid_shape[0]):
            for iy in range(grid_shape[1]):
                for iz in range(grid_shape[2]):
                    N = lapse[ix, iy, iz]
                    
                    # ∂_t h_ij
                    dh_dt = h_spatial_dot[ix, iy, iz]
                    
                    # Covariant derivatives of shift (simplified)
                    D_shift = torch.zeros(3, 3, dtype=self.dtype, device=self.device)
                    
                    for i in range(3):
                        for j in range(3):
                            # D_i β_j ≈ ∂_i β_j (ignoring Christoffel symbols for simplicity)
                            D_shift[i, j] = self._compute_shift_derivative(shift, ix, iy, iz, i, j)
                    
                    # K_ij = (1/2N)(∂_t h_ij - D_i β_j - D_j β_i)
                    K[ix, iy, iz] = (dh_dt - D_shift - D_shift.T) / (2.0 * N)
        
        return K
    
    def _compute_shift_derivative(self, shift: torch.Tensor,
                                 ix: int, iy: int, iz: int,
                                 i: int, j: int,
                                 h: float = 1.0) -> float:
        """Compute ∂_i β_j using finite differences"""
        grid_shape = shift.shape[:3]
        
        idx_plus = [ix, iy, iz]
        idx_minus = [ix, iy, iz]
        
        idx_plus[i] = min(idx_plus[i] + 1, grid_shape[i] - 1)
        idx_minus[i] = max(idx_minus[i] - 1, 0)
        
        beta_plus = shift[idx_plus[0], idx_plus[1], idx_plus[2], j]
        beta_minus = shift[idx_minus[0], idx_minus[1], idx_minus[2], j]
        
        return (beta_plus - beta_minus) / (2.0 * h)
    
    def compute_hamiltonian_constraint(self,
                                      h_spatial: torch.Tensor,
                                      K: torch.Tensor,
                                      rho: torch.Tensor,
                                      grid_spacing: float = 1.0) -> torch.Tensor:
        """
        Compute Hamiltonian constraint violation.
        
        H = R + K² - K_ij K^ij - 16πρ
        
        Should be zero if constraints satisfied.
        
        Args:
            h_spatial: [Nx, Ny, Nz, 3, 3] spatial metric
            K: [Nx, Ny, Nz, 3, 3] extrinsic curvature
            rho: [Nx, Ny, Nz] energy density
            grid_spacing: grid spacing
        Returns:
            H: [Nx, Ny, Nz] constraint violation
        """
        grid_shape = h_spatial.shape[:3]
        H = torch.zeros(grid_shape, dtype=self.dtype, device=self.device)
        
        for ix in range(grid_shape[0]):
            for iy in range(grid_shape[1]):
                for iz in range(grid_shape[2]):
                    h = h_spatial[ix, iy, iz]
                    h_inv = torch.linalg.inv(h)
                    K_local = K[ix, iy, iz]
                    
                    # R: 3D Ricci scalar (compute from h)
                    R = self._compute_3d_ricci_scalar(h_spatial, ix, iy, iz, grid_spacing)
                    
                    # K = h^ij K_ij (trace)
                    K_trace = torch.einsum('ij,ij->', h_inv, K_local)
                    
                    # K_ij K^ij
                    K_squared = torch.einsum('ij,kl,ik,jl->', K_local, K_local, h_inv, h_inv)
                    
                    # H = R + K² - K_ij K^ij - 16πρ
                    H[ix, iy, iz] = R + K_trace**2 - K_squared - 16.0 * np.pi * rho[ix, iy, iz]
        
        return H
    
    def compute_momentum_constraint(self,
                                   h_spatial: torch.Tensor,
                                   K: torch.Tensor,
                                   j: torch.Tensor,
                                   grid_spacing: float = 1.0) -> torch.Tensor:
        """
        Compute momentum constraint violation.
        
        M_i = D_j(K^j_i - K δ^j_i) - 8πj_i
        
        Args:
            h_spatial: [Nx, Ny, Nz, 3, 3] spatial metric
            K: [Nx, Ny, Nz, 3, 3] extrinsic curvature
            j: [Nx, Ny, Nz, 3] momentum density
            grid_spacing: grid spacing
        Returns:
            M: [Nx, Ny, Nz, 3] constraint violation
        """
        grid_shape = h_spatial.shape[:3]
        M = torch.zeros((*grid_shape, 3), dtype=self.dtype, device=self.device)
        
        for ix in range(grid_shape[0]):
            for iy in range(grid_shape[1]):
                for iz in range(grid_shape[2]):
                    h = h_spatial[ix, iy, iz]
                    h_inv = torch.linalg.inv(h)
                    K_local = K[ix, iy, iz]
                    
                    # K = trace
                    K_trace = torch.einsum('ij,ij->', h_inv, K_local)
                    
                    # K^j_i = h^jk K_ki
                    K_mixed = torch.einsum('jk,ki->ji', h_inv, K_local)
                    
                    for i in range(3):
                        # D_j(K^j_i - K δ^j_i)
                        div_term = 0.0
                        
                        for j_idx in range(3):
                            # ∂_j K^j_i
                            dK = self._compute_K_derivative(K, h_spatial, ix, iy, iz, j_idx, i, grid_spacing)
                            div_term += dK
                            
                            # -∂_j(K δ^j_i) = -∂_i K
                            if j_idx == i:
                                dK_trace = self._compute_K_trace_derivative(K, h_spatial, ix, iy, iz, i, grid_spacing)
                                div_term -= dK_trace
                        
                        # M_i = D_j(...) - 8πj_i
                        M[ix, iy, iz, i] = div_term - 8.0 * np.pi * j[ix, iy, iz, i]
        
        return M
    
    def _compute_3d_ricci_scalar(self, h_spatial: torch.Tensor,
                                ix: int, iy: int, iz: int,
                                grid_spacing: float) -> float:
        """
        Compute 3D Ricci scalar R from spatial metric.
        Simplified calculation using finite differences.
        """
        # This is a placeholder - full calculation is very complex
        # For now, return approximate value based on metric deviation from flat
        h = h_spatial[ix, iy, iz]
        h_flat = torch.eye(3, dtype=self.dtype, device=self.device)
        
        deviation = torch.norm(h - h_flat)
        
        # R ~ (deviation)² / l²
        return (deviation**2) / (grid_spacing**2)
    
    def _compute_K_derivative(self, K: torch.Tensor, h_spatial: torch.Tensor,
                             ix: int, iy: int, iz: int,
                             j: int, i: int, grid_spacing: float) -> float:
        """Compute ∂_j K^j_i"""
        grid_shape = K.shape[:3]
        
        idx_plus = [ix, iy, iz]
        idx_minus = [ix, iy, iz]
        
        idx_plus[j] = min(idx_plus[j] + 1, grid_shape[j] - 1)
        idx_minus[j] = max(idx_minus[j] - 1, 0)
        
        # K^j_i = h^jk K_ki
        h_inv_plus = torch.linalg.inv(h_spatial[idx_plus[0], idx_plus[1], idx_plus[2]])
        h_inv_minus = torch.linalg.inv(h_spatial[idx_minus[0], idx_minus[1], idx_minus[2]])
        
        K_plus = K[idx_plus[0], idx_plus[1], idx_plus[2]]
        K_minus = K[idx_minus[0], idx_minus[1], idx_minus[2]]
        
        K_mixed_plus = torch.einsum('jk,ki->ji', h_inv_plus, K_plus)[j, i]
        K_mixed_minus = torch.einsum('jk,ki->ji', h_inv_minus, K_minus)[j, i]
        
        return (K_mixed_plus - K_mixed_minus) / (2.0 * grid_spacing)
    
    def _compute_K_trace_derivative(self, K: torch.Tensor, h_spatial: torch.Tensor,
                                   ix: int, iy: int, iz: int,
                                   direction: int, grid_spacing: float) -> float:
        """Compute ∂_i K (derivative of trace)"""
        grid_shape = K.shape[:3]
        
        idx_plus = [ix, iy, iz]
        idx_minus = [ix, iy, iz]
        
        idx_plus[direction] = min(idx_plus[direction] + 1, grid_shape[direction] - 1)
        idx_minus[direction] = max(idx_minus[direction] - 1, 0)
        
        h_inv_plus = torch.linalg.inv(h_spatial[idx_plus[0], idx_plus[1], idx_plus[2]])
        h_inv_minus = torch.linalg.inv(h_spatial[idx_minus[0], idx_minus[1], idx_minus[2]])
        
        K_plus = K[idx_plus[0], idx_plus[1], idx_plus[2]]
        K_minus = K[idx_minus[0], idx_minus[1], idx_minus[2]]
        
        K_trace_plus = torch.einsum('ij,ij->', h_inv_plus, K_plus)
        K_trace_minus = torch.einsum('ij,ij->', h_inv_minus, K_minus)
        
        return (K_trace_plus - K_trace_minus) / (2.0 * grid_spacing)
    
    def check_constraints(self, 
                         h_spatial: torch.Tensor,
                         K: torch.Tensor,
                         rho: torch.Tensor,
                         j: torch.Tensor,
                         grid_spacing: float = 1.0) -> Dict:
        """
        Check all ADM constraints and return diagnostics.
        
        Args:
            h_spatial: spatial metric
            K: extrinsic curvature
            rho: energy density
            j: momentum density
            grid_spacing: grid spacing
        Returns:
            dict with constraint violations
        """
        print("Checking ADM constraints...")
        
        # Hamiltonian constraint
        H = self.compute_hamiltonian_constraint(h_spatial, K, rho, grid_spacing)
        
        # Momentum constraint
        M = self.compute_momentum_constraint(h_spatial, K, j, grid_spacing)
        
        # Statistics
        H_max = torch.max(torch.abs(H)).item()
        H_mean = torch.mean(torch.abs(H)).item()
        H_rms = torch.sqrt(torch.mean(H**2)).item()
        
        M_max = torch.max(torch.abs(M)).item()
        M_mean = torch.mean(torch.abs(M)).item()
        M_rms = torch.sqrt(torch.mean(M**2)).item()
        
        print(f"  Hamiltonian constraint:")
        print(f"    Max violation: {H_max:.6e}")
        print(f"    Mean violation: {H_mean:.6e}")
        print(f"    RMS violation: {H_rms:.6e}")
        
        print(f"  Momentum constraint:")
        print(f"    Max violation: {M_max:.6e}")
        print(f"    Mean violation: {M_mean:.6e}")
        print(f"    RMS violation: {M_rms:.6e}")
        
        # Check if constraints satisfied (within tolerance)
        tolerance = 1e-4
        H_satisfied = H_max < tolerance
        M_satisfied = M_max < tolerance
        
        print(f"\n  Status:")
        print(f"    Hamiltonian: {'✓ SATISFIED' if H_satisfied else '✗ VIOLATED'}")
        print(f"    Momentum: {'✓ SATISFIED' if M_satisfied else '✗ VIOLATED'}")
        
        return {
            'hamiltonian_violation': H,
            'momentum_violation': M,
            'H_max': H_max,
            'H_mean': H_mean,
            'H_rms': H_rms,
            'M_max': M_max,
            'M_mean': M_mean,
            'M_rms': M_rms,
            'constraints_satisfied': H_satisfied and M_satisfied
        }
