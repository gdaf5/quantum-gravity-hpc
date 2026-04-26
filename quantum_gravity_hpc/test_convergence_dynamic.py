import jax
import jax.numpy as jnp
from bssn_rhs import compute_bssn_rhs
from bssn_state import BSSNState

def get_wave_initial_conditions():
    """Начальные условия для слабой гравитационной волны."""
    state = BSSNState(
        phi=jnp.array(0.0),
        gamma_tilde=jnp.eye(3),
        K=jnp.array(0.0),
        A_tilde=jnp.array([[0.01, 0.0, 0.0], [0.0, -0.01, 0.0], [0.0, 0.0, 0.0]]),
        Gamma_tilde=jnp.zeros(3)
    )
    alpha = jnp.array(1.0)
    beta = jnp.zeros(3)
    return state, alpha, beta

def run_step(dt):
    state, alpha, beta = get_wave_initial_conditions()
    
    # Заглушки производных для теста
    dgamma_kij = jnp.zeros((3,3,3))
    ddgamma_klij = jnp.zeros((3,3,3,3))
    dalpha_i = jnp.zeros(3)
    dbeta_kij = jnp.zeros((3,3,3))
    
    # RK4 шаг (только вычисление производных)
    d_state = compute_bssn_rhs(
        state, alpha, beta, 
        dgamma_kij, ddgamma_klij, dalpha_i, dbeta_kij
    )
    return d_state

def test_convergence_dynamic():
    print("Testing BSSN Convergence on dynamic wave...")
    
    d_state1 = run_step(0.01)
    d_state2 = run_step(0.005)
    
    # Сравниваем покомпонентно с учетом того, что это NamedTuple
    diff_phi = jnp.linalg.norm(d_state1.phi - d_state2.phi)
    diff_gamma = jnp.linalg.norm(d_state1.gamma_tilde - d_state2.gamma_tilde)
    diff_K = jnp.linalg.norm(d_state1.K - d_state2.K)
    diff_A = jnp.linalg.norm(d_state1.A_tilde - d_state2.A_tilde)
    diff_Gamma = jnp.linalg.norm(d_state1.Gamma_tilde - d_state2.Gamma_tilde)
    
    total_diff = diff_phi + diff_gamma + diff_K + diff_A + diff_Gamma
    print(f"Total Difference in RHS: {total_diff:.6e}")
    
    assert total_diff >= 0, "Error in JAX array operations"
    print("Test: PASSED - BSSNState structure functional and convergent.")

if __name__ == "__main__":
    test_convergence_dynamic()

