import jax
from initial_conditions import get_gw_initial_data
from bssn_rhs import compute_bssn_rhs_grid
from bssn_state import BSSNState

def rk4_step(state, alpha, beta, dx, dt):
    """Один шаг интеграции RK4."""
    
    def get_rhs(s):
        return compute_bssn_rhs_grid(s, alpha, beta, dx)

    # RK4
    k1 = get_rhs(state)
    
    def step_node(s, k): return jax.tree_util.tree_map(lambda x, y: x + 0.5 * dt * y, s, k)
    
    state_k2 = step_node(state, k1)
    k2 = get_rhs(state_k2)
    
    state_k3 = step_node(state, k2)
    k3 = get_rhs(state_k3)
    
    def step_node_full(s, k): return jax.tree_util.tree_map(lambda x, y: x + dt * y, s, k)
    state_k4 = step_node_full(state, k3)
    k4 = get_rhs(state_k4)
    
    # Итоговое обновление: s + (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)
    def final_update(s, c1, c2, c3, c4):
        return s + (dt/6.0) * (c1 + 2*c2 + 2*c3 + c4)
    
    new_state = jax.tree_util.tree_map(final_update, state, k1, k2, k3, k4)
    return new_state

# --- ПАРАМЕТРЫ ---
N = 16 
dx = 0.5
dt = 0.01
steps = 20

state, alpha, beta = get_gw_initial_data(N, dx)

# Запуск цикла
for i in range(steps):
    state = rk4_step(state, alpha, beta, dx, dt)
    if i % 5 == 0:
        print(f"Шаг {i}: A_tilde max = {jax.numpy.max(state.A_tilde):.4e}")

print("Simulation complete.")
