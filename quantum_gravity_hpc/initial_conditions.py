import jax.numpy as jnp
from bssn_state import BSSNState

def get_gw_initial_data(N, dx, amplitude=1e-4, sigma=1.0):
    """
    Генерирует начальные данные: пакет гравитационных волн в центре сетки.
    """
    coords = jnp.linspace(-N*dx/2, N*dx/2, N)
    X, Y, Z = jnp.meshgrid(coords, coords, coords, indexing='ij')
    R2 = X**2 + Y**2 + Z**2
    
    phi = jnp.zeros((N, N, N))
    gamma_tilde = jnp.tile(jnp.eye(3)[..., None, None, None], (1, 1, N, N, N))
    K = jnp.zeros((N, N, N))
    Gamma_tilde = jnp.zeros((3, N, N, N))
    
    gaussian = amplitude * jnp.exp(-R2 / (2 * sigma**2))
    
    A_tilde = jnp.zeros((3, 3, N, N, N))
    A_tilde = A_tilde.at[0, 0].set(gaussian)
    A_tilde = A_tilde.at[1, 1].set(-gaussian)
    
    alpha = jnp.ones((N, N, N))
    beta = jnp.zeros((3, N, N, N))
    
    state = BSSNState(
        phi=phi,
        gamma_tilde=gamma_tilde,
        K=K,
        A_tilde=A_tilde,
        Gamma_tilde=Gamma_tilde,
        beta=beta
    )
    return state, alpha, beta
