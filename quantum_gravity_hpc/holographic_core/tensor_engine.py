"""
Tensor Network Core (MERA-based)
================================
Uses Quimb to compute entanglement entropy and holographic measures.

Author: wosky021@gmail.com
"""
import quimb.tensor as qtn
import numpy as np

class TensorEngine:
    def __init__(self, n_sites: int = 16):
        self.n_sites = n_sites
        # Create a simple MPS
        self.mera = qtn.MPS_rand_state(n_sites, bond_dim=4)
        
    def get_entanglement_entropy(self, site_idx: int) -> float:
        """Compute von Neumann entropy of a site."""
        # Entropy requires an integer bond index (0 to L-1)
        return self.mera.entropy(site_idx)

    def compute_holographic_measure(self) -> float:
        """Measure global entanglement structure."""
        return self.mera.bond_dims_mean()
