"""
Модуль 4: Термодинамика и энтропия квантовой гравитации.
Реализует анализ энтропии, голографический принцип и термодинамику черных дыр.
"""

import torch
import numpy as np
from typing import Tuple, List, Dict, Optional
import h5py
from scipy.spatial import ConvexHull
from scipy.stats import entropy as scipy_entropy

class QuantumGravityThermodynamics:
    """
    Термодинамический анализ квантовой гравитации.
    Включает энтропию фон Неймана, голографический принцип, температуру Хокинга.
    """
    
    def __init__(self, grid_shape=(8, 8, 8, 8),
                 device='cpu',
                 dtype=torch.float64):
        
        self.grid_shape = grid_shape
        self.device = device
        self.dtype = dtype
        
        # Физические константы
        self.l_P = 1.616e-35  # планковская длина
        self.t_P = 5.39e-44   # планковское время
        self.m_P = 2.176e-8   # планковская масса
        self.k_B = 1.380649e-23  # постоянная Больцмана
        self.hbar = 1.054571817e-34
        self.c = 3e8
        self.G = 6.67430e-11
        
        # Температура Планка
        self.T_P = np.sqrt(self.hbar * self.c**5 / (self.G * self.k_B**2))
        
        # История термодинамических величин
        self.history = {
            'entropy': [],
            'temperature': [],
            'free_energy': [],
            'information_density': []
        }
        
        print(f"Инициализация термодинамики квантовой гравитации:")
        print(f"  Сетка: {grid_shape}")
        print(f"  Температура Планка: {self.T_P:.3e} K")
        print(f"  Энтропия Планка: {self.k_B:.3e} J/K")
    
    def compute_phase_space_volume(self, particles: torch.Tensor) -> float:
        """
        Вычисление объема фазового пространства.
        V_phase = ∫ d³x d³p
        
        Args:
            particles: [N, 8] - (t, x, y, z, u^0, u^1, u^2, u^3)
        """
        positions = particles[:, 1:4].cpu().numpy()
        velocities = particles[:, 5:8].cpu().numpy()
        
        # Ковариационная матрица в фазовом пространстве (6D)
        phase_coords = np.concatenate([positions, velocities], axis=1)
        cov_matrix = np.cov(phase_coords.T)
        
        # Объем ~ √det(Σ)
        det = np.linalg.det(cov_matrix)
        volume = np.sqrt(np.abs(det)) if det > 0 else 0
        
        return volume
    
    def compute_boltzmann_entropy(self, particles: torch.Tensor, 
                                  n_bins: int = 10) -> float:
        """
        Энтропия Больцмана: S = k_B log W
        где W - число микросостояний
        
        Используем гистограмму фазового пространства для оценки W.
        """
        positions = particles[:, 1:4].cpu().numpy()
        velocities = particles[:, 5:8].cpu().numpy()
        
        # Гистограмма в фазовом пространстве
        phase_coords = np.concatenate([positions, velocities], axis=1)
        
        # Многомерная гистограмма (упрощенно - по каждой координате)
        hist_list = []
        for dim in range(6):
            hist, _ = np.histogram(phase_coords[:, dim], bins=n_bins)
            hist_list.append(hist)
        
        # Совместная вероятность (приближенно)
        p_joint = np.prod(hist_list, axis=0)
        p_joint = p_joint / np.sum(p_joint)
        
        # Энтропия Шеннона (классический аналог)
        S_shannon = scipy_entropy(p_joint[p_joint > 0])
        
        # Энтропия Больцмана
        W = np.exp(S_shannon)
        S_boltzmann = self.k_B * np.log(W)
        
        return S_boltzmann
    
    def compute_von_neumann_entropy(self, density_matrix: torch.Tensor) -> float:
        """
        Энтропия фон Неймана: S = -Tr(ρ log ρ) = -Σ λ_i log λ_i
        
        Args:
            density_matrix: матрица плотности квантовой системы
        """
        # Собственные значения
        eigenvalues = torch.linalg.eigvalsh(density_matrix)
        
        # Убираем нулевые и отрицательные
        eigenvalues = eigenvalues[eigenvalues > 1e-10]
        
        # S = -Σ λ_i log λ_i
        S = -torch.sum(eigenvalues * torch.log(eigenvalues))
        
        return S.item() * self.k_B
    
    def compute_bekenstein_hawking_entropy(self, area: float) -> float:
        """
        Энтропия Бекенштейна-Хокинга для черной дыры:
        S_BH = (k_B c³ A) / (4 ℏ G) = A / (4 l_P²)
        
        Args:
            area: площадь горизонта событий в м²
        """
        S_BH = (self.k_B * self.c**3 * area) / (4 * self.hbar * self.G)
        
        # В планковских единицах
        S_BH_planck = area / (4 * self.l_P**2)
        
        return S_BH
    
    def compute_hawking_temperature(self, mass: float) -> float:
        """
        Температура Хокинга:
        T_H = (ℏ c³) / (8π G M k_B)
        
        Args:
            mass: масса черной дыры в кг
        """
        T_H = (self.hbar * self.c**3) / (8 * np.pi * self.G * mass * self.k_B)
        
        return T_H
    
    def compute_holographic_entropy_boundary(self, particles: torch.Tensor) -> Dict:
        """
        Голографическая энтропия на границе расчетной области.
        
        Голографический принцип: вся информация в объеме закодирована на границе.
        S_boundary = A_boundary / (4 l_P²)
        """
        positions = particles[:, 1:4].cpu().numpy()
        
        # Находим выпуклую оболочку (граница области)
        try:
            hull = ConvexHull(positions)
            area = hull.area * (self.l_P**2)
            volume = hull.volume * (self.l_P**3)
        except:
            # Если не удается построить выпуклую оболочку
            # Оцениваем через радиус
            center = np.mean(positions, axis=0)
            distances = np.linalg.norm(positions - center, axis=1)
            radius = np.max(distances)
            area = 4 * np.pi * radius**2 * (self.l_P**2)
            volume = (4/3) * np.pi * radius**3 * (self.l_P**3)
        
        # Голографическая энтропия
        S_holographic = area / (4 * self.l_P**2)
        
        # Плотность информации (биты на планковскую площадь)
        info_density = S_holographic / (area / self.l_P**2)
        
        results = {
            'boundary_area': area,
            'volume': volume,
            'holographic_entropy': S_holographic * self.k_B,
            'information_density': info_density,
            'entropy_per_particle': S_holographic * self.k_B / len(particles)
        }
        
        return results
    
    def compute_entanglement_entropy_region(self, particles: torch.Tensor,
                                           region_fraction: float = 0.5) -> Dict:
        """
        Энтропия запутанности для подсистемы.
        
        Разделяем систему на регион A и дополнение B.
        S_ent(A) = -Tr(ρ_A log ρ_A)
        """
        N = len(particles)
        N_A = int(N * region_fraction)
        
        # Случайное разделение на регионы
        indices = np.random.permutation(N)
        region_A = indices[:N_A]
        region_B = indices[N_A:]
        
        # Упрощенная оценка через фазовое пространство
        particles_A = particles[region_A]
        particles_B = particles[region_B]
        
        # Объемы фазового пространства
        V_A = self.compute_phase_space_volume(particles_A)
        V_B = self.compute_phase_space_volume(particles_B)
        V_total = self.compute_phase_space_volume(particles)
        
        # Энтропия запутанности (приближенно)
        # S_ent ≈ k_B log(V_total / (V_A * V_B))
        if V_A > 0 and V_B > 0:
            S_ent = self.k_B * np.log(V_total / (V_A * V_B))
        else:
            S_ent = 0
        
        # Площадь границы между регионами (упрощенно)
        positions_A = particles_A[:, 1:4].cpu().numpy()
        positions_B = particles_B[:, 1:4].cpu().numpy()
        
        # Минимальное расстояние между регионами
        from scipy.spatial.distance import cdist
        distances = cdist(positions_A, positions_B)
        min_distance = np.min(distances)
        
        # Оценка площади границы
        N_B = N - N_A
        boundary_area = N_A * N_B / (N**2) * 4 * np.pi * min_distance**2
        
        # Голографическая энтропия границы
        S_boundary = boundary_area / (4 * self.l_P**2) * self.k_B
        
        results = {
            'entanglement_entropy': S_ent,
            'boundary_entropy': S_boundary,
            'ratio': S_ent / S_boundary if S_boundary > 0 else 0,
            'region_A_size': N_A,
            'region_B_size': N - N_A,
            'boundary_area': boundary_area
        }
        
        return results
    
    def compute_thermodynamic_temperature(self, particles: torch.Tensor) -> float:
        """
        Термодинамическая температура через кинетическую энергию:
        T = (2/3) ⟨E_kin⟩ / k_B
        """
        velocities = particles[:, 5:8]
        
        # Кинетическая энергия (нерелятивистское приближение)
        m = 1.674927498e-27  # масса нейтрона
        E_kin = 0.5 * m * torch.sum(velocities**2, dim=1)
        
        # Средняя кинетическая энергия
        E_kin_mean = torch.mean(E_kin)
        
        # Температура
        T = (2.0 / 3.0) * E_kin_mean / self.k_B
        
        return T.item()
    
    def compute_free_energy(self, particles: torch.Tensor, 
                           metric: Optional[torch.Tensor] = None) -> Dict:
        """
        Свободная энергия Гельмгольца: F = E - TS
        
        где E - внутренняя энергия, T - температура, S - энтропия
        """
        # Кинетическая энергия
        velocities = particles[:, 5:8]
        m = 1.674927498e-27
        E_kin = torch.sum(0.5 * m * torch.sum(velocities**2, dim=1))
        
        # Потенциальная энергия (гравитационная)
        E_pot = 0.0
        if metric is not None:
            # Упрощенная оценка через кривизну
            positions = particles[:, 1:4]
            for i, pos in enumerate(positions):
                # Индексы ближайшего узла
                idx = (pos / self.l_P).long()
                idx = torch.clamp(idx, 0, min(self.grid_shape[1:]) - 1)
                
                # Метрика в этой точке
                g = metric[0, idx[0], idx[1], idx[2]]
                
                # Потенциал ~ отклонение от плоской метрики
                eta = torch.diag(torch.tensor([-1.0, 1.0, 1.0, 1.0], dtype=self.dtype))
                delta_g = g - eta
                E_pot += torch.trace(torch.matmul(delta_g, delta_g))
        
        E_total = E_kin.item() + E_pot.item() if isinstance(E_pot, torch.Tensor) else E_kin.item() + E_pot
        
        # Температура
        T = self.compute_thermodynamic_temperature(particles)
        
        # Энтропия
        S = self.compute_boltzmann_entropy(particles)
        
        # Свободная энергия
        F = E_total - T * S
        
        results = {
            'free_energy': F,
            'internal_energy': E_total,
            'kinetic_energy': E_kin.item(),
            'potential_energy': E_pot.item() if isinstance(E_pot, torch.Tensor) else E_pot,
            'temperature': T,
            'entropy': S
        }
        
        return results
    
    def compute_information_content(self, particles: torch.Tensor) -> Dict:
        """
        Информационное содержание системы.
        
        Измеряется в битах на планковский объем.
        """
        N = len(particles)
        
        # Объем системы
        positions = particles[:, 1:4].cpu().numpy()
        center = np.mean(positions, axis=0)
        distances = np.linalg.norm(positions - center, axis=1)
        radius = np.max(distances)
        volume = (4/3) * np.pi * radius**3
        
        # Количество планковских объемов
        n_planck_volumes = volume / (self.l_P**3)
        
        # Информация (биты)
        # Каждая частица несет log2(n_planck_volumes) бит информации о позиции
        # плюс log2(n_velocity_states) о скорости
        info_position = N * np.log2(n_planck_volumes) if n_planck_volumes > 1 else 0
        info_velocity = N * 3 * np.log2(100)  # ~100 состояний на компоненту скорости
        
        total_info = info_position + info_velocity
        
        # Плотность информации
        info_density = total_info / n_planck_volumes if n_planck_volumes > 0 else 0
        
        # Голографический предел
        area = 4 * np.pi * radius**2
        holographic_limit = area / (4 * self.l_P**2)
        
        results = {
            'total_information_bits': total_info,
            'information_density': info_density,
            'holographic_limit': holographic_limit,
            'ratio_to_holographic': total_info / holographic_limit if holographic_limit > 0 else 0,
            'volume_planck_units': n_planck_volumes,
            'area_planck_units': area / (self.l_P**2)
        }
        
        return results
    
    def analyze_black_hole_formation(self, particles: torch.Tensor,
                                     metric: torch.Tensor) -> Dict:
        """
        Анализ возможного формирования микро-черных дыр.
        
        Критерий: масса в объеме радиуса Шварцшильда
        r_s = 2GM/c²
        """
        positions = particles[:, 1:4].cpu().numpy()
        N = len(particles)
        m_particle = 1.674927498e-27  # масса нейтрона
        
        # Центр масс
        center = np.mean(positions, axis=0)
        
        # Радиус системы
        distances = np.linalg.norm(positions - center, axis=1)
        radius = np.max(distances)
        
        # Полная масса
        total_mass = N * m_particle
        
        # Радиус Шварцшильда
        r_schwarzschild = 2 * self.G * total_mass / (self.c**2)
        
        # Критерий формирования черной дыры: r < r_s
        is_black_hole = radius < r_schwarzschild
        
        # Если черная дыра, вычисляем термодинамику
        if is_black_hole:
            # Площадь горизонта
            A_horizon = 4 * np.pi * r_schwarzschild**2
            
            # Энтропия Бекенштейна-Хокинга
            S_BH = self.compute_bekenstein_hawking_entropy(A_horizon)
            
            # Температура Хокинга
            T_H = self.compute_hawking_temperature(total_mass)
            
            # Время испарения
            t_evap = (5120 * np.pi * self.G**2 * total_mass**3) / (self.hbar * self.c**4)
            
            results = {
                'is_black_hole': True,
                'schwarzschild_radius': r_schwarzschild,
                'actual_radius': radius,
                'horizon_area': A_horizon,
                'bekenstein_hawking_entropy': S_BH,
                'hawking_temperature': T_H,
                'evaporation_time': t_evap,
                'mass': total_mass
            }
        else:
            results = {
                'is_black_hole': False,
                'schwarzschild_radius': r_schwarzschild,
                'actual_radius': radius,
                'mass': total_mass,
                'compression_factor': r_schwarzschild / radius
            }
        
        return results
    
    def compute_full_thermodynamics(self, particles: torch.Tensor,
                                   metric: Optional[torch.Tensor] = None) -> Dict:
        """
        Полный термодинамический анализ системы.
        """
        print("Вычисление полной термодинамики...")
        
        results = {}
        
        # 1. Энтропии
        print("  1. Энтропии...")
        results['boltzmann_entropy'] = self.compute_boltzmann_entropy(particles)
        results['holographic'] = self.compute_holographic_entropy_boundary(particles)
        results['entanglement'] = self.compute_entanglement_entropy_region(particles)
        
        # 2. Температура
        print("  2. Температура...")
        results['temperature'] = self.compute_thermodynamic_temperature(particles)
        
        # 3. Свободная энергия
        print("  3. Свободная энергия...")
        results['free_energy'] = self.compute_free_energy(particles, metric)
        
        # 4. Информация
        print("  4. Информационное содержание...")
        results['information'] = self.compute_information_content(particles)
        
        # 5. Черные дыры
        if metric is not None:
            print("  5. Анализ черных дыр...")
            results['black_hole'] = self.analyze_black_hole_formation(particles, metric)
        
        # Сохраняем в историю
        self.history['entropy'].append(results['boltzmann_entropy'])
        self.history['temperature'].append(results['temperature'])
        self.history['free_energy'].append(results['free_energy']['free_energy'])
        self.history['information_density'].append(results['information']['information_density'])
        
        return results
    
    def save_thermodynamics(self, filename: str):
        """Сохранение термодинамических данных"""
        with h5py.File(filename, 'w') as f:
            # История
            for key, values in self.history.items():
                if values:
                    f.create_dataset(f'history/{key}', data=np.array(values))
            
            # Константы
            f.attrs['T_Planck'] = self.T_P
            f.attrs['l_Planck'] = self.l_P
            f.attrs['k_Boltzmann'] = self.k_B


if __name__ == "__main__":
    print("="*70)
    print("ТЕСТ: Термодинамика квантовой гравитации")
    print("="*70)
    
    # Инициализация
    thermo = QuantumGravityThermodynamics(grid_shape=(8, 8, 8, 8))
    
    # Тестовые частицы
    N = 100
    particles = torch.randn((N, 8), dtype=torch.float64)
    particles[:, 0] = 0.0
    particles[:, 1:4] *= thermo.l_P * 10
    particles[:, 4] = 1.0
    particles[:, 5:8] *= 1e5
    
    # Тестовая метрика
    metric = torch.randn((8, 8, 8, 8, 4, 4), dtype=torch.float64) * 0.1
    for i in range(8):
        for j in range(8):
            for k in range(8):
                for l in range(8):
                    metric[i,j,k,l] += torch.eye(4, dtype=torch.float64)
    
    # Полный анализ
    results = thermo.compute_full_thermodynamics(particles, metric)
    
    print("\n" + "="*70)
    print("РЕЗУЛЬТАТЫ ТЕРМОДИНАМИЧЕСКОГО АНАЛИЗА")
    print("="*70)
    
    print(f"\n1. ЭНТРОПИЯ:")
    print(f"   Больцмана: {results['boltzmann_entropy']:.6e} J/K")
    print(f"   Голографическая: {results['holographic']['holographic_entropy']:.6e} J/K")
    print(f"   Запутанности: {results['entanglement']['entanglement_entropy']:.6e} J/K")
    print(f"   Отношение запутанность/граница: {results['entanglement']['ratio']:.4f}")
    
    print(f"\n2. ТЕМПЕРАТУРА:")
    print(f"   T = {results['temperature']:.6e} K")
    print(f"   T/T_Planck = {results['temperature']/thermo.T_P:.6e}")
    
    print(f"\n3. СВОБОДНАЯ ЭНЕРГИЯ:")
    print(f"   F = {results['free_energy']['free_energy']:.6e} J")
    print(f"   E_внутр = {results['free_energy']['internal_energy']:.6e} J")
    print(f"   E_кин = {results['free_energy']['kinetic_energy']:.6e} J")
    
    print(f"\n4. ИНФОРМАЦИЯ:")
    print(f"   Всего бит: {results['information']['total_information_bits']:.6e}")
    print(f"   Плотность: {results['information']['information_density']:.6e} бит/V_P")
    print(f"   Голографический предел: {results['information']['holographic_limit']:.6e}")
    print(f"   Отношение к пределу: {results['information']['ratio_to_holographic']:.4f}")
    
    print(f"\n5. ЧЕРНЫЕ ДЫРЫ:")
    if results['black_hole']['is_black_hole']:
        print(f"   ОБНАРУЖЕНА МИКРО-ЧЕРНАЯ ДЫРА!")
        print(f"   r_Schwarzschild = {results['black_hole']['schwarzschild_radius']:.6e} м")
        print(f"   S_BH = {results['black_hole']['bekenstein_hawking_entropy']:.6e} J/K")
        print(f"   T_Hawking = {results['black_hole']['hawking_temperature']:.6e} K")
    else:
        print(f"   Черная дыра не сформирована")
        print(f"   Фактор сжатия: {results['black_hole']['compression_factor']:.6e}")
    
    # Сохранение
    thermo.save_thermodynamics("quantum_thermodynamics.h5")
    print("\nДанные сохранены в: quantum_thermodynamics.h5")
