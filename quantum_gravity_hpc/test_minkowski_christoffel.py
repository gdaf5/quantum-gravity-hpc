import jax
import jax.numpy as jnp
from jax_engine.jax_engine import get_christoffel_symbols

def minkowski_metric(x):
    return jnp.diag(jnp.array([-1.0, 1.0, 1.0, 1.0]))

def test_minkowski():
    x = jnp.array([0.0, 0.0, 0.0, 0.0])
    Gamma = get_christoffel_symbols(minkowski_metric, x)
    
    # Christoffel symbols for Minkowski space should be zero
    is_all_zero = jnp.allclose(Gamma, 0.0, atol=1e-6)
    
    print(f"Minkowski Christoffel symbols: \n{Gamma}")
    print(f"Test Passed: {is_all_zero}")
    
    if not is_all_zero:
        raise ValueError("Christoffel symbols for Minkowski should be zero!")

if __name__ == "__main__":
    test_minkowski()
