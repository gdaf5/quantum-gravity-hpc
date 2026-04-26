import jax.numpy as jnp
from stencils import gradient_stencil, hessian_stencil

def get_christoffel_3d(gamma_tilde, dgamma_kij):
    gamma_inv = jnp.linalg.inv(gamma_tilde.transpose(2, 3, 4, 0, 1)).transpose(3, 4, 0, 1, 2)
    term = dgamma_kij.transpose(1, 0, 2, 3, 4, 5) + dgamma_kij.transpose(2, 0, 1, 3, 4, 5) - dgamma_kij
    return 0.5 * jnp.einsum('kl..., lij... -> kij...', gamma_inv, term)

def compute_ricci_3d_grid(gamma_tilde, dgamma, ddgamma, dx):
    gamma_inv = jnp.linalg.inv(gamma_tilde.transpose(2, 3, 4, 0, 1)).transpose(3, 4, 0, 1, 2)
    Gamma = get_christoffel_3d(gamma_tilde, dgamma)
    dGamma = 0.5 * jnp.einsum('lm..., kijm... -> klij...', gamma_inv, ddgamma)
    R_ij = jnp.einsum('k kij... -> ij...', dGamma) - jnp.einsum('j ikk... -> ij...', dGamma) + \
           jnp.einsum('kkl..., lij... -> ij...', Gamma, Gamma) - jnp.einsum('kjl..., lik... -> ij...', Gamma, Gamma)
    return R_ij

def compute_hamiltonian_constraint(state, dx):
    gamma_inv = jnp.linalg.inv(state.gamma_tilde.transpose(2, 3, 4, 0, 1)).transpose(3, 4, 0, 1, 2)
    dgamma = jnp.stack([jnp.stack([gradient_stencil(state.gamma_tilde[i, j], dx) for j in range(3)]) for i in range(3)])
    ddgamma = jnp.stack([jnp.stack([hessian_stencil(state.gamma_tilde[i, j], dx) for j in range(3)]) for i in range(3)])
    R_ij = compute_ricci_3d_grid(state.gamma_tilde, dgamma, ddgamma, dx)
    R_tilde = jnp.einsum('ij..., ij... -> ...', gamma_inv, R_ij)
    A_sq = jnp.einsum('ij..., im..., jn..., mn... -> ...', state.A_tilde, gamma_inv, gamma_inv, state.A_tilde)
    H = R_tilde - A_sq + (2.0/3.0) * state.K**2
    return jnp.sqrt(jnp.mean(H**2))
