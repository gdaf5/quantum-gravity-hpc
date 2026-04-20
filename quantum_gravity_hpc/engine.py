import torch
from torch.func import jacrev, vmap
import torch.nn.functional as F

# 1. Функция метрики, теперь ТОЛЬКО вычисляет тензор из переданного g_local
def get_metric_from_local(g_local):
    """
    g_local: [4, 4] - тензор метрики, уже интерполированный для данной точки
    """
    return g_local

# 2. Математика тензорных операций
def get_christoffel_precomputed(coords, g_func):
    # g_func - функция, возвращающая метрику в точке coords
    g = g_func(coords)
    g_inv = torch.inverse(g)
    
    # Производная метрики по координатам
    dg = jacrev(g_func)(coords)
    
    # Γ^σ_{μν} = ½ g^{σρ} (∂_μ g_{ρν} + ∂_ν g_{ρμ} - ∂_ρ g_{μν})
    gamma = 0.5 * torch.einsum('sr, mnr -> smn', g_inv, dg.permute(0, 2, 1) + dg.permute(1, 2, 0) - dg)
    
    return 0.5 * (gamma + gamma.transpose(1, 2))

# 3. Интегратор
def compute_single_step(p, g_local):
    coords = p[:4]
    vel = p[4:]
    
    # Локальная метрика (константа для шага)
    g_func = lambda c: g_local
    
    gamma = get_christoffel_precomputed(coords, g_func)
    accel = -torch.einsum('smn, m, n -> s', gamma, vel, vel)
    
    dt = 1e-45
    new_pos = coords + vel * dt + 0.5 * accel * dt**2
    
    # Второе приближение ускорения (gamma_new = gamma, так как g константа для шага)
    new_vel = vel + accel * dt
    
    return torch.cat([new_pos, new_vel])

# 4. Векторизация
def batch_geodesic(particles, g_locals):
    # Передаем g_locals (метрикa для каждой частицы) в compute_single_step
    return vmap(compute_single_step, in_dims=(0, 0))(particles, g_locals)
