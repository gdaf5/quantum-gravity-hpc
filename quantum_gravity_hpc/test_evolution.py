import jax.numpy as jnp
from adm_solver import ADMSolver

def test_evolution():
    print("Test: ADM evolution (gamma changes due to K)...")
    
    # 1. Начальное состояние: Плоская 3-метрика (γ_ij = δ_ij)
    gamma = jnp.eye(3)
    
    # 2. Начальное возмущение кривизны (K_ij)
    # Положим K_{xx} = 0.1, K_{yy} = -0.1 (бесследовое возмущение)
    K = jnp.array([[0.1, 0.0, 0.0],
                   [0.0, -0.1, 0.0],
                   [0.0, 0.0, 0.0]])
    
    alpha = 1.0 # Lapse (простейший случай)
    dt = 0.1
    
    # Эволюция
    solver = ADMSolver(None, None) 
    new_gamma, new_K = solver.step_tensor(gamma, K, alpha, dt)
    
    print(f"Initial Gamma:\n{gamma}")
    print(f"Evolved Gamma:\n{new_gamma}")
    
    # Проверка: Эволюция γ_ij = -2 α K_ij dt
    # Δγ = -2 * 1.0 * K * 0.1 = -0.2 * K
    expected_change = -0.2 * K
    
    is_correct = jnp.allclose(new_gamma - gamma, expected_change, atol=1e-6)
    print(f"Test Passed: {is_correct}")
    
    assert is_correct, "ADM evolution logic incorrect!"

if __name__ == "__main__":
    test_evolution()
