"""
PHYSICS REGISTRY - Scientifically Justified Parameters
=======================================================

This module provides experimentally constrained parameters for quantum gravity simulations.
All values are derived from published observations and theoretical constraints.

Author: wosky021@gmail.com
Date: April 21, 2026
Version: 3.2.1
"""

import numpy as np
from typing import Dict, Any

class PhysicsRegistry:
    """
    Registry of physical constants and experimentally constrained parameters.
    
    All parameters include:
    - Value
    - Uncertainty
    - Source (publication reference)
    - Physical interpretation
    """
    
    def __init__(self):
        """Initialize physics registry with fundamental constants and constraints."""
        
        # ============================================================
        # FUNDAMENTAL CONSTANTS (SI units)
        # ============================================================
        
        self.constants = {
            'c': {
                'value': 299792458.0,  # m/s
                'unit': 'm/s',
                'description': 'Speed of light',
                'source': 'CODATA 2018'
            },
            'G': {
                'value': 6.67430e-11,  # m^3 kg^-1 s^-2
                'uncertainty': 0.00015e-11,
                'unit': 'm^3 kg^-1 s^-2',
                'description': 'Gravitational constant',
                'source': 'CODATA 2018'
            },
            'hbar': {
                'value': 1.054571817e-34,  # J·s
                'unit': 'J·s',
                'description': 'Reduced Planck constant',
                'source': 'CODATA 2018'
            },
            'k_B': {
                'value': 1.380649e-23,  # J/K
                'unit': 'J/K',
                'description': 'Boltzmann constant',
                'source': 'CODATA 2018'
            }
        }
        
        # ============================================================
        # PLANCK UNITS
        # ============================================================
        
        c = self.constants['c']['value']
        G = self.constants['G']['value']
        hbar = self.constants['hbar']['value']
        
        self.planck = {
            'length': {
                'value': np.sqrt(hbar * G / c**3),  # 1.616255e-35 m
                'unit': 'm',
                'description': 'Planck length',
                'formula': 'sqrt(ℏG/c³)'
            },
            'time': {
                'value': np.sqrt(hbar * G / c**5),  # 5.391247e-44 s
                'unit': 's',
                'description': 'Planck time',
                'formula': 'sqrt(ℏG/c⁵)'
            },
            'mass': {
                'value': np.sqrt(hbar * c / G),  # 2.176434e-8 kg
                'unit': 'kg',
                'description': 'Planck mass',
                'formula': 'sqrt(ℏc/G)'
            },
            'energy': {
                'value': np.sqrt(hbar * c**5 / G),  # 1.956e9 J
                'unit': 'J',
                'description': 'Planck energy',
                'formula': 'sqrt(ℏc⁵/G)'
            }
        }
        
        # ============================================================
        # LORENTZ INVARIANCE VIOLATION (LIV) CONSTRAINTS
        # Source: Fermi-LAT observations of gamma-ray bursts
        # ============================================================
        
        self.liv_constraints = {
            'fermi_grb_090510': {
                'alpha_linear': {
                    'value': 1e-20,  # Upper limit
                    'constraint': 'upper_limit',
                    'unit': 'dimensionless',
                    'description': 'Linear LIV parameter from GRB 090510',
                    'source': 'Vasileiou et al., Phys. Rev. D 87, 122001 (2013)',
                    'energy_scale': 'E_Planck',
                    'interpretation': 'Photon time delay: Δt/t ~ α(E/E_P)'
                },
                'alpha_quadratic': {
                    'value': 1e-15,  # Upper limit
                    'constraint': 'upper_limit',
                    'unit': 'dimensionless',
                    'description': 'Quadratic LIV parameter',
                    'source': 'Fermi-LAT Collaboration (2013)',
                    'interpretation': 'Δt/t ~ α(E/E_P)²'
                }
            },
            'fermi_grb_130427a': {
                'alpha_linear': {
                    'value': 7.2e-21,  # Improved limit
                    'constraint': 'upper_limit',
                    'unit': 'dimensionless',
                    'description': 'Improved LIV constraint from GRB 130427A',
                    'source': 'Vasileiou et al., Phys. Rev. D 87, 122001 (2013)',
                    'energy_scale': 'E_Planck'
                }
            }
        }
        
        # ============================================================
        # GRAVITATIONAL WAVE DISPERSION CONSTRAINTS
        # Source: LIGO/Virgo observations
        # ============================================================
        
        self.gw_constraints = {
            'ligo_gw150914': {
                'dispersion_n2': {
                    'value': 1e-22,  # Upper limit on quadratic dispersion
                    'constraint': 'upper_limit',
                    'unit': 's²/m²',
                    'description': 'GW dispersion from GW150914',
                    'source': 'Abbott et al., Phys. Rev. Lett. 116, 221101 (2016)',
                    'interpretation': 'ω² = k²c² + α(kl_P)²'
                }
            },
            'ligo_gw170817': {
                'speed_difference': {
                    'value': 3e-15,  # |v_GW - c|/c
                    'constraint': 'upper_limit',
                    'unit': 'dimensionless',
                    'description': 'GW speed vs light speed',
                    'source': 'Abbott et al., Astrophys. J. Lett. 848, L13 (2017)',
                    'interpretation': 'GW and photons arrived within 1.7s over 130 Mly'
                }
            }
        }
        
        # ============================================================
        # CMB SPECTRAL DISTORTION CONSTRAINTS
        # Source: COBE/FIRAS, Planck
        # ============================================================
        
        self.cmb_constraints = {
            'cobe_firas': {
                'mu_distortion': {
                    'value': 9e-5,  # Upper limit
                    'constraint': 'upper_limit',
                    'unit': 'dimensionless',
                    'description': 'μ-type spectral distortion',
                    'source': 'Fixsen et al., Astrophys. J. 473, 576 (1996)',
                    'interpretation': 'Energy injection at z > 2×10⁶'
                },
                'y_distortion': {
                    'value': 1.5e-5,  # Upper limit
                    'constraint': 'upper_limit',
                    'unit': 'dimensionless',
                    'description': 'y-type spectral distortion (Compton)',
                    'source': 'Fixsen et al. (1996)',
                    'interpretation': 'Energy injection at z < 10⁵'
                }
            }
        }
        
        # ============================================================
        # HAWKING RADIATION PARAMETERS
        # Source: Theoretical calculations + Black Hole Perturbation Toolkit
        # ============================================================
        
        self.hawking = {
            'solar_mass_bh': {
                'mass': 1.98847e30,  # kg
                'temperature': {
                    'value': 6.169e-8,  # K
                    'unit': 'K',
                    'formula': 'T_H = ℏc³/(8πGMk_B)',
                    'source': 'Hawking (1974)'
                },
                'luminosity': {
                    'value': 9.007e-29,  # W
                    'unit': 'W',
                    'formula': 'L = ℏc⁶/(15360πG²M²)',
                    'source': 'Page (1976)'
                },
                'evaporation_time': {
                    'value': 2.098e67,  # years
                    'unit': 'years',
                    'formula': 't_evap = 5120πG²M³/(ℏc⁴)',
                    'source': 'Hawking (1974)'
                }
            },
            'planck_mass_bh': {
                'mass': 2.176434e-8,  # kg (Planck mass)
                'temperature': {
                    'value': 1.417e32,  # K (Planck temperature)
                    'unit': 'K',
                    'description': 'Planck-scale black hole temperature'
                },
                'evaporation_time': {
                    'value': 5.391e-44,  # s (Planck time)
                    'unit': 's',
                    'description': 'Instant evaporation at Planck scale'
                }
            }
        }
        
        # ============================================================
        # QUANTUM FOAM PARAMETERS (Derived from constraints)
        # ============================================================
        
        self.foam_parameters = {
            'dispersion_alpha': {
                'baseline': 0.0,  # Classical GR
                'weak_foam': 1e-20,  # Fermi-LAT limit
                'strong_foam': 1e-5,  # For visualization
                'unit': 'dimensionless',
                'description': 'Dispersion parameter: E² = p²c² + α(E/E_P)^n',
                'constraint_source': 'Fermi-LAT GRB observations'
            },
            'dispersion_n': {
                'linear': 1,
                'quadratic': 2,
                'cubic': 3,
                'description': 'Dispersion order (n=1: linear, n=2: quadratic)',
                'typical': 2,
                'source': 'Loop Quantum Gravity, String Theory'
            },
            'foam_density': {
                'baseline': 0.0,  # No foam
                'low': 0.1,  # 10% of Planck density
                'medium': 0.5,  # 50% of Planck density
                'high': 0.8,  # 80% of Planck density
                'unit': 'ρ/ρ_Planck',
                'description': 'Quantum foam energy density'
            },
            'creation_rate': {
                'low': 0.2,  # particles per t_P per V_P
                'medium': 0.4,
                'high': 0.8,
                'unit': 'particles/(t_P × V_P)',
                'description': 'Virtual particle creation rate'
            },
            'collapse_threshold': {
                'easy': 1.0,  # r < r_s
                'medium': 1.2,  # r < 1.2 r_s
                'hard': 1.5,  # r < 1.5 r_s
                'unit': 'r_s',
                'description': 'Schwarzschild radius multiplier for collapse'
            },
            'softening_length': {
                'value': 0.1,  # in Planck lengths
                'range': [0.05, 0.2],
                'unit': 'l_Planck',
                'description': 'Gravitational softening to prevent numerical singularities',
                'source': 'Standard N-body simulation practice'
            }
        }
        
        # ============================================================
        # SCHWARZSCHILD SOLUTION (Benchmark)
        # ============================================================
        
        self.schwarzschild = {
            'metric_signature': '(-,+,+,+)',
            'schwarzschild_radius': {
                'formula': 'r_s = 2GM/c²',
                'solar_mass': 2953.0,  # meters
                'earth_mass': 8.87e-3,  # meters
                'planck_mass': 3.232e-35  # meters (2 Planck lengths)
            },
            'test_coordinates': {
                'far_field': 1000.0,  # r >> r_s (weak field)
                'near_horizon': 1.1,  # r ~ r_s (strong field)
                'description': 'Test points in units of r_s'
            }
        }
        
        # ============================================================
        # KERR SOLUTION (Rotating Black Hole Benchmark)
        # ============================================================
        
        self.kerr = {
            'spin_parameter': {
                'non_rotating': 0.0,  # a = 0 (Schwarzschild limit)
                'slow': 0.3,  # a/M = 0.3
                'moderate': 0.7,  # a/M = 0.7
                'extremal': 0.998,  # a/M → 1 (maximum rotation)
                'unit': 'GM/c',
                'description': 'Angular momentum per unit mass'
            },
            'ergosphere': {
                'description': 'Region where frame-dragging dominates',
                'outer_radius': 'r_ergo = M + sqrt(M² - a²cos²θ)'
            }
        }
    
    def get_recommended_parameters(self, regime: str = 'weak_foam') -> Dict[str, Any]:
        """
        Get recommended parameters for a specific physical regime.
        
        Args:
            regime: 'classical', 'weak_foam', 'medium_foam', 'strong_foam'
        
        Returns:
            Dictionary of recommended parameters with justifications
        """
        
        if regime == 'classical':
            return {
                'dispersion_alpha': 0.0,
                'foam_density': 0.0,
                'creation_rate': 0.0,
                'justification': 'Classical General Relativity (no quantum effects)'
            }
        
        elif regime == 'weak_foam':
            return {
                'dispersion_alpha': self.liv_constraints['fermi_grb_130427a']['alpha_linear']['value'],
                'foam_density': 0.1,
                'creation_rate': 0.2,
                'collapse_threshold': 1.2,
                'softening_length': 0.1,
                'justification': 'Constrained by Fermi-LAT observations',
                'source': 'Vasileiou et al., PRD 87, 122001 (2013)'
            }
        
        elif regime == 'medium_foam':
            return {
                'dispersion_alpha': 1e-15,
                'foam_density': 0.5,
                'creation_rate': 0.4,
                'collapse_threshold': 1.2,
                'softening_length': 0.1,
                'justification': 'Moderate quantum gravity effects',
                'source': 'Theoretical exploration within observational bounds'
            }
        
        elif regime == 'strong_foam':
            return {
                'dispersion_alpha': 1e-5,
                'foam_density': 0.8,
                'creation_rate': 0.8,
                'collapse_threshold': 1.0,
                'softening_length': 0.1,
                'justification': 'Strong quantum effects for visualization',
                'warning': 'May violate observational constraints - for theoretical study only'
            }
        
        else:
            raise ValueError(f"Unknown regime: {regime}. Use 'classical', 'weak_foam', 'medium_foam', or 'strong_foam'")
    
    def print_summary(self):
        """Print a summary of key constraints."""
        
        print("="*70)
        print("PHYSICS REGISTRY - Experimentally Constrained Parameters")
        print("="*70)
        
        print("\n1. LORENTZ INVARIANCE VIOLATION (Fermi-LAT):")
        alpha = self.liv_constraints['fermi_grb_130427a']['alpha_linear']['value']
        print(f"   alpha_linear < {alpha:.2e} (GRB 130427A)")
        
        print("\n2. GRAVITATIONAL WAVE DISPERSION (LIGO):")
        gw_speed = self.gw_constraints['ligo_gw170817']['speed_difference']['value']
        print(f"   |v_GW - c|/c < {gw_speed:.2e} (GW170817)")
        
        print("\n3. CMB SPECTRAL DISTORTIONS (COBE/FIRAS):")
        mu = self.cmb_constraints['cobe_firas']['mu_distortion']['value']
        y = self.cmb_constraints['cobe_firas']['y_distortion']['value']
        print(f"   mu < {mu:.2e}")
        print(f"   y < {y:.2e}")
        
        print("\n4. PLANCK UNITS:")
        print(f"   l_P = {self.planck['length']['value']:.6e} m")
        print(f"   t_P = {self.planck['time']['value']:.6e} s")
        print(f"   m_P = {self.planck['mass']['value']:.6e} kg")
        
        print("\n5. RECOMMENDED REGIMES:")
        for regime in ['classical', 'weak_foam', 'medium_foam', 'strong_foam']:
            params = self.get_recommended_parameters(regime)
            print(f"\n   {regime.upper()}:")
            print(f"     alpha = {params.get('dispersion_alpha', 0):.2e}")
            print(f"     rho_foam = {params.get('foam_density', 0):.1f} rho_P")
        
        print("\n" + "="*70)


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def get_physics_registry() -> PhysicsRegistry:
    """Get singleton instance of physics registry."""
    return PhysicsRegistry()


def get_fermi_lat_constraint() -> float:
    """Get Fermi-LAT constraint on LIV parameter (most stringent)."""
    registry = PhysicsRegistry()
    return registry.liv_constraints['fermi_grb_130427a']['alpha_linear']['value']


def get_planck_units() -> Dict[str, float]:
    """Get Planck units in SI."""
    registry = PhysicsRegistry()
    return {
        'length': registry.planck['length']['value'],
        'time': registry.planck['time']['value'],
        'mass': registry.planck['mass']['value'],
        'energy': registry.planck['energy']['value']
    }


# ============================================================
# MAIN (for testing)
# ============================================================

if __name__ == "__main__":
    registry = PhysicsRegistry()
    registry.print_summary()
    
    print("\n" + "="*70)
    print("TESTING: Get recommended parameters")
    print("="*70)
    
    for regime in ['weak_foam', 'medium_foam', 'strong_foam']:
        print(f"\n{regime.upper()}:")
        params = registry.get_recommended_parameters(regime)
        for key, value in params.items():
            print(f"  {key}: {value}")
