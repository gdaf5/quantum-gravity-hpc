import jax
import jax.numpy as jnp
from initial_conditions import get_gw_initial_data
from bssn_rhs import compute_bssn_rhs_grid
from bssn_state import BSSNState

def rk4_step(state, alpha, beta, dx, dt):
    """Один шаг интеграции RK4."""
    
    def get_rhs(s):
        return compute_bssn_rhs_grid(s, alpha, beta, dx)

    # RK4
    k1 = get_rhs(state)
    
    state_k2 = jax.tree_util.tree_map(lambda s, k: s + 0.5 * dt * k, state, k1)
    k2 = get_rhs(state_k2)
    
    state_k3 = jax.tree_util.tree_map(lambda s, k: s + 0.5 * dt * k, state, k2)
    k3 = get_rhs(state_k3)
    
    state_k4 = jax.tree_util.tree_map(lambda s, k: s + dt * k, state, k3)
    k4 = get_rhs(state_k4)
    
    # Итоговое обновление: s + (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)
    def final_update(s, c1, c2, c3, c4):
        return s + (dt/6.0) * (c1 + 2*c2 + 2*c3 + c4)
    
    new_state = jax.tree_util.tree_map(final_update, state, k1, k2, k3, k4)
    return new_state

def run_stress_test():
    print("Starting BSSN Stress Test (1000 steps)...")
    N = 16
    dx = 0.5
    dt = 0.001 
    
    state, alpha, beta = get_gw_initial_data(N, dx)
    
    for i in range(1000):
        state = rk4_step(state, alpha, beta, dx, dt)
        
        # Мониторинг стабильности
        if jnp.isnan(state.phi).any() or jnp.isinf(state.phi).any():
            print(f"FAILED at step {i}: NaN/Inf detected!")
            return
            
        if i % 100 == 0:
            print(f"Step {i}: Max Phi={jnp.max(jnp.abs(state.phi)):.4e}, Max A_tilde={jnp.max(jnp.abs(state.A_tilde)):.4e}")

    print("STRESS TEST PASSED: System is stable.")

if __name__ == "__main__":
    run_stress_test()
