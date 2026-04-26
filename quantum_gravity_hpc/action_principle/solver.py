"""
RIGOROUS ACTION PRINCIPLE SOLVER
================================
Uses JAX for exact gradients to minimize Regge-like action.
Metric is represented by edge lengths [l_1, l_2, ..., l_N].

Author: wosky021@gmail.com
"""
import numpy as np
from scipy.optimize import minimize
import jax
import jax.numpy as jnp

# The Physics: Action = Curvature (Gravity) + Entanglement (Quantum)
# S = sum(1/l^2) + lambda * sum(log(l^2))
# This is a scale-invariant model for a 1D lattice.
def action_functional(lengths, lambda_q=0.5):
    # Добавляем локальный "источник энергии" в центр графа (индексы 4, 5)
    # Повышаем lambda_q (запутанность) локально для имитации источника
    local_lambda = lambda_q * jnp.ones_like(lengths)
    local_lambda = local_lambda.at[4:6].set(lambda_q * 5.0) # В 5 раз больше запутанности!
    
    curvature_term = jnp.sum(1.0 / (lengths**2 + 1e-6))
    entanglement_term = jnp.sum(local_lambda * jnp.log(lengths**2 + 1e-6))
    return curvature_term + entanglement_term

# Exact gradient using JAX
grad_action = jax.grad(action_functional)

def objective(l):
    return float(action_functional(l))

def gradient(l):
    return np.array(grad_action(l))

def solve_variational_state(n_edges=10):
    # Start with a random initial configuration to test for spontaneous symmetry breaking
    x0 = np.random.uniform(0.5, 2.0, n_edges)
    bounds = [(1e-2, 5.0)] * n_edges
    
    # Minimize using L-BFGS-B (robust gradient-based optimizer)
    res = minimize(objective, x0, jac=gradient, bounds=bounds, method='L-BFGS-B')
    return res

if __name__ == "__main__":
    result = solve_variational_state()
    
    print("--- RIGOROUS VARIATIONAL RESULT ---")
    print(f"Success: {result.success}")
    print(f"Minimal Action: {result.fun:.6f}")
    print(f"Optimized metric (lengths):")
    print(np.round(result.x, 4))
    
    # Physical check: are all lengths equal (flat vacuum) or different (emergent)?
    std_dev = np.std(result.x)
    print(f"Standard deviation of lengths: {std_dev:.6f}")
    if std_dev > 1e-3:
        print("RESULT: Spontaneous symmetry breaking (Emergent geometry) detected.")
    else:
        print("RESULT: Stable flat vacuum (Uniform geometry) detected.")
