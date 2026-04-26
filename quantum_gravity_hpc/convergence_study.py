import jax
import jax.numpy as jnp
from bssn_state import BSSNState
from bssn_rhs import compute_bssn_rhs_grid, enforce_constraints
from initial_conditions import get_gw_initial_data
from geometry import compute_hamiltonian_constraint
import time

# Функция одного шага (повторно используем из main_simulation)
def perform_step(state, alpha, beta, dx, dt):
    def get_full_rhs(s, a, b):
        return compute_bssn_rhs_grid(s, a, b, dx)

    k1_s, k1_a, k1_b = get_full_rhs(state, alpha, beta)
    k2_s, k2_a, k2_b = get_full_rhs(
        jax.tree_util.tree_map(lambda x, k: x + 0.5 * dt * k, state, k1_s),
        alpha + 0.5 * dt * k1_a, beta + 0.5 * dt * k1_b
    )
    k3_s, k3_a, k3_b = get_full_rhs(
        jax.tree_util.tree_map(lambda x, k: x + 0.5 * dt * k, state, k2_s),
        alpha + 0.5 * dt * k2_a, beta + 0.5 * dt * k2_b
    )
    k4_s, k4_a, k4_b = get_full_rhs(
        jax.tree_util.tree_map(lambda x, k: x + dt * k, state, k3_s),
        alpha + dt * k3_a, beta + dt * k3_b
    )
    
    new_state = jax.tree_util.tree_map(
        lambda s, c1, c2, c3, c4: s + (dt/6.0)*(c1 + 2*c2 + 2*c3 + c4),
        state, k1_s, k2_s, k3_s, k4_s
    )
    new_alpha = alpha + (dt/6.0)*(k1_a + 2*k2_a + 2*k3_a + k4_a)
    new_beta = beta + (dt/6.0)*(k1_b + 2*k2_b + 2*k3_b + k4_b)
    
    return enforce_constraints(new_state), new_alpha, new_beta

def run_convergence():
    results = []
    # Фиксируем размер области, dx = L / N
    L = 3.2 
    steps = 100
    
    for N in [16, 32, 64]:
        dx = L / N
        dt = 0.0001 * (N / 32) # Масштабируем dt
        
        state, alpha, beta = get_gw_initial_data(N, dx, amplitude=1e-4)
        
        start = time.time()
        for _ in range(steps):
            state, alpha, beta = perform_step(state, alpha, beta, dx, dt)
        end = time.time()
        
        h_err = compute_hamiltonian_constraint(state, dx)
        results.append((N, h_err, (end-start)/steps))
        print(f"N={N} | H-err: {h_err:.4e} | Время шага: {(end-start)/steps:.4f}с")

if __name__ == "__main__":
    run_convergence()
