import jax
import jax.numpy as jnp
from adm_solver import ADMSolver, hamiltonian_constraint

def test_evolution_constraints():
    print("Test: ADM constraint preservation during evolution...")
    
    # 1. Начальные данные (слегка возмущенное плоское пространство)
    # Гарантированно удовлетворяют H = 0
    gamma_fn = lambda x: jnp.eye(3) * (1.0 + 0.01 * jnp.sum(x**2))
    K_fn = lambda x: jnp.zeros((3, 3))
    alpha_fn = lambda x: 1.0 + 0.01 * jnp.sum(x**2)
    
    # 2. Инициализация солвера
    solver = ADMSolver(gamma_fn, K_fn, alpha_fn)
    
    # 3. Эволюция
    x = jnp.array([0.1, 0.1, 0.1])
    dt = 0.01
    steps = 100 # Увеличили до 100 шагов
    
    gamma = gamma_fn(x)
    K = K_fn(x)
    alpha = alpha_fn(x) # Добавили alpha
    
    for i in range(steps):
        # Эволюция на шаг методом RK4
        gamma, K = solver.step_tensor(gamma, K, alpha, x, dt)
        
        # 4. Проверка связи на каждом шаге
        current_gamma_fn = lambda x: gamma
        current_K_fn = lambda x: K
        
        H = hamiltonian_constraint(current_gamma_fn, current_K_fn, x)
        print(f"Step {i+1}: Constraint H = {H:.6e}")
        
        # Связь должна оставаться близкой к 0
        assert jnp.allclose(H, 0.0, atol=1e-3), f"Constraint violated at step {i+1}!"

    print("Status: PASSED - Constraints preserved during evolution.")

if __name__ == "__main__":
    test_evolution_constraints()
