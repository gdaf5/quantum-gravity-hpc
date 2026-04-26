import jax
import jax.numpy as jnp
from bssn_solver import BSSNSolver

def test_framework():
    print("Testing BSSN framework compatibility with JAX...")
    
    # 1. Dummy data (инициализация тензорных переменных BSSN)
    phi = jnp.array(0.0, dtype=jnp.float64)
    gamma_tilde = jnp.eye(3, dtype=jnp.float64)
    K = jnp.array(0.0, dtype=jnp.float64)
    A_tilde = jnp.zeros((3, 3), dtype=jnp.float64)
    Gamma_tilde = jnp.zeros(3, dtype=jnp.float64)
    alpha = jnp.array(1.0, dtype=jnp.float64)
    beta = jnp.zeros(3, dtype=jnp.float64)
    
    # 2. Инициализация солвера
    solver = BSSNSolver(phi, gamma_tilde, K, A_tilde, Gamma_tilde, alpha, beta)
    
    # 3. Тест JIT-компиляции и эволюции
    try:
        # Пытаемся скомпилировать метод evolve
        evolve_jit = jax.jit(solver.evolve)
        
        # Запуск эволюции
        result = evolve_jit(0.1)
        
        print("JIT and Evolve: PASSED")
        # Проверка типов возвращаемых значений
        print(f"Result types: {[type(r) for r in result]}")
        
    except Exception as e:
        print(f"JIT/Evolve FAILED: {e}")
        return

    # 4. Тест проверки ограничений
    print(f"Constraint check: {solver.check_constraints()}")

if __name__ == "__main__":
    test_framework()
