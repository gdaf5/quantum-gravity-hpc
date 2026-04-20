"""
Модуль 2: Динамика метрики (Уравнения Уилера-Девитта).
Реализует ADM-формализм для эволюции самого пространства-времени.
Метрика становится динамической системой с кинетической энергией.
"""

import torch
import numpy as np
from typing import Tuple, Optional
import h5py

class ADMMetricEvolution:
    """
    ADM (Arnowitt-Deser-Misner) формализм для динамики метрики.
    Разделяет пространство-время на пространство + время: ds² = -N²dt² + h_ij(dx^i + N^i dt)(dx^j + N^j dt)
    """
    
    def __init__(self, grid_shape=(8, 8, 8), 
                 device='cpu',
                 dtype=torch.float64):
        
        self.grid_shape = grid_shape
        self.device = device
        self.dtype = dtype
        
        # Планковские единицы
        self.l_P = 1.616e-35
        self.t_P = 5.39e-44
        self.c = 3e8
        
        # ADM переменные
        self.h_spatial = self._initialize_spatial_metric()  # 3-метрика h_ij
        self.K_extrinsic = torch.zeros((*grid_shape, 3, 3), dtype=dtype, device=device)  # внешняя кривизна K_ij
        self.N_lapse = torch.ones(grid_shape, dtype=dtype, device=device)  # функция хода N
        self.N_shift = torch.zeros((*grid_shape, 3), dtype=dtype, device=device)  # вектор сдвига N^i
        
        # Сопряженные импульсы (для гамильтоновой формулировки)
        self.pi_h = torch.zeros_like(self.h_spatial)  # π^ij = √h (K^ij - K h^ij)
        
        # История гравитационных волн
        self.gw_history = []
        
        print(f"Инициализация ADM-формализма:")
        print(f"  Пространственная сетка: {grid_shape}")
        print(f"  Степени свободы: {np.prod(grid_shape) * 6}")  # 6 независимых компонент h_ij
    
    def _initialize_spatial_metric(self):
        """Инициализация 3-метрики (плоская + малые возмущения)"""
        h = torch.zeros((*self.grid_shape, 3, 3), dtype=self.dtype, device=self.device)
        
        # Плоская метрика δ_ij
        for i in range(self.grid_shape[0]):
            for j in range(self.grid_shape[1]):
                for k in range(self.grid_shape[2]):
                    h[i, j, k] = torch.eye(3, dtype=self.dtype, device=self.device)
        
        # Малые начальные возмущения (гравитационные волны)
        amplitude = 0.01
        for i in range(3):
            for j in range(i, 3):
                perturbation = torch.randn(self.grid_shape, dtype=self.dtype, device=self.device)
                perturbation = perturbation * amplitude
                
                h[..., i, j] += perturbation
                if i != j:
                    h[..., j, i] += perturbation
        
        return h
    
    def compute_hamiltonian_constraint(self) -> torch.Tensor:
        """
        Гамильтоново ограничение (constraint):
        H = R^(3) + K² - K_ij K^ij = 0
        
        где R^(3) - скалярная кривизна 3-пространства
        """
        # Вычисляем 3D скалярную кривизну
        R_3d = self.compute_3d_scalar_curvature()
        
        # След внешней кривизны
        K_trace = torch.zeros(self.grid_shape, dtype=self.dtype, device=self.device)
        for i in range(self.grid_shape[0]):
            for j in range(self.grid_shape[1]):
                for k in range(self.grid_shape[2]):
                    h_inv = torch.inverse(self.h_spatial[i, j, k])
                    K_trace[i, j, k] = torch.einsum('ij,ij->', h_inv, self.K_extrinsic[i, j, k])
        
        # K_ij K^ij
        K_squared = torch.zeros(self.grid_shape, dtype=self.dtype, device=self.device)
        for i in range(self.grid_shape[0]):
            for j in range(self.grid_shape[1]):
                for k in range(self.grid_shape[2]):
                    h_inv = torch.inverse(self.h_spatial[i, j, k])
                    K_up = torch.einsum('im,jn,mn->ij', h_inv, h_inv, self.K_extrinsic[i, j, k])
                    K_squared[i, j, k] = torch.einsum('ij,ij->', self.K_extrinsic[i, j, k], K_up)
        
        # Гамильтоново ограничение
        H = R_3d + K_trace**2 - K_squared
        
        return H
    
    def compute_momentum_constraint(self) -> torch.Tensor:
        """
        Импульсное ограничение:
        M_i = D_j (K^j_i - δ^j_i K) = 0
        
        где D_j - ковариантная производная
        """
        M = torch.zeros((*self.grid_shape, 3), dtype=self.dtype, device=self.device)
        dx = self.l_P
        
        # Упрощенная версия через конечные разности
        for i in range(3):
            for j in range(3):
                # Производная K^j_i
                if j == 0:
                    K_plus = torch.roll(self.K_extrinsic[..., j, i], -1, dims=0)
                    K_minus = torch.roll(self.K_extrinsic[..., j, i], 1, dims=0)
                elif j == 1:
                    K_plus = torch.roll(self.K_extrinsic[..., j, i], -1, dims=1)
                    K_minus = torch.roll(self.K_extrinsic[..., j, i], 1, dims=1)
                else:
                    K_plus = torch.roll(self.K_extrinsic[..., j, i], -1, dims=2)
                    K_minus = torch.roll(self.K_extrinsic[..., j, i], 1, dims=2)
                
                M[..., i] += (K_plus - K_minus) / (2 * dx)
        
        return M
    
    def compute_3d_scalar_curvature(self) -> torch.Tensor:
        """Вычисление скалярной кривизны 3-пространства R^(3)"""
        R_3d = torch.zeros(self.grid_shape, dtype=self.dtype, device=self.device)
        
        # Вычисляем символы Кристоффеля для 3-метрики
        gamma_3d = self.compute_3d_christoffel()
        
        # Тензор Риччи для 3-пространства (упрощенная версия)
        dx = self.l_P
        
        for i in range(3):
            for j in range(3):
                # Производные символов Кристоффеля
                for k in range(3):
                    if k == 0:
                        gamma_plus = torch.roll(gamma_3d[..., k, i, j], -1, dims=0)
                        gamma_minus = torch.roll(gamma_3d[..., k, i, j], 1, dims=0)
                    elif k == 1:
                        gamma_plus = torch.roll(gamma_3d[..., k, i, j], -1, dims=1)
                        gamma_minus = torch.roll(gamma_3d[..., k, i, j], 1, dims=1)
                    else:
                        gamma_plus = torch.roll(gamma_3d[..., k, i, j], -1, dims=2)
                        gamma_minus = torch.roll(gamma_3d[..., k, i, j], 1, dims=2)
                    
                    R_3d += (gamma_plus - gamma_minus) / (2 * dx)
        
        return R_3d
    
    def compute_3d_christoffel(self) -> torch.Tensor:
        """Символы Кристоффеля для 3-метрики"""
        gamma = torch.zeros((*self.grid_shape, 3, 3, 3), dtype=self.dtype, device=self.device)
        dx = self.l_P
        
        for i in range(self.grid_shape[0]):
            for j in range(self.grid_shape[1]):
                for k in range(self.grid_shape[2]):
                    h_inv = torch.inverse(self.h_spatial[i, j, k])
                    
                    # Производные метрики (конечные разности)
                    for m in range(3):
                        for n in range(3):
                            for p in range(3):
                                # ∂_m h_np
                                if m == 0:
                                    h_plus = self.h_spatial[min(i+1, self.grid_shape[0]-1), j, k, n, p]
                                    h_minus = self.h_spatial[max(i-1, 0), j, k, n, p]
                                elif m == 1:
                                    h_plus = self.h_spatial[i, min(j+1, self.grid_shape[1]-1), k, n, p]
                                    h_minus = self.h_spatial[i, max(j-1, 0), k, n, p]
                                else:
                                    h_plus = self.h_spatial[i, j, min(k+1, self.grid_shape[2]-1), n, p]
                                    h_minus = self.h_spatial[i, j, max(k-1, 0), n, p]
                                
                                dh = (h_plus - h_minus) / (2 * dx)
                                
                                # Γ^l_mn = ½ h^lp (∂_m h_pn + ∂_n h_pm - ∂_p h_mn)
                                for l in range(3):
                                    gamma[i, j, k, l, m, n] += 0.5 * h_inv[l, p] * dh
        
        return gamma
    
    def compute_adm_hamiltonian(self) -> float:
        """
        Вычисление ADM гамильтониана:
        H_ADM = ∫ d³x N √h (R^(3) + K² - K_ij K^ij)
        """
        # Детерминант 3-метрики
        h_det = torch.zeros(self.grid_shape, dtype=self.dtype, device=self.device)
        for i in range(self.grid_shape[0]):
            for j in range(self.grid_shape[1]):
                for k in range(self.grid_shape[2]):
                    h_det[i, j, k] = torch.det(self.h_spatial[i, j, k])
        
        sqrt_h = torch.sqrt(torch.abs(h_det))
        
        # Гамильтоново ограничение
        H_constraint = self.compute_hamiltonian_constraint()
        
        # Интеграл
        integrand = self.N_lapse * sqrt_h * H_constraint
        H_ADM = torch.sum(integrand) * (self.l_P**3)
        
        return H_ADM.item()
    
    def evolve_metric_adm(self, dt: float):
        """
        Эволюция метрики по ADM уравнениям:
        ∂_t h_ij = -2N K_ij + D_i N_j + D_j N_i
        ∂_t K_ij = -D_i D_j N + N(R_ij + K K_ij - 2K_ik K^k_j) + ...
        """
        # 1. Эволюция 3-метрики
        dh_dt = torch.zeros_like(self.h_spatial)
        
        for i in range(self.grid_shape[0]):
            for j in range(self.grid_shape[1]):
                for k in range(self.grid_shape[2]):
                    # -2N K_ij
                    dh_dt[i, j, k] = -2 * self.N_lapse[i, j, k] * self.K_extrinsic[i, j, k]
                    
                    # Добавляем члены с вектором сдвига (упрощенно)
                    # D_i N_j + D_j N_i
        
        self.h_spatial += dh_dt * dt
        
        # 2. Эволюция внешней кривизны
        dK_dt = torch.zeros_like(self.K_extrinsic)
        
        # Вычисляем тензор Риччи 3-пространства
        R_3d_scalar = self.compute_3d_scalar_curvature()
        
        # След K
        K_trace = torch.zeros(self.grid_shape, dtype=self.dtype, device=self.device)
        for i in range(self.grid_shape[0]):
            for j in range(self.grid_shape[1]):
                for k in range(self.grid_shape[2]):
                    h_inv = torch.inverse(self.h_spatial[i, j, k])
                    K_trace[i, j, k] = torch.einsum('ij,ij->', h_inv, self.K_extrinsic[i, j, k])
        
        # Упрощенная эволюция
        for i in range(self.grid_shape[0]):
            for j in range(self.grid_shape[1]):
                for k in range(self.grid_shape[2]):
                    N = self.N_lapse[i, j, k]
                    K = K_trace[i, j, k]
                    
                    # ∂_t K_ij ≈ N(R_ij + K K_ij - 2K_ik K^k_j)
                    dK_dt[i, j, k] = N * (K * self.K_extrinsic[i, j, k])
        
        self.K_extrinsic += dK_dt * dt
        
        # 3. Нормализация для стабильности
        self._enforce_metric_constraints()
    
    def _enforce_metric_constraints(self):
        """Наложение ограничений на метрику для численной стабильности"""
        # Положительная определенность 3-метрики
        for i in range(self.grid_shape[0]):
            for j in range(self.grid_shape[1]):
                for k in range(self.grid_shape[2]):
                    # Проверяем собственные значения
                    eigenvalues = torch.linalg.eigvalsh(self.h_spatial[i, j, k])
                    
                    if torch.any(eigenvalues < 0.1):
                        # Корректируем метрику
                        self.h_spatial[i, j, k] = torch.eye(3, dtype=self.dtype, device=self.device)
        
        # Ограничение на функцию хода
        self.N_lapse = torch.clamp(self.N_lapse, 0.5, 2.0)
    
    def extract_gravitational_waves(self) -> dict:
        """
        Извлечение гравитационных волн из метрики.
        Использует TT-декомпозицию (transverse-traceless).
        """
        # Вычисляем возмущения метрики
        h_perturbation = self.h_spatial - torch.eye(3, dtype=self.dtype, device=self.device)
        
        # TT-проекция (упрощенная версия)
        h_TT = torch.zeros_like(h_perturbation)
        
        for i in range(self.grid_shape[0]):
            for j in range(self.grid_shape[1]):
                for k in range(self.grid_shape[2]):
                    h_ij = h_perturbation[i, j, k]
                    
                    # Убираем след
                    trace = torch.trace(h_ij)
                    h_TT[i, j, k] = h_ij - trace / 3.0 * torch.eye(3, dtype=self.dtype, device=self.device)
        
        # Амплитуда гравитационных волн
        h_plus = torch.mean(h_TT[..., 0, 0] - h_TT[..., 1, 1])
        h_cross = torch.mean(h_TT[..., 0, 1])
        
        # Частота (через временную производную)
        if len(self.gw_history) > 0:
            dh_dt = (h_plus - self.gw_history[-1]['h_plus']) / self.t_P
            frequency = dh_dt / (2 * np.pi * h_plus) if h_plus != 0 else 0
        else:
            frequency = 0
        
        gw_data = {
            'h_plus': h_plus.item(),
            'h_cross': h_cross.item(),
            'frequency': float(frequency) if not isinstance(frequency, float) else frequency,
            'amplitude': torch.sqrt(h_plus**2 + h_cross**2).item()
        }
        
        self.gw_history.append(gw_data)
        
        return gw_data
    
    def compute_gravitational_wave_energy(self) -> float:
        """
        Вычисление энергии гравитационных волн:
        E_GW = (c⁴/32πG) ∫ d³x (∂_t h_TT)²
        """
        if len(self.gw_history) < 2:
            return 0.0
        
        # Временная производная амплитуды
        dh_dt = (self.gw_history[-1]['amplitude'] - self.gw_history[-2]['amplitude']) / self.t_P
        
        # Энергия (в планковских единицах)
        G = 6.67430e-11
        E_GW = (self.c**4 / (32 * np.pi * G)) * dh_dt**2 * (self.l_P**3) * np.prod(self.grid_shape)
        
        return E_GW
    
    def save_adm_state(self, filename: str):
        """Сохранение ADM состояния"""
        with h5py.File(filename, 'w') as f:
            f.create_dataset('h_spatial', data=self.h_spatial.cpu().numpy())
            f.create_dataset('K_extrinsic', data=self.K_extrinsic.cpu().numpy())
            f.create_dataset('N_lapse', data=self.N_lapse.cpu().numpy())
            f.create_dataset('N_shift', data=self.N_shift.cpu().numpy())
            
            # История гравитационных волн
            if self.gw_history:
                gw_array = np.array([[gw['h_plus'], gw['h_cross'], gw['frequency'], gw['amplitude']] 
                                     for gw in self.gw_history])
                f.create_dataset('gw_history', data=gw_array)
            
            f.attrs['grid_shape'] = self.grid_shape
            f.attrs['l_P'] = self.l_P
            f.attrs['t_P'] = self.t_P


if __name__ == "__main__":
    print("="*70)
    print("ТЕСТ: ADM-формализм и динамика метрики")
    print("="*70)
    
    # Инициализация
    adm = ADMMetricEvolution(grid_shape=(6, 6, 6))
    
    print("\nЗапуск эволюции метрики...")
    
    for step in range(10):
        # Эволюция метрики
        adm.evolve_metric_adm(dt=adm.t_P * 0.1)
        
        # Извлечение гравитационных волн
        gw = adm.extract_gravitational_waves()
        
        # Проверка ограничений
        H_constraint = torch.mean(torch.abs(adm.compute_hamiltonian_constraint()))
        
        # Гамильтониан
        H_ADM = adm.compute_adm_hamiltonian()
        
        if step % 2 == 0:
            print(f"\nШаг {step}:")
            print(f"  h_plus: {gw['h_plus']:.6e}")
            print(f"  h_cross: {gw['h_cross']:.6e}")
            print(f"  Амплитуда ГВ: {gw['amplitude']:.6e}")
            print(f"  Частота: {gw['frequency']:.6e} Гц")
            print(f"  Нарушение H: {H_constraint:.6e}")
            print(f"  H_ADM: {H_ADM:.6e}")
    
    # Энергия гравитационных волн
    E_GW = adm.compute_gravitational_wave_energy()
    print(f"\nЭнергия гравитационных волн: {E_GW:.6e} Дж")
    
    # Сохранение
    adm.save_adm_state("adm_metric_evolution.h5")
    print("\nСостояние сохранено в: adm_metric_evolution.h5")
