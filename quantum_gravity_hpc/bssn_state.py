from typing import NamedTuple
import jax.numpy as jnp

class BSSNState(NamedTuple):
    phi: jnp.ndarray
    gamma_tilde: jnp.ndarray
    K: jnp.ndarray
    A_tilde: jnp.ndarray
    Gamma_tilde: jnp.ndarray  # Эволюционирует
    beta: jnp.ndarray         # Сдвиг (динамический)
