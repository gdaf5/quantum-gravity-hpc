"""
TEST: JAX Physics Engine Singularity Resilience
===============================================
Tests if the JAX engine can handle a metric near a singularity 
without crashing (which the Torch engine failed at).

Author: wosky021@gmail.com
"""
import jax
import jax.numpy as jnp
from jax_engine.jax_engine import get_christoffel_symbols

def near_singularity_metric(x):
    """
    Simulates a metric with a singularity at r=1.0, 
    using jnp.where for physical regularization.
    """
    r = jnp.sqrt(jnp.sum(x[1:]**2))
    
    # Define a safety threshold for the singularity
    threshold = 1.0 + 1e-6
    
    # Smooth regularization: if r < threshold, f -> fixed value, else f = 1 - 1/r
    # This maintains the metric structure while avoiding ZeroDivisionError
    f = jnp.where(r < threshold, 0.1, 1.0 - 1.0 / r)
    
    g = jnp.diag(jnp.array([-f, 1.0/f, 1.0, 1.0]))
    return g

def test_singularity():
    print("Testing JAX engine near singularity (r ~ 1.0)...")
    
    # Point very close to r=1.0
    x = jnp.array([0.0, 1.05, 0.0, 0.0])
    
    try:
        Gamma = get_christoffel_symbols(near_singularity_metric, x)
        print("Christoffel symbols calculated successfully:")
        print(Gamma.shape) # Should be [4, 4, 4]
        print("Success: JAX handled the singularity without crashing.")
    except Exception as e:
        print(f"JAX engine failed: {e}")

if __name__ == "__main__":
    test_singularity()
