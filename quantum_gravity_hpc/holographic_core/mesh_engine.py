"""
Dynamic Adaptive Mesh Refinement (AMR) Engine
=============================================
Generates a spatial mesh where point density is proportional to
local entanglement density. Higher entanglement = higher resolution.

Author: wosky021@gmail.com
"""
import numpy as np
import torch

class AdaptiveMesh:
    def __init__(self, bounds: np.ndarray, base_resolution: int = 10):
        self.bounds = bounds # [[xmin, xmax], [ymin, ymax], ...]
        self.base_resolution = base_resolution

    def generate_mesh(self, entanglement_field: np.ndarray) -> np.ndarray:
        """
        Generate adaptive mesh based on entanglement density field.
        Higher entanglement density -> more points.
        """
        # Simplification: treat entanglement_field as density map
        # Return points where density is high
        threshold = np.mean(entanglement_field)
        indices = np.argwhere(entanglement_field > threshold)
        return indices.astype(float)
