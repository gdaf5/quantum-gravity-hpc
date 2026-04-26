import jax.numpy as jnp

def laplacian_stencil(field, dx):
    """Лапласиан ∇² (2-й порядок)."""
    f = jnp.pad(field, 1, mode='wrap')
    lap = (f[:-2, 1:-1, 1:-1] + f[2:, 1:-1, 1:-1] +
           f[1:-1, :-2, 1:-1] + f[1:-1, 2:, 1:-1] +
           f[1:-1, 1:-1, :-2] + f[1:-1, 1:-1, 2:] - 6*field) / (dx**2)
    return lap

def gradient_stencil(field, dx):
    """Градиент ∇_i."""
    f = jnp.pad(field, 1, mode='wrap')
    df_dx = (f[2:, 1:-1, 1:-1] - f[:-2, 1:-1, 1:-1]) / (2*dx)
    df_dy = (f[1:-1, 2:, 1:-1] - f[1:-1, :-2, 1:-1]) / (2*dx)
    df_dz = (f[1:-1, 1:-1, 2:] - f[1:-1, 1:-1, :-2]) / (2*dx)
    return jnp.stack([df_dx, df_dy, df_dz], axis=0)

def hessian_stencil(field, dx):
    """Гессиан ∇_i ∇_j."""
    # Используем градиент градиента с паддингом внутри
    grad = gradient_stencil(field, dx)
    hess = jnp.stack([gradient_stencil(grad[0], dx),
                      gradient_stencil(grad[1], dx),
                      gradient_stencil(grad[2], dx)], axis=0)
    return hess

def apply_dissipation(field, dx, epsilon=0.05):
    """Диссипация 4-го порядка. Работает для полей любого ранга (скаляры, тензоры)."""
    # Вычисляем паддинг: (0,0) для тензорных индексов, (2,2) для 3 пространственных
    ndim = field.ndim
    pad_width = [(0, 0)] * (ndim - 3) + [(2, 2)] * 3
    f = jnp.pad(field, pad_width, mode='wrap')
    
    # Считаем производные по 3 последним осям (пространственным)
    # Используем срез для размерности [..., N, N, N]
    d4_x = (f[..., 4:, 2:-2, 2:-2] - 4*f[..., 3:-1, 2:-2, 2:-2] + 6*f[..., 2:-2, 2:-2, 2:-2] - 4*f[..., 1:-3, 2:-2, 2:-2] + f[..., :-4, 2:-2, 2:-2])
    d4_y = (f[..., 2:-2, 4:, 2:-2] - 4*f[..., 2:-2, 3:-1, 2:-2] + 6*f[..., 2:-2, 2:-2, 2:-2] - 4*f[..., 2:-2, 1:-3, 2:-2] + f[..., 2:-2, :-4, 2:-2])
    d4_z = (f[..., 2:-2, 2:-2, 4:] - 4*f[..., 2:-2, 2:-2, 3:-1] + 6*f[..., 2:-2, 2:-2, 2:-2] - 4*f[..., 2:-2, 2:-2, 1:-3] + f[..., 2:-2, 2:-2, :-4])
    
    return - (epsilon / (16 * dx**4)) * (d4_x + d4_y + d4_z)
