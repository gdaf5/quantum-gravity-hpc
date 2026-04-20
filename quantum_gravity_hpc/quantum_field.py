"""
Quantum Field Theory on Curved Spacetime
Implements scalar field quantization in curved background.
"""

import torch
import numpy as np
from typing import Tuple, Dict

class QuantumFieldCurvedSpace:
    """
    Quantum scalar field φ on curved spacetime.
    
    Implements:
    - Klein-Gordon equation: (□ - m² - ξR)φ = 0
    - Vacuum fluctuations: ⟨φ²⟩
    - Stress-energy tensor: T_μν = ∂_μφ ∂_νφ - ½ g_μν (g^ρσ ∂_ρφ ∂_σφ + m²φ²)
    """
    
    def __init__(self, grid_shape=(8, 8, 8, 8), 
                 field_mass=1.0,  # in Planck masses
                 xi=0.0,  # coupling to curvature (0=minimal, 1/6=conformal)
                 dtype=torch.float64,
                 device='cpu'):
        
        self.grid_shape = grid_shape
        self.m = field_mass
        self.xi = xi
        self.dtype = dtype
        self.device = device
        
        # Field configuration
        self.phi = torch.zeros(grid_shape, dtype=dtype, device=device)
        self.pi = torch.zeros(grid_shape, dtype=dtype, device=device)  # conjugate momentum
        
        # Initialize with vacuum fluctuations
        self._initialize_vacuum_state()
        
        print(f"Quantum Field initialized:")
        print(f"  Grid: {grid_shape}")
        print(f"  Mass: {field_mass} m_P")
        print(f"  Coupling ξ: {xi}")
        print(f"  Type: {'Conformal' if abs(xi - 1/6) < 1e-6 else 'Minimal' if xi == 0 else 'Non-minimal'}")
    
    def _initialize_vacuum_state(self):
        """
        Initialize field with vacuum fluctuations.
        
        In Planck units: ⟨φ²⟩ ~ 1/l_P³ ~ 1
        """
        # Vacuum fluctuation amplitude
        vacuum_amplitude = 1.0 / np.sqrt(np.prod(self.grid_shape))
        
        # Random Gaussian fluctuations
        self.phi = torch.randn(self.grid_shape, dtype=self.dtype, device=self.device) * vacuum_amplitude
        self.pi = torch.randn(self.grid_shape, dtype=self.dtype, device=self.device) * vacuum_amplitude
        
        print(f"  Vacuum fluctuations: σ(φ) = {vacuum_amplitude:.6e}")
    
    def compute_klein_gordon_operator(self, g_metric: torch.Tensor, 
                                     ricci_scalar: torch.Tensor,
                                     grid_spacing: float = 1.0) -> torch.Tensor:
        """
        Compute Klein-Gordon operator acting on field.
        
        □φ = (1/√-g) ∂_μ(√-g g^μν ∂_ν φ)
        
        Args:
            g_metric: [Nt, Nx, Ny, Nz, 4, 4] metric tensor
            ricci_scalar: [Nt, Nx, Ny, Nz] Ricci scalar R
            grid_spacing: grid spacing in Planck lengths
        Returns:
            KG_phi: [Nt, Nx, Ny, Nz] result of operator
        """
        KG_phi = torch.zeros(self.grid_shape, dtype=self.dtype, device=self.device)
        
        for it in range(self.grid_shape[0]):
            for ix in range(self.grid_shape[1]):
                for iy in range(self.grid_shape[2]):
                    for iz in range(self.grid_shape[3]):
                        g = g_metric[it, ix, iy, iz]
                        g_inv = torch.linalg.inv(g)
                        
                        # √-g (determinant)
                        g_det = torch.linalg.det(g)
                        sqrt_g = torch.sqrt(torch.abs(g_det))
                        
                        # Compute ∂_μ φ using finite differences
                        dphi = self._compute_field_derivatives(it, ix, iy, iz, grid_spacing)
                        
                        # g^μν ∂_ν φ
                        g_inv_dphi = torch.einsum('mn,n->m', g_inv, dphi)
                        
                        # ∂_μ (√-g g^μν ∂_ν φ)
                        # Approximate using finite differences
                        box_phi = 0.0
                        
                        for mu in range(4):
                            # Forward and backward points
                            idx_p = [it, ix, iy, iz]
                            idx_m = [it, ix, iy, iz]
                            
                            idx_p[mu] = min(idx_p[mu] + 1, self.grid_shape[mu] - 1)
                            idx_m[mu] = max(idx_m[mu] - 1, 0)
                            
                            # √-g g^μν ∂_ν φ at neighboring points
                            g_p = g_metric[idx_p[0], idx_p[1], idx_p[2], idx_p[3]]
                            g_m = g_metric[idx_m[0], idx_m[1], idx_m[2], idx_m[3]]
                            
                            sqrt_g_p = torch.sqrt(torch.abs(torch.linalg.det(g_p)))
                            sqrt_g_m = torch.sqrt(torch.abs(torch.linalg.det(g_m)))
                            
                            dphi_p = self._compute_field_derivatives(idx_p[0], idx_p[1], idx_p[2], idx_p[3], grid_spacing)
                            dphi_m = self._compute_field_derivatives(idx_m[0], idx_m[1], idx_m[2], idx_m[3], grid_spacing)
                            
                            g_inv_p = torch.linalg.inv(g_p)
                            g_inv_m = torch.linalg.inv(g_m)
                            
                            term_p = sqrt_g_p * torch.einsum('mn,n->', g_inv_p[mu:mu+1, :], dphi_p)
                            term_m = sqrt_g_m * torch.einsum('mn,n->', g_inv_m[mu:mu+1, :], dphi_m)
                            
                            box_phi += (term_p - term_m) / (2.0 * grid_spacing)
                        
                        box_phi = box_phi / sqrt_g
                        
                        # Klein-Gordon: (□ - m² - ξR)φ = 0
                        R = ricci_scalar[it, ix, iy, iz]
                        KG_phi[it, ix, iy, iz] = box_phi - self.m**2 * self.phi[it, ix, iy, iz] - \
                                                 self.xi * R * self.phi[it, ix, iy, iz]
        
        return KG_phi
    
    def _compute_field_derivatives(self, it: int, ix: int, iy: int, iz: int, 
                                   h: float = 1.0) -> torch.Tensor:
        """Compute ∂_μ φ at grid point using finite differences"""
        dphi = torch.zeros(4, dtype=self.dtype, device=self.device)
        
        indices = [it, ix, iy, iz]
        
        for mu in range(4):
            idx_plus = indices.copy()
            idx_minus = indices.copy()
            
            idx_plus[mu] = min(idx_plus[mu] + 1, self.grid_shape[mu] - 1)
            idx_minus[mu] = max(idx_minus[mu] - 1, 0)
            
            phi_plus = self.phi[idx_plus[0], idx_plus[1], idx_plus[2], idx_plus[3]]
            phi_minus = self.phi[idx_minus[0], idx_minus[1], idx_minus[2], idx_minus[3]]
            
            dphi[mu] = (phi_plus - phi_minus) / (2.0 * h)
        
        return dphi
    
    def evolve_field(self, g_metric: torch.Tensor, 
                    ricci_scalar: torch.Tensor,
                    dt: float,
                    grid_spacing: float = 1.0):
        """
        Evolve quantum field using Klein-Gordon equation.
        
        Uses leapfrog integration:
        π^{n+1/2} = π^n + (dt/2) * KG(φ^n)
        φ^{n+1} = φ^n + dt * π^{n+1/2}
        π^{n+1} = π^{n+1/2} + (dt/2) * KG(φ^{n+1})
        
        Args:
            g_metric: metric tensor
            ricci_scalar: Ricci scalar
            dt: timestep
            grid_spacing: grid spacing
        """
        # Half step for momentum
        KG_phi = self.compute_klein_gordon_operator(g_metric, ricci_scalar, grid_spacing)
        self.pi = self.pi + 0.5 * dt * KG_phi
        
        # Full step for field
        self.phi = self.phi + dt * self.pi
        
        # Half step for momentum
        KG_phi = self.compute_klein_gordon_operator(g_metric, ricci_scalar, grid_spacing)
        self.pi = self.pi + 0.5 * dt * KG_phi
    
    def compute_stress_energy_tensor(self, g_metric: torch.Tensor,
                                    grid_spacing: float = 1.0) -> torch.Tensor:
        """
        Compute quantum stress-energy tensor.
        
        T_μν = ∂_μφ ∂_νφ - ½ g_μν (g^ρσ ∂_ρφ ∂_σφ + m²φ²)
        
        Args:
            g_metric: [Nt, Nx, Ny, Nz, 4, 4] metric
            grid_spacing: grid spacing
        Returns:
            T: [Nt, Nx, Ny, Nz, 4, 4] stress-energy tensor
        """
        T = torch.zeros((*self.grid_shape, 4, 4), dtype=self.dtype, device=self.device)
        
        for it in range(self.grid_shape[0]):
            for ix in range(self.grid_shape[1]):
                for iy in range(self.grid_shape[2]):
                    for iz in range(self.grid_shape[3]):
                        g = g_metric[it, ix, iy, iz]
                        g_inv = torch.linalg.inv(g)
                        
                        # ∂_μ φ
                        dphi = self._compute_field_derivatives(it, ix, iy, iz, grid_spacing)
                        
                        # g^ρσ ∂_ρφ ∂_σφ
                        kinetic = torch.einsum('rs,r,s->', g_inv, dphi, dphi)
                        
                        # φ²
                        phi_sq = self.phi[it, ix, iy, iz]**2
                        
                        # T_μν = ∂_μφ ∂_νφ - ½ g_μν (kinetic + m²φ²)
                        for mu in range(4):
                            for nu in range(4):
                                T[it, ix, iy, iz, mu, nu] = dphi[mu] * dphi[nu] - \
                                    0.5 * g[mu, nu] * (kinetic + self.m**2 * phi_sq)
        
        return T
    
    def compute_vacuum_expectation_value(self) -> Dict:
        """
        Compute vacuum expectation values.
        
        Returns:
            dict with ⟨φ²⟩, ⟨(∂φ)²⟩, etc.
        """
        phi_squared = torch.mean(self.phi**2).item()
        pi_squared = torch.mean(self.pi**2).item()
        
        # Compute ⟨(∂φ)²⟩
        grad_phi_sq = 0.0
        count = 0
        
        for it in range(self.grid_shape[0]):
            for ix in range(self.grid_shape[1]):
                for iy in range(self.grid_shape[2]):
                    for iz in range(self.grid_shape[3]):
                        dphi = self._compute_field_derivatives(it, ix, iy, iz)
                        grad_phi_sq += torch.sum(dphi**2).item()
                        count += 1
        
        grad_phi_sq /= count
        
        return {
            'phi_squared': phi_squared,
            'pi_squared': pi_squared,
            'grad_phi_squared': grad_phi_sq,
            'field_energy': 0.5 * (pi_squared + grad_phi_sq + self.m**2 * phi_squared)
        }
