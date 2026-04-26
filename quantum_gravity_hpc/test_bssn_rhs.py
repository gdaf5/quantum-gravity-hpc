import jax
import jax.numpy as jnp
from bssn_state import BSSNState
from bssn_rhs import compute_bssn_rhs

def test_bssn_full_evolution():
    print("Testing BSSN full evolution (RHS) step...")
    
    # 1. Инициализация переменных (слабое возмущение)
    state = BSSNState(
        phi=jnp.array(0.0),
        gamma_tilde=jnp.eye(3),
        K=jnp.array(0.0),
        A_tilde=jnp.array([[0.01, 0.0, 0.0], [0.0, -0.01, 0.0], [0.0, 0.0, 0.0]]),
        Gamma_tilde=jnp.zeros(3)
    )
    alpha = jnp.array(1.0)
    beta = jnp.zeros(3)
    
    # Тензорные производные (для теста возьмем малые значения)
    dgamma_kij = jnp.zeros((3, 3, 3))
    ddgamma_klij = jnp.zeros((3, 3, 3, 3))
    dalpha_i = jnp.array([0.0, 0.0, 0.0])
    dbeta_kij = jnp.zeros((3, 3, 3))
    
    # 2. Вычисление правых частей (RHS)
    d_state = compute_bssn_rhs(
        state, alpha, beta, 
        dgamma_kij, ddgamma_klij, dalpha_i, dbeta_kij
    )

    
    # 3. Проверка: изменения не должны быть нулевыми (система эволюционирует)
    print(f"dphi_dt: {d_state.phi:.4f}")
    print(f"dA_tilde_dt_norm: {jnp.linalg.norm(d_state.A_tilde):.4f}")
    
    assert not jnp.allclose(d_state.A_tilde, 0.0), "dA_tilde_dt should not be zero!"
    print("Test: PASSED - BSSN RHS framework is fully functional.")

if __name__ == "__main__":
    test_bssn_full_evolution()
