import jax.numpy as jnp
from stencils import laplacian_stencil, gradient_stencil, hessian_stencil, apply_dissipation
from bssn_state import BSSNState
from geometry import compute_ricci_3d_grid, get_christoffel_3d

def apply_boundary_conditions(field, dx):
    """
    Sponge Layer с мягким затуханием (exp(-5.0)).
    """
    N = field.shape[-1]
    z = jnp.linspace(-1, 1, N)
    X, Y, Z = jnp.meshgrid(z, z, z, indexing='ij')
    r = jnp.sqrt(X**2 + Y**2 + Z**2)
    # Коэффициент -5.0 делает переход плавным
    mask = jnp.where(r > 0.8, jnp.exp(-5.0 * (r - 0.8)**2), 1.0)
    return field * mask

def compute_bssn_rhs_grid(state: BSSNState, alpha, beta, dx):
    gamma_inv = jnp.linalg.inv(state.gamma_tilde.transpose(2, 3, 4, 0, 1)).transpose(3, 4, 0, 1, 2)
    dgamma = jnp.stack([jnp.stack([gradient_stencil(state.gamma_tilde[i, j], dx) for j in range(3)]) for i in range(3)])
    ddgamma = jnp.stack([jnp.stack([hessian_stencil(state.gamma_tilde[i, j], dx) for j in range(3)]) for i in range(3)])
    R_tilde_ij = compute_ricci_3d_grid(state.gamma_tilde, dgamma, ddgamma, dx)
    
    alpha_floor = 0.05
    dalpha = -2.0 * alpha * state.K * jnp.where(alpha < alpha_floor, (alpha/alpha_floor)**2, 1.0)
    
    dphi = -1.0/6.0 * alpha * state.K
    dgamma_tilde = -2.0 * alpha * state.A_tilde
    
    lap_alpha = laplacian_stencil(alpha, dx)
    A_sq = jnp.einsum('ij..., im..., jn..., mn... -> ...', state.A_tilde, gamma_inv, gamma_inv, state.A_tilde)
    dK = -lap_alpha + alpha * (A_sq + 1.0/3.0 * state.K**2)
    
    def trace_free(tensor, gamma, g_inv):
        trace = jnp.einsum('ij..., ij... -> ...', g_inv, tensor)
        return tensor - 1.0/3.0 * gamma * trace
    
    term_alpha = alpha * R_tilde_ij - hessian_stencil(alpha, dx)
    dA_tilde = jnp.exp(-4*state.phi) * trace_free(term_alpha, state.gamma_tilde, gamma_inv) + \
               alpha * (state.K * state.A_tilde - 2.0 * jnp.einsum('il..., lm..., mj... -> ij...', state.A_tilde, gamma_inv, state.A_tilde))
    
    Gamma_ijk = get_christoffel_3d(state.gamma_tilde, dgamma)
    grad_alpha = gradient_stencil(alpha, dx)
    eta = 2.0  # Коэффициент демпфирования
    dGamma_tilde = -2.0 * jnp.einsum('ij..., j... -> i...', state.A_tilde, grad_alpha) + \
                   2.0 * alpha * jnp.einsum('ijk..., jk... -> i...', Gamma_ijk, state.A_tilde) - \
                   eta * state.Gamma_tilde  # Демпфирующий член
    
    eps = 0.01
    dphi = apply_boundary_conditions(dphi + apply_dissipation(state.phi, dx, eps), dx)
    dK = apply_boundary_conditions(dK + apply_dissipation(state.K, dx, eps), dx)
    
    # Векторизованная диссипация (убираем циклы для скорости JIT)
    new_dgamma = dgamma_tilde + apply_dissipation(state.gamma_tilde, dx, eps)
    new_dA = dA_tilde + apply_dissipation(state.A_tilde, dx, eps)
            
    dGamma_tilde = apply_boundary_conditions(dGamma_tilde, dx)
            
    return BSSNState(dphi, new_dgamma, dK, new_dA, dGamma_tilde, jnp.zeros_like(beta)), dalpha, jnp.zeros_like(beta)

def enforce_constraints(state: BSSNState):
    gamma_mat = state.gamma_tilde.transpose(2, 3, 4, 0, 1)
    det = jnp.linalg.det(gamma_mat)
    scale = (det**(-1.0/3.0))[None, None, ...]
    new_gamma_tilde = state.gamma_tilde * scale
    
    gamma_inv = jnp.linalg.inv(new_gamma_tilde.transpose(2, 3, 4, 0, 1)).transpose(3, 4, 0, 1, 2)
    trace_A = jnp.einsum('ij..., ij... -> ...', gamma_inv, state.A_tilde)
    new_A_tilde = state.A_tilde - (1.0/3.0) * new_gamma_tilde * trace_A[None, None, ...]
    
    return state._replace(gamma_tilde=new_gamma_tilde, A_tilde=new_A_tilde)
