import jax
import jax.numpy as jnp
from adm_solver import hamiltonian_constraint

def test_flat_space_constraints():
    """Проверка: Гамильтонова связь на плоском пространстве должна быть 0."""
    
    # Плоская 3-метрика (δ_ij)
    gamma_fn = lambda x: jnp.eye(3)
    # Плоская кривизна (0)
    K_fn = lambda x: jnp.zeros((3, 3))
    
    x = jnp.array([0.0, 0.0, 0.0])
    
    constraint_value = hamiltonian_constraint(gamma_fn, K_fn, x)
    
    print(f"Test: Hamiltonian constraint on flat space...")
    print(f"Constraint value: {constraint_value}")
    
    # Проверка на соответствие нулю (с учетом машинного эпсилона)
    assert jnp.allclose(constraint_value, 0.0, atol=1e-6), "Hamiltonian constraint failed on flat space!"
    print("Status: PASSED")

if __name__ == "__main__":
    test_flat_space_constraints()
