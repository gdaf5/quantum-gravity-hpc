"""
Hawking Radiation Calculator
Computes thermal radiation from black holes and horizons.
"""

import torch
import numpy as np
from typing import Dict, Tuple

class HawkingRadiation:
    """
    Calculate Hawking radiation from event horizons.
    
    Temperature: T_H = ℏc³/(8πGMk_B) = 1/(8πM) in Planck units
    Luminosity: L = ℏc⁶/(15360πG²M²) 
    """
    
    def __init__(self, dtype=torch.float64, device='cpu'):
        self.dtype = dtype
        self.device = device
        
        # Planck units (all = 1)
        self.c = 1.0
        self.G = 1.0
        self.hbar = 1.0
        self.k_B = 1.0
        
        print("Hawking Radiation Calculator initialized")
    
    def compute_hawking_temperature(self, M: float) -> float:
        """
        Compute Hawking temperature for black hole of mass M.
        
        T_H = ℏc³/(8πGMk_B) = 1/(8πM) in Planck units
        
        Args:
            M: black hole mass in Planck masses
        Returns:
            T_H: Hawking temperature in Planck temperature
        """
        return 1.0 / (8.0 * np.pi * M)
    
    def compute_schwarzschild_radius(self, M: float) -> float:
        """r_s = 2GM/c² = 2M in Planck units"""
        return 2.0 * M
    
    def compute_hawking_luminosity(self, M: float) -> float:
        """
        Luminosity from Hawking radiation.
        
        L = ℏc⁶/(15360πG²M²) in SI
        L = 1/(15360πM²) in Planck units
        
        Args:
            M: black hole mass in Planck masses
        Returns:
            L: luminosity in Planck power
        """
        return 1.0 / (15360.0 * np.pi * M**2)
    
    def compute_evaporation_time(self, M: float) -> float:
        """
        Time for black hole to evaporate completely.
        
        t_evap = 5120πG²M³/(ℏc⁴) = 5120πM³ in Planck units
        
        Args:
            M: initial mass in Planck masses
        Returns:
            t_evap: evaporation time in Planck times
        """
        return 5120.0 * np.pi * M**3
    
    def compute_particle_emission_rate(self, M: float, particle_mass: float = 0.0) -> float:
        """
        Emission rate of particles with given mass.
        
        Γ ~ exp(-E/T_H) for E >> T_H (Boltzmann suppression)
        
        Args:
            M: black hole mass
            particle_mass: emitted particle mass
        Returns:
            rate: emission rate (dimensionless)
        """
        T_H = self.compute_hawking_temperature(M)
        
        if particle_mass == 0.0:
            # Massless particles (photons, gravitons)
            return T_H**2  # Stefan-Boltzmann
        else:
            # Massive particles (Boltzmann suppressed)
            if particle_mass > T_H:
                return T_H**2 * np.exp(-particle_mass / T_H)
            else:
                return T_H**2
    
    def compute_entropy(self, M: float) -> float:
        """
        Bekenstein-Hawking entropy.
        
        S = (k_B c³ A)/(4ℏG) = A/4 in Planck units
        where A = 4πr_s² = 16πM²
        
        Args:
            M: black hole mass
        Returns:
            S: entropy in Planck entropy units
        """
        r_s = self.compute_schwarzschild_radius(M)
        A = 4.0 * np.pi * r_s**2
        return A / 4.0
    
    def detect_horizons(self, g_metric: torch.Tensor, 
                       grid_spacing: float = 1.0,
                       threshold: float = 0.1) -> list:
        """
        Detect apparent horizons in metric.
        
        Horizon condition: g_tt ≈ 0 (null surface)
        
        Args:
            g_metric: [Nt, Nx, Ny, Nz, 4, 4] metric tensor
            grid_spacing: grid spacing in Planck lengths
            threshold: detection threshold for |g_tt|
        Returns:
            horizons: list of horizon locations
        """
        horizons = []
        
        grid_shape = g_metric.shape[:4]
        
        for it in range(grid_shape[0]):
            for ix in range(grid_shape[1]):
                for iy in range(grid_shape[2]):
                    for iz in range(grid_shape[3]):
                        g_tt = g_metric[it, ix, iy, iz, 0, 0].item()
                        
                        # Horizon: g_tt ≈ 0
                        if abs(g_tt) < threshold:
                            # Physical coordinates
                            x = (ix - grid_shape[1]/2) * grid_spacing
                            y = (iy - grid_shape[2]/2) * grid_spacing
                            z = (iz - grid_shape[3]/2) * grid_spacing
                            r = np.sqrt(x**2 + y**2 + z**2)
                            
                            horizons.append({
                                'position': (x, y, z),
                                'radius': r,
                                'g_tt': g_tt,
                                'grid_index': (it, ix, iy, iz)
                            })
        
        return horizons
    
    def compute_unruh_temperature(self, acceleration: float) -> float:
        """
        Unruh temperature for accelerated observer.
        
        T_U = ℏa/(2πck_B) = a/(2π) in Planck units
        
        Args:
            acceleration: proper acceleration in Planck acceleration
        Returns:
            T_U: Unruh temperature
        """
        return acceleration / (2.0 * np.pi)
    
    def analyze_black_hole(self, M: float) -> Dict:
        """
        Complete analysis of black hole properties.
        
        Args:
            M: black hole mass in Planck masses
        Returns:
            dict with all properties
        """
        T_H = self.compute_hawking_temperature(M)
        r_s = self.compute_schwarzschild_radius(M)
        L = self.compute_hawking_luminosity(M)
        t_evap = self.compute_evaporation_time(M)
        S = self.compute_entropy(M)
        
        # Emission rates for different particles
        photon_rate = self.compute_particle_emission_rate(M, 0.0)
        electron_rate = self.compute_particle_emission_rate(M, 1e-22)  # electron mass in Planck units
        
        # Convert to SI for reference
        T_H_SI = T_H * 1.417e32  # Kelvin
        r_s_SI = r_s * 1.616e-35  # meters
        t_evap_SI = t_evap * 5.39e-44  # seconds
        
        return {
            'mass_planck': M,
            'temperature_planck': T_H,
            'temperature_kelvin': T_H_SI,
            'schwarzschild_radius_planck': r_s,
            'schwarzschild_radius_meters': r_s_SI,
            'luminosity_planck': L,
            'evaporation_time_planck': t_evap,
            'evaporation_time_seconds': t_evap_SI,
            'entropy_planck': S,
            'photon_emission_rate': photon_rate,
            'electron_emission_rate': electron_rate,
            'surface_gravity': 1.0 / (4.0 * M)  # κ = 1/(4M)
        }
    
    def compute_information_paradox_measure(self, 
                                           initial_entropy: float,
                                           final_entropy: float) -> Dict:
        """
        Measure information loss in black hole evaporation.
        
        Information paradox: S_initial vs S_radiation
        
        Args:
            initial_entropy: initial black hole entropy
            final_entropy: entropy of Hawking radiation
        Returns:
            dict with information measures
        """
        # Information loss
        delta_S = final_entropy - initial_entropy
        
        # Page time: when S_radiation = S_BH/2
        # This is when information starts to come out (if it does)
        
        return {
            'initial_entropy': initial_entropy,
            'final_entropy': final_entropy,
            'entropy_change': delta_S,
            'information_loss': max(0, -delta_S),  # positive if information lost
            'unitarity_violation': delta_S < 0  # True if entropy decreased
        }


def demonstrate_hawking_radiation():
    """Demonstration of Hawking radiation calculations"""
    print("="*70)
    print("HAWKING RADIATION ANALYSIS")
    print("="*70)
    
    hawking = HawkingRadiation()
    
    # Analyze different mass black holes
    masses = [0.1, 1.0, 10.0, 100.0]  # Planck masses
    
    for M in masses:
        print(f"\n{'='*70}")
        print(f"Black Hole: M = {M} m_P")
        print(f"{'='*70}")
        
        analysis = hawking.analyze_black_hole(M)
        
        print(f"  Schwarzschild radius: {analysis['schwarzschild_radius_planck']:.2f} l_P")
        print(f"                       ({analysis['schwarzschild_radius_meters']:.3e} m)")
        print(f"  Hawking temperature:  {analysis['temperature_planck']:.6f} T_P")
        print(f"                       ({analysis['temperature_kelvin']:.3e} K)")
        print(f"  Luminosity:          {analysis['luminosity_planck']:.6e} P_P")
        print(f"  Evaporation time:    {analysis['evaporation_time_planck']:.3e} t_P")
        print(f"                       ({analysis['evaporation_time_seconds']:.3e} s)")
        print(f"  Entropy:             {analysis['entropy_planck']:.3e} k_B")
        print(f"  Surface gravity:     {analysis['surface_gravity']:.6f}")
        print(f"  Photon emission:     {analysis['photon_emission_rate']:.6e}")
        print(f"  Electron emission:   {analysis['electron_emission_rate']:.6e}")
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)


if __name__ == "__main__":
    demonstrate_hawking_radiation()
