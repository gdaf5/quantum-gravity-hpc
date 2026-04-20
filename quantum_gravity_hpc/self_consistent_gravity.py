"""
Модуль 1: Полноценный Back-Reaction с самосогласованной эволюцией.
Реализует итерационный цикл: частицы → T_μν → решение уравнений Эйнштейна → обновление метрики.
"""

import torch
import numpy as np
from typing import Tuple, Optional
import h5py
from datetime import datetime

class SelfConsistentGravity:
    """
    Самосогласованная гравитационная динамика.
    Реализует полный цикл обратного влияния материи на метрику.
    """
    
    def __init__(self, grid_shape=(8, 8, 8, 8), 
                 G_newton=6.67430e-11,
                 c=3e8,
                 hbar=1.054571817e-34,
                 device='cpu',
                 dtype=torch.float64):
        
        self.grid_shape = grid_shape
        self.G = G_newton
        self.c = c
        self.hbar = hbar
        self.device = device
        self.dtype = dtype
        
        # Планковские единицы
        self.l_P = np.sqrt(hbar * G_newton / c**3)  # 1.616e-35 м
        self.t_P = self.l_P / c  # 5.39e-44 с
        self.m_P = np.sqrt(hbar * c / G_newton)  # 2.176e-8 кг
        
        # Инициализация метрики (Минковский + малые флуктуации)
        self.g_metric = self._initialize_metric()
        
        # Сопряженный импульс (для гамильтоновой формулировки)
        self.pi_metric = torch.zeros_like(self.g_metric)
        
        # История для анализа
        self.history = {
            'metric_trace': [],
            'energy_density': [],
            'curvature_scalar': [],
            'constraint_violation': [],
            'max_delta_g': []
        }
        
        print(f"Инициализация самосогласованной гравитации:")
        print(f"  Сетка: {grid_shape}")
        print(f"  Планковская длина: {self.l_P:.3e} м")
        print(f"  Планковское время: {self.t_P:.3e} с")
        print(f"  Планковская масса: {self.m_P:.3e} кг")
    
    def _initialize_metric(self):
        """Инициализация метрики Минковского с малыми флуктуациями"""
        g = torch.zeros((*self.grid_shape, 4, 4), dtype=self.dtype, device=self.device)
        
        # Метрика Минковского
        eta = torch.diag(torch.tensor([-1.0, 1.0, 1.0, 1.0], dtype=self.dtype))
        
        for i in range(self.grid_shape[0]):
            for j in range(self.grid_shape[1]):
                for k in range(self.grid_shape[2]):
                    for l in range(self.grid_shape[3]):
                        g[i, j, k, l] = eta
        
        # Малые начальные флуктуации (квантовые)
        fluctuation_amplitude = 0.01
        for mu in range(4):
            for nu in range(mu, 4):
                fluct = torch.randn(self.grid_shape, dtype=self.dtype, device=self.device)
                fluct = fluct * fluctuation_amplitude
                
                g[..., mu, nu] += fluct
                if mu != nu:
                    g[..., nu, mu] += fluct
        
        return g
    
    def compute_energy_momentum_tensor(self, particles: torch.Tensor) -> torch.Tensor:
        """
        Вычисление тензора энергии-импульса T^μν на сетке.
        Использует улучшенный PIC (Particle-In-Cell) с интерполяцией.
        
        Args:
            particles: [N, 8] - (t, x, y, z, u^0, u^1, u^2, u^3)
        
        Returns:
            T: [grid_shape, 4, 4] - тензор энергии-импульса
        """
        N = particles.shape[0]
        T = torch.zeros((*self.grid_shape, 4, 4), dtype=self.dtype, device=self.device)
        
        # Масса частицы в планковских единицах
        m_particle = 1.674927498e-27 / self.m_P  # масса нейтрона
        
        for p_idx in range(N):
            pos = particles[p_idx, 1:4]  # пространственные координаты
            vel = particles[p_idx, 4:8]  # 4-скорость
            
            # Нормализация координат к индексам сетки
            grid_pos = torch.zeros(3, dtype=self.dtype, device=self.device)
            for i in range(3):
                grid_pos[i] = pos[i] / self.l_P  # в единицах планковской длины
            
            # Индексы ближайших узлов (для интерполяции)
            i0 = int(torch.clamp(grid_pos[0], 0, self.grid_shape[1]-2))
            j0 = int(torch.clamp(grid_pos[1], 0, self.grid_shape[2]-2))
            k0 = int(torch.clamp(grid_pos[2], 0, self.grid_shape[3]-2))
            
            # Веса для трилинейной интерполяции
            dx = grid_pos[0] - i0
            dy = grid_pos[1] - j0
            dz = grid_pos[2] - k0
            
            # 8 соседних узлов
            weights = [
                (1-dx)*(1-dy)*(1-dz),
                dx*(1-dy)*(1-dz),
                (1-dx)*dy*(1-dz),
                dx*dy*(1-dz),
                (1-dx)*(1-dy)*dz,
                dx*(1-dy)*dz,
                (1-dx)*dy*dz,
                dx*dy*dz
            ]
            
            nodes = [
                (0, i0, j0, k0),
                (0, i0+1, j0, k0),
                (0, i0, j0+1, k0),
                (0, i0+1, j0+1, k0),
                (0, i0, j0, k0+1),
                (0, i0+1, j0, k0+1),
                (0, i0, j0+1, k0+1),
                (0, i0+1, j0+1, k0+1)
            ]
            
            # T^μν = ρ u^μ u^ν (для пылевидной материи)
            # ρ = m * n (плотность = масса × концентрация)
            for weight, node in zip(weights, nodes):
                for mu in range(4):
                    for nu in range(4):
                        T[node][mu, nu] += weight * m_particle * vel[mu] * vel[nu]
        
        # Нормировка на объем ячейки
        cell_volume = self.l_P**3
        T = T / (N * cell_volume)
        
        return T
    
    def solve_einstein_equations(self, T: torch.Tensor, 
                                 relaxation_param: float = 0.1) -> torch.Tensor:
        """
        Решение упрощенных уравнений Эйнштейна: G_μν = 8πG/c⁴ T_μν
        
        Используем релаксационный метод для стабильности:
        δg_μν^(n+1) = δg_μν^(n) + α * (8πG/c⁴ * T_μν - G_μν)
        
        Args:
            T: тензор энергии-импульса
            relaxation_param: параметр релаксации (0 < α < 1)
        
        Returns:
            delta_g: изменение метрики
        """
        # Константа связи в планковских единицах
        kappa = 8 * np.pi * self.G / self.c**4
        
        # Вычисляем тензор Эйнштейна G_μν = R_μν - ½g_μν R
        G_tensor = self.compute_einstein_tensor()
        
        # Правая часть уравнений Эйнштейна
        source = kappa * T
        
        # Релаксационное обновление
        delta_g = relaxation_param * (source - G_tensor)
        
        # Проверка ограничений (симметрия, детерминант)
        delta_g = self._enforce_constraints(delta_g)
        
        return delta_g
    
    def compute_einstein_tensor(self) -> torch.Tensor:
        """
        Вычисление тензора Эйнштейна G_μν = R_μν - ½g_μν R
        
        Использует конечно-разностную аппроксимацию для производных.
        """
        G = torch.zeros_like(self.g_metric)
        
        # Вычисляем тензор Риччи R_μν
        R_ricci = self.compute_ricci_tensor()
        
        # Скалярная кривизна R = g^μν R_μν
        R_scalar = self.compute_scalar_curvature(R_ricci)
        
        # G_μν = R_μν - ½g_μν R
        for i in range(self.grid_shape[0]):
            for j in range(self.grid_shape[1]):
                for k in range(self.grid_shape[2]):
                    for l in range(self.grid_shape[3]):
                        G[i, j, k, l] = R_ricci[i, j, k, l] - 0.5 * self.g_metric[i, j, k, l] * R_scalar[i, j, k, l]
        
        return G
    
    def compute_ricci_tensor(self) -> torch.Tensor:
        """
        Вычисление тензора Риччи R_μν через конечные разности.
        
        R_μν = ∂_ρ Γ^ρ_μν - ∂_ν Γ^ρ_μρ + Γ^ρ_ρλ Γ^λ_μν - Γ^ρ_νλ Γ^λ_μρ
        """
        R = torch.zeros_like(self.g_metric)
        
        # Вычисляем символы Кристоффеля
        christoffel = self.compute_christoffel_symbols()
        
        # Производные символов Кристоффеля (конечные разности)
        dx = self.l_P
        
        for mu in range(4):
            for nu in range(4):
                # Первый член: ∂_ρ Γ^ρ_μν
                for rho in range(4):
                    if rho == 0:  # временная производная
                        continue  # пропускаем для стационарного случая
                    else:
                        # Пространственная производная
                        axis = rho - 1
                        gamma_plus = torch.roll(christoffel[..., rho, mu, nu], -1, dims=axis+1)
                        gamma_minus = torch.roll(christoffel[..., rho, mu, nu], 1, dims=axis+1)
                        R[..., mu, nu] += (gamma_plus - gamma_minus) / (2 * dx)
                
                # Второй член: -∂_ν Γ^ρ_μρ
                if nu > 0:
                    axis = nu - 1
                    for rho in range(4):
                        gamma_trace_plus = torch.roll(christoffel[..., rho, mu, rho], -1, dims=axis+1)
                        gamma_trace_minus = torch.roll(christoffel[..., rho, mu, rho], 1, dims=axis+1)
                        R[..., mu, nu] -= (gamma_trace_plus - gamma_trace_minus) / (2 * dx)
                
                # Нелинейные члены (упрощенная версия)
                for rho in range(4):
                    for lam in range(4):
                        R[..., mu, nu] += christoffel[..., rho, rho, lam] * christoffel[..., lam, mu, nu]
                        R[..., mu, nu] -= christoffel[..., rho, nu, lam] * christoffel[..., lam, mu, rho]
        
        return R
    
    def compute_christoffel_symbols(self) -> torch.Tensor:
        """
        Вычисление символов Кристоффеля Γ^σ_μν = ½ g^σρ (∂_μ g_ρν + ∂_ν g_ρμ - ∂_ρ g_μν)
        """
        gamma = torch.zeros((*self.grid_shape, 4, 4, 4), dtype=self.dtype, device=self.device)
        dx = self.l_P
        
        # Обратная метрика
        g_inv = torch.zeros_like(self.g_metric)
        for i in range(self.grid_shape[0]):
            for j in range(self.grid_shape[1]):
                for k in range(self.grid_shape[2]):
                    for l in range(self.grid_shape[3]):
                        g_inv[i, j, k, l] = torch.inverse(self.g_metric[i, j, k, l])
        
        # Производные метрики (конечные разности)
        for mu in range(4):
            if mu == 0:
                continue  # пропускаем временные производные для стационарного случая
            
            axis = mu - 1
            for rho in range(4):
                for nu in range(4):
                    g_plus = torch.roll(self.g_metric[..., rho, nu], -1, dims=axis+1)
                    g_minus = torch.roll(self.g_metric[..., rho, nu], 1, dims=axis+1)
                    dg_mu = (g_plus - g_minus) / (2 * dx)
                    
                    # Γ^σ_μν
                    for sigma in range(4):
                        gamma[..., sigma, mu, nu] += 0.5 * g_inv[..., sigma, rho] * dg_mu
        
        # Симметризация по нижним индексам
        for sigma in range(4):
            for mu in range(4):
                for nu in range(4):
                    gamma[..., sigma, mu, nu] = 0.5 * (gamma[..., sigma, mu, nu] + gamma[..., sigma, nu, mu])
        
        return gamma
    
    def compute_scalar_curvature(self, R_ricci: torch.Tensor) -> torch.Tensor:
        """Вычисление скалярной кривизны R = g^μν R_μν"""
        R_scalar = torch.zeros(self.grid_shape, dtype=self.dtype, device=self.device)
        
        for i in range(self.grid_shape[0]):
            for j in range(self.grid_shape[1]):
                for k in range(self.grid_shape[2]):
                    for l in range(self.grid_shape[3]):
                        g_inv = torch.inverse(self.g_metric[i, j, k, l])
                        R_scalar[i, j, k, l] = torch.einsum('mn,mn->', g_inv, R_ricci[i, j, k, l])
        
        return R_scalar
    
    def _enforce_constraints(self, delta_g: torch.Tensor) -> torch.Tensor:
        """
        Наложение ограничений на изменение метрики:
        1. Симметрия: g_μν = g_νμ
        2. Сохранение сигнатуры (-+++)
        3. Ограничение на величину изменения
        """
        # Симметризация
        for mu in range(4):
            for nu in range(mu+1, 4):
                avg = 0.5 * (delta_g[..., mu, nu] + delta_g[..., nu, mu])
                delta_g[..., mu, nu] = avg
                delta_g[..., nu, mu] = avg
        
        # Ограничение амплитуды изменения
        max_change = 0.1  # максимальное относительное изменение
        delta_g = torch.clamp(delta_g, -max_change, max_change)
        
        return delta_g
    
    def update_metric(self, delta_g: torch.Tensor):
        """Обновление метрики с проверкой физических ограничений"""
        self.g_metric += delta_g
        
        # Проверка сигнатуры (g_00 должна быть отрицательной)
        self.g_metric[..., 0, 0] = torch.clamp(self.g_metric[..., 0, 0], -2.0, -0.5)
        
        # Пространственные компоненты должны быть положительными
        for i in range(1, 4):
            self.g_metric[..., i, i] = torch.clamp(self.g_metric[..., i, i], 0.5, 2.0)
    
    def check_hamiltonian_constraint(self) -> float:
        """
        Проверка гамильтонова ограничения (constraint).
        В ОТО: H = R + K^ij K_ij - K^2 - 16πG ρ = 0
        
        Returns:
            Средняя величина нарушения ограничения
        """
        R_scalar = self.compute_scalar_curvature(self.compute_ricci_tensor())
        
        # Упрощенная версия: проверяем только скалярную кривизну
        constraint_violation = torch.mean(torch.abs(R_scalar))
        
        return constraint_violation.item()
    
    def evolve_step(self, particles: torch.Tensor, dt: float) -> Tuple[torch.Tensor, dict]:
        """
        Один шаг самосогласованной эволюции:
        1. Вычисление T_μν из частиц
        2. Решение уравнений Эйнштейна
        3. Обновление метрики
        4. Эволюция частиц в новой метрике
        
        Args:
            particles: текущее состояние частиц
            dt: шаг времени
        
        Returns:
            new_particles: обновленное состояние частиц
            diagnostics: диагностическая информация
        """
        # 1. Вычисляем тензор энергии-импульса
        T = self.compute_energy_momentum_tensor(particles)
        
        # 2. Решаем уравнения Эйнштейна
        delta_g = self.solve_einstein_equations(T, relaxation_param=0.05)
        
        # 3. Обновляем метрику
        self.update_metric(delta_g)
        
        # 4. Эволюция частиц (используем существующий движок)
        from engine import batch_geodesic
        
        # Интерполируем метрику для частиц
        g_locals = self._interpolate_metric_for_particles(particles)
        new_particles = batch_geodesic(particles, g_locals)
        
        # 5. Диагностика
        # Вычисляем след метрики
        metric_flat = self.g_metric.reshape(-1, 4, 4)
        traces = torch.stack([torch.trace(metric_flat[i]) for i in range(metric_flat.shape[0])])
        
        diagnostics = {
            'metric_trace': torch.mean(traces).item(),
            'energy_density': torch.mean(T[..., 0, 0]).item(),
            'curvature_scalar': torch.mean(self.compute_scalar_curvature(self.compute_ricci_tensor())).item(),
            'constraint_violation': self.check_hamiltonian_constraint(),
            'max_delta_g': torch.max(torch.abs(delta_g)).item()
        }
        
        # Сохраняем в историю
        for key, value in diagnostics.items():
            self.history[key].append(value)
        
        return new_particles, diagnostics
    
    def _interpolate_metric_for_particles(self, particles: torch.Tensor) -> torch.Tensor:
        """Интерполяция метрики для позиций частиц"""
        N = particles.shape[0]
        g_locals = torch.zeros((N, 4, 4), dtype=self.dtype, device=self.device)
        
        for p_idx in range(N):
            pos = particles[p_idx, 1:4]
            
            # Индексы ближайшего узла
            i = int(torch.clamp(pos[0] / self.l_P, 0, self.grid_shape[1]-1))
            j = int(torch.clamp(pos[1] / self.l_P, 0, self.grid_shape[2]-1))
            k = int(torch.clamp(pos[2] / self.l_P, 0, self.grid_shape[3]-1))
            
            g_locals[p_idx] = self.g_metric[0, i, j, k]
        
        return g_locals
    
    def detect_planck_stars(self, threshold_curvature: float = 1e50) -> list:
        """
        Детектирование планковских звезд и микро-черных дыр.
        
        Критерий: области с экстремальной кривизной R > R_threshold
        """
        R_scalar = self.compute_scalar_curvature(self.compute_ricci_tensor())
        
        # Находим области с высокой кривизной
        high_curvature_mask = torch.abs(R_scalar) > threshold_curvature
        
        # Подсчет связных компонент (упрощенно)
        planck_stars = []
        
        if torch.any(high_curvature_mask):
            indices = torch.nonzero(high_curvature_mask)
            
            for idx in indices:
                i, j, k, l = idx.tolist()
                curvature_value = R_scalar[i, j, k, l].item()
                
                planck_stars.append({
                    'position': (i, j, k, l),
                    'curvature': curvature_value,
                    'metric': self.g_metric[i, j, k, l].cpu().numpy()
                })
        
        return planck_stars
    
    def save_state(self, filename: str):
        """Сохранение состояния симуляции"""
        with h5py.File(filename, 'w') as f:
            f.create_dataset('metric', data=self.g_metric.cpu().numpy())
            f.create_dataset('pi_metric', data=self.pi_metric.cpu().numpy())
            
            # История
            for key, values in self.history.items():
                f.create_dataset(f'history/{key}', data=np.array(values))
            
            # Метаданные
            f.attrs['timestamp'] = str(datetime.now())
            f.attrs['grid_shape'] = self.grid_shape
            f.attrs['l_P'] = self.l_P
            f.attrs['t_P'] = self.t_P


if __name__ == "__main__":
    print("="*70)
    print("ТЕСТ: Самосогласованная гравитационная динамика")
    print("="*70)
    
    # Инициализация
    gravity = SelfConsistentGravity(grid_shape=(4, 4, 4, 4))
    
    # Тестовые частицы
    N = 10
    particles = torch.randn((N, 8), dtype=torch.float64)
    particles[:, 0] = 0.0  # время
    particles[:, 1:4] *= gravity.l_P * 2  # позиции
    particles[:, 4] = 1.0  # u^0
    
    print("\nЗапуск самосогласованной эволюции...")
    
    for step in range(5):
        particles, diag = gravity.evolve_step(particles, dt=gravity.t_P)
        
        print(f"\nШаг {step}:")
        print(f"  Trace(g): {diag['metric_trace']:.6f}")
        print(f"  Плотность энергии: {diag['energy_density']:.6e}")
        print(f"  Скалярная кривизна: {diag['curvature_scalar']:.6e}")
        print(f"  Нарушение ограничения: {diag['constraint_violation']:.6e}")
    
    # Поиск планковских звезд
    planck_stars = gravity.detect_planck_stars()
    print(f"\nОбнаружено планковских звезд: {len(planck_stars)}")
    
    # Сохранение
    gravity.save_state("self_consistent_gravity.h5")
    print("\nСостояние сохранено в: self_consistent_gravity.h5")
