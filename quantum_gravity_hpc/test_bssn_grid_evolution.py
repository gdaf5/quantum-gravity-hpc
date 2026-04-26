import jax
import jax.numpy as jnp
from bssn_rhs import compute_bssn_rhs_grid
from bssn_state import BSSNState

def test_grid_evolution():
    print("Testing BSSN evolution on a 3D grid...")
    N = 8 # Размер сетки
    
    # 1. Инициализация BSSNState с 3D массивами
    state = BSSNState(
        phi=jnp.zeros((N, N, N)),
        gamma_tilde=jnp.tile(jnp.eye(3)[..., None, None, None], (1, 1, N, N, N)),
        K=jnp.zeros((N, N, N)),
        A_tilde=jnp.zeros((3, 3, N, N, N)),
        Gamma_tilde=jnp.zeros((3, N, N, N))
    )
    alpha = jnp.ones((N, N, N))
    beta = jnp.zeros((3, N, N, N))
    
    # Заглушки производных для теста
    dgamma_kij = jnp.zeros((3, 3, 3, N, N, N))
    ddgamma_klij = jnp.zeros((3, 3, 3, 3, N, N, N))
    dalpha_i = jnp.zeros((3, N, N, N))
    dbeta_kij = jnp.zeros((3, 3, 3, N, N, N))
    
    # 2. Вычисление правых частей (RHS)
    dx = 0.1
    d_state = compute_bssn_rhs_grid(
        state, alpha, beta, dx
    )
    
    print(f"RHS shapes: phi={d_state.phi.shape}, gamma={d_state.gamma_tilde.shape}")
    
    assert d_state.gamma_tilde.shape == (3, 3, N, N, N), "Incorrect gamma_tilde shape!"
    print("Test: PASSED - BSSNState structure functional on 3D grid.")

if __name__ == "__main__":
    test_grid_evolution()
