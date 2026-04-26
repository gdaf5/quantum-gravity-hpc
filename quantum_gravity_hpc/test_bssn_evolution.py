import jax
import jax.numpy as jnp
from bssn_solver import BSSNSolver

def test_full_evolution():
    print("Testing BSSN evolution step (physics-aware)...")
    
    # Инициализация переменных (в окрестности плоского пространства)
    phi = jnp.array(0.0)
    gamma_tilde = jnp.eye(3)
    K = jnp.array(0.0)
    A_tilde = jnp.array([[0.1, 0.0, 0.0], [0.0, -0.1, 0.0], [0.0, 0.0, 0.0]])
    Gamma_tilde = jnp.zeros(3)
    alpha = jnp.array(1.0)
    beta = jnp.zeros(3)
    
    # Инициализация солвера
    solver = BSSNSolver(phi, gamma_tilde, K, A_tilde, Gamma_tilde, alpha, beta)
    
    # Эволюция на шаг
    dt = 0.01
    new_vars = solver.evolve(dt)
    
    # Проверка, что эволюция изменила переменные физически корректно
    # ∂_t γ_ij = -2 α A_ij => Δγ = -2 * 1.0 * A_ij * dt = -0.2 * A_tilde
    expected_dgamma = -2.0 * alpha * A_tilde * dt
    
    is_gamma_correct = jnp.allclose(new_vars[1] - gamma_tilde, expected_dgamma, atol=1e-5)
    print(f"Gamma evolution test: {'PASSED' if is_gamma_correct else 'FAILED'}")
    
    assert is_gamma_correct, "Gamma evolution inconsistent!"
    print("Test: PASSED - BSSN evolution framework operational.")

if __name__ == "__main__":
    test_full_evolution()
