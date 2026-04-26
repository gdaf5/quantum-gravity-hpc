import jax
import jax.numpy as jnp
from jax import jacfwd, jacrev, grad

def get_christoffel_3d(gamma_fn, x):
    gamma = gamma_fn(x)
    gamma_inv = jnp.linalg.inv(gamma)
    dgamma = jacfwd(gamma_fn)(x)
    
    term1 = jnp.einsum('kl, ilj -> kij', gamma_inv, dgamma)
    term2 = jnp.einsum('kl, jli -> kij', gamma_inv, dgamma)
    term3 = jnp.einsum('kl, lij -> kij', gamma_inv, dgamma)
    
    return 0.5 * (term1 + term2 - term3)

def get_ricci_3d(gamma_fn, x):
    Gamma_fn = lambda x: get_christoffel_3d(gamma_fn, x)
    dGamma = jacfwd(Gamma_fn)(x)
    Gamma = Gamma_fn(x)
    
    R_ij = jnp.einsum('k kij -> ij', dGamma) - jnp.einsum('j ikk -> ij', dGamma) + \
           jnp.einsum('kkl, lij -> ij', Gamma, Gamma) - jnp.einsum('kjl, lik -> ij', Gamma, Gamma)
    
    return R_ij

def hamiltonian_constraint(gamma_fn, K_fn, x):
    gamma = gamma_fn(x)
    gamma_inv = jnp.linalg.inv(gamma)
    K = K_fn(x)
    
    R_ij = get_ricci_3d(gamma_fn, x)
    R = jnp.einsum('ij, ij ->', gamma_inv, R_ij)
    K_trace = jnp.einsum('ij, ij ->', gamma_inv, K)
    K_sq = jnp.einsum('ij, im, jn, mn ->', K, gamma_inv, gamma_inv, K)
    
    return R + K_trace**2 - K_sq

from jax import jacfwd, hessian

class ADMSolver:
    def __init__(self, gamma_fn, K_fn, alpha_fn, beta_fn=None):
        self.gamma_fn = gamma_fn
        self.K_fn = K_fn
        self.alpha_fn = alpha_fn
        
    def compute_derivatives(self, gamma, K, alpha, x):
        """Вычисляет ∂_t γ и ∂_t K для текущего состояния."""
        gamma_inv = jnp.linalg.inv(gamma)
        
        # Тензор Риччи 3-метрики (на основе текущей gamma)
        # Мы переопределяем функцию метрики на текущее значение
        R_ij = get_ricci_3d(lambda x: gamma, x)
        
        # Эволюционные уравнения
        dgamma_dt = -2.0 * alpha * K
        
        K_trace = jnp.einsum('ij, ij ->', gamma_inv, K)
        K_il_Klj = jnp.einsum('il, lm, mj -> ij', K, gamma_inv, K)
        
        # ∇_i ∇_j α (Гессиан)
        nabla_nabla_alpha = hessian(self.alpha_fn)(x)
        
        dK_dt = -nabla_nabla_alpha + alpha * (R_ij + K_trace * K - 2.0 * K_il_Klj)
        
        return dgamma_dt, dK_dt

    def step_tensor(self, gamma, K, alpha, x, dt):
        """Эволюция на шаг dt методом RK4."""
        k1_gamma, k1_K = self.compute_derivatives(gamma, K, alpha, x)
        
        k2_gamma, k2_K = self.compute_derivatives(gamma + 0.5*dt*k1_gamma, K + 0.5*dt*k1_K, alpha, x)
        k3_gamma, k3_K = self.compute_derivatives(gamma + 0.5*dt*k2_gamma, K + 0.5*dt*k2_K, alpha, x)
        k4_gamma, k4_K = self.compute_derivatives(gamma + dt*k3_gamma, K + dt*k3_K, alpha, x)
        
        gamma_new = gamma + (dt/6.0) * (k1_gamma + 2*k2_gamma + 2*k3_gamma + k4_gamma)
        K_new = K + (dt/6.0) * (k1_K + 2*k2_K + 2*k3_K + k4_K)
        
        return gamma_new, K_new

