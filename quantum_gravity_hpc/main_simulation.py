import jax
import jax.lax
import jax.numpy as jnp
import time
from bssn_state import BSSNState
from bssn_rhs import compute_bssn_rhs_grid, enforce_constraints
from initial_conditions import get_gw_initial_data
from geometry import compute_hamiltonian_constraint

@jax.jit
def perform_step(state, alpha, beta, dx, dt):
    """Один полный шаг RK4."""
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

@jax.jit
def run_simulation(state, alpha, beta, dx, dt, num_steps):
    def body_fun(i, val):
        s, a, b = val
        return perform_step(s, a, b, dx, dt)
    return jax.lax.fori_loop(0, num_steps, body_fun, (state, alpha, beta))

# --- ПУСК ---
N, dx, dt = 64, 0.05, 0.00005
total_steps = 1000
report_interval = 50  # Выводим отчет каждые 50 шагов
state, alpha, beta = get_gw_initial_data(N, dx, amplitude=1e-6)

print(f"Старт: N={N}, dt={dt}. Остановка при NaN.")
start_time = time.time()

# "Прогрев" компилятора
_, _, _ = run_simulation(state, alpha, beta, dx, dt, 1)

for i in range(0, total_steps, report_interval):
    # Считаем блок из 50 шагов прямо в GPU
    state, alpha, beta = run_simulation(state, alpha, beta, dx, dt, report_interval)
    
    # Синхронизация и проверка на взрыв
    state.phi.block_until_ready()
    
    if jnp.isnan(state.phi).any():
        print(f"\n!!! РАСЧЕТ ПРЕРВАН на шаге {i + report_interval} из-за NaN !!!")
        break
        
    h_err = compute_hamiltonian_constraint(state, dx)
    elapsed = time.time() - start_time
    print(f"Шаг {i + report_interval:4d} | H-err: {h_err:.4e} | Время: {elapsed:.2f} сек")

print(f"\nИтоговое время работы: {time.time() - start_time:.2f} сек")
