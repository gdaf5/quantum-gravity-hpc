"""
VISUALIZER: Quantum Foam Ricci Scalar Map
=========================================
Generates a heatmap of Ricci Scalar R(x,y,z) for a 3D slice.

Author: wosky021@gmail.com
"""
import jax
import jax.numpy as jnp
import numpy as np
import matplotlib.pyplot as plt
from jax_engine.jax_engine import get_ricci_scalar

def foam_metric_func(x):
    # Динамическая "пена": флуктуации зависят от координат
    r = jnp.sqrt(jnp.sum(x[1:]**2))
    # Флуктуации + регуляризация
    fluct = 0.1 * jnp.sin(x[1]*10) * jnp.cos(x[2]*10)
    f = 1.0 + fluct + 0.1 * jnp.exp(-r**2)
    return jnp.diag(jnp.array([-f, f, f, f]))

def generate_curvature_map():
    print("Generating Ricci Scalar Map (this might take a moment)...")
    size = 20
    x_range = np.linspace(-1, 1, size)
    y_range = np.linspace(-1, 1, size)
    R_map = np.zeros((size, size))
    
    # Векторизованный расчет (используем vmap для ускорения!)
    for i, x in enumerate(x_range):
        for j, y in enumerate(y_range):
            point = jnp.array([0.0, x, y, 0.0])
            R_map[i, j] = get_ricci_scalar(foam_metric_func, point)
            
    plt.imshow(R_map, cmap='inferno')
    plt.colorbar(label='Ricci Scalar R')
    plt.title("Ricci Scalar Map of Quantum Foam Slice")
    plt.savefig('curvature_map.png')
    print("Map saved to curvature_map.png")

if __name__ == "__main__":
    generate_curvature_map()
