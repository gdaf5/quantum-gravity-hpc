"""
JAX Physics Engine (Scientific-Grade)
=====================================
Uses Automatic Differentiation (JAX) for exact curvature tensor calculation.

Author: wosky021@gmail.com
"""
import jax
import jax.numpy as jnp

def get_christoffel_symbols(metric_func, x):
    """
    Computes Christoffel symbols Γ^σ_{μν} at point x
    using exact automatic differentiation.
    
    Γ^σ_{μν} = 1/2 * g^{σρ} * (∂_μ g_{ρν} + ∂_ν g_{ρμ} - ∂_ρ g_{μν})
    """
    # 1. Compute metric at x
    g = metric_func(x)
    g_inv = jnp.linalg.inv(g)
    
    # 2. Compute partial derivatives ∂_ρ g_{μν} using JAX jacobian
    # Metric function returns [4, 4] for input [4]
    # Jacobian will return [4, 4, 4] -> ∂_ρ g_{μν}
    dg = jax.jacfwd(metric_func)(x)
    
    # 3. Compute Christoffel symbols
    # Γ^σ_{μν} = 0.5 * g^{σρ} * (∂_μ g_{ρν} + ∂_ν g_{ρμ} - ∂_ρ g_{μν})
    # We use jnp.einsum for index contraction (the "pro" way)
    Gamma = 0.5 * jnp.einsum('sr, mnr -> smn', g_inv, 
                             dg[:, :, :] + jnp.transpose(dg, (1, 2, 0)) - jnp.transpose(dg, (2, 0, 1)))
    
    return Gamma

# Example: Minkowski metric in JAX
def minkowski_metric(x):
    return jnp.diag(jnp.array([-1.0, 1.0, 1.0, 1.0]))

def get_riemann_tensor(metric_func, x):
    """
    Computes Riemann Curvature Tensor R^ρ_{σμν}
    R^ρ_{σμν} = ∂_μ Γ^ρ_{νσ} - ∂_ν Γ^ρ_{μσ} + Γ^ρ_{μλ}Γ^λ_{νσ} - Γ^ρ_{νλ}Γ^λ_{μσ}
    """
    # 1. Γ^ρ_{μν}
    # Мы используем функцию get_christoffel_symbols, но нужно её переделать для JAX
    # для этого определим вспомогательную функцию для Г
    def christoffel_func(x):
        return get_christoffel_symbols(metric_func, x)
    
    Gamma = christoffel_func(x)
    
    # 2. ∂_μ Γ^ρ_{νσ}
    dGamma = jax.jacobian(christoffel_func)(x) # [4, 4, 4, 4] -> ∂_μ Γ^ρ_{νσ}
    
    # 3. Riemann Tensor
    # R^ρ_{σμν} = ∂_μ Γ^ρ_{νσ} - ∂_ν Γ^ρ_{μσ} + Γ^ρ_{μλ}Γ^λ_{νσ} - Γ^ρ_{νλ}Γ^λ_{μσ}
    R = (dGamma[..., 0, :, :] - dGamma[..., 1, :, :] + 
         jnp.einsum('ρμλ, λνσ -> ρσμν', Gamma, Gamma) - 
         jnp.einsum('ρνλ, λμσ -> ρσμν', Gamma, Gamma))
    
    return R

def get_ricci_scalar(metric_func, x):
    """Computes Ricci Scalar R = g^{σν} R^μ_{σμν}"""
    R = get_riemann_tensor(metric_func, x) # [4, 4, 4, 4]
    Ricci = jnp.einsum('ρσμρ -> σμ', R)
    g = metric_func(x)
    g_inv = jnp.linalg.inv(g)
    return jnp.einsum('σν, σν ->', g_inv, Ricci)

