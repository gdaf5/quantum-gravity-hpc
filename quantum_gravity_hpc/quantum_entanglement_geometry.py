"""
Модуль 3: Квантовая запутанность и нелокальность (ER=EPR).
Реализует связь между геометрией и запутанностью через микро-кротовые норы.
"""

import torch
import numpy as np
from typing import Tuple, List, Dict
import h5py
from scipy.spatial.distance import pdist, squareform

class QuantumEntanglementGeometry:
    """
    Исследование связи между квантовой запутанностью и геометрией пространства-времени.
    Гипотеза ER=EPR: запутанность создает микро-кротовые норы (wormholes).
    """
    
    def __init__(self, grid_shape=(8, 8, 8, 8),
                 device='cpu',
                 dtype=torch.float64):
        
        self.grid_shape = grid_shape
        self.device = device
        self.dtype = dtype
        
        self.l_P = 1.616e-35
        
        # Квантовые состояния в узлах сетки
        self.quantum_states = self._initialize_quantum_states()
        
        # Матрица запутанности (взаимная информация между узлами)
        self.entanglement_matrix = None
        
        # Метрика (для корреляции с запутанностью)
        self.metric = None
        
        # История микро-кротовых нор
        self.wormholes = []
        
        print(f"Инициализация квантовой запутанности:")
        print(f"  Узлов сетки: {np.prod(grid_shape)}")
        print(f"  Размерность Гильбертова пространства: 2^{np.prod(grid_shape)}")
    
    def _initialize_quantum_states(self):
        """
        Инициализация квантовых состояний в узлах сетки.
        Каждый узел - кубит в суперпозиции.
        """
        n_nodes = np.prod(self.grid_shape)
        
        # Состояние каждого узла: |ψ⟩ = α|0⟩ + β|1⟩
        # Представляем как комплексный вектор [α, β]
        states = torch.randn((n_nodes, 2), dtype=torch.complex128, device=self.device)
        
        # Нормализация: |α|² + |β|² = 1
        norms = torch.sqrt(torch.sum(torch.abs(states)**2, dim=1, keepdim=True))
        states = states / norms
        
        return states
    
    def compute_mutual_information(self, node_i: int, node_j: int) -> float:
        """
        Вычисление взаимной информации между двумя узлами:
        I(A:B) = S(ρ_A) + S(ρ_B) - S(ρ_AB)
        
        где S(ρ) = -Tr(ρ log ρ) - энтропия фон Неймана
        """
        # Состояния узлов
        psi_i = self.quantum_states[node_i]
        psi_j = self.quantum_states[node_j]
        
        # Матрицы плотности
        rho_i = torch.outer(psi_i, psi_i.conj())
        rho_j = torch.outer(psi_j, psi_j.conj())
        
        # Совместное состояние (тензорное произведение)
        psi_ij = torch.kron(psi_i, psi_j)
        rho_ij = torch.outer(psi_ij, psi_ij.conj())
        
        # Энтропии фон Неймана
        S_i = self._von_neumann_entropy(rho_i)
        S_j = self._von_neumann_entropy(rho_j)
        S_ij = self._von_neumann_entropy(rho_ij)
        
        # Взаимная информация
        I = S_i + S_j - S_ij
        
        return I.real.item()
    
    def _von_neumann_entropy(self, rho: torch.Tensor) -> torch.Tensor:
        """
        Энтропия фон Неймана: S(ρ) = -Tr(ρ log ρ)
        """
        # Собственные значения матрицы плотности
        eigenvalues = torch.linalg.eigvalsh(rho)
        
        # Убираем нулевые и отрицательные (численные ошибки)
        eigenvalues = eigenvalues[eigenvalues > 1e-10]
        
        # S = -Σ λ_i log λ_i
        S = -torch.sum(eigenvalues * torch.log(eigenvalues))
        
        return S
    
    def build_entanglement_matrix(self):
        """
        Построение матрицы запутанности для всех пар узлов.
        Размер: [n_nodes, n_nodes]
        """
        n_nodes = np.prod(self.grid_shape)
        
        print(f"Вычисление матрицы запутанности ({n_nodes}×{n_nodes})...")
        
        self.entanglement_matrix = torch.zeros((n_nodes, n_nodes), 
                                               dtype=self.dtype, 
                                               device=self.device)
        
        # Вычисляем только верхний треугольник (симметричная матрица)
        for i in range(n_nodes):
            if i % 100 == 0:
                print(f"  Прогресс: {i}/{n_nodes}")
            
            for j in range(i+1, n_nodes):
                I_ij = self.compute_mutual_information(i, j)
                self.entanglement_matrix[i, j] = I_ij
                self.entanglement_matrix[j, i] = I_ij
        
        print("Матрица запутанности построена.")
    
    def compute_curvature_at_nodes(self, metric: torch.Tensor) -> torch.Tensor:
        """
        Вычисление скалярной кривизны в каждом узле сетки.
        
        Args:
            metric: [grid_shape, 4, 4] - метрический тензор
        
        Returns:
            curvature: [n_nodes] - скалярная кривизна в узлах
        """
        self.metric = metric
        n_nodes = np.prod(self.grid_shape)
        curvature = torch.zeros(n_nodes, dtype=self.dtype, device=self.device)
        
        # Упрощенное вычисление через след метрики
        metric_flat = metric.reshape(n_nodes, 4, 4)
        
        for i in range(n_nodes):
            # Отклонение от метрики Минковского
            eta = torch.diag(torch.tensor([-1.0, 1.0, 1.0, 1.0], dtype=self.dtype))
            delta_g = metric_flat[i] - eta
            
            # Приближенная кривизна ~ Tr(δg²)
            curvature[i] = torch.trace(torch.matmul(delta_g, delta_g))
        
        return curvature
    
    def correlate_entanglement_curvature(self, metric: torch.Tensor) -> Dict:
        """
        Корреляция между запутанностью и кривизной.
        Проверка гипотезы: высокая запутанность ↔ высокая кривизна (кротовые норы).
        """
        if self.entanglement_matrix is None:
            self.build_entanglement_matrix()
        
        # Вычисляем кривизну
        curvature = self.compute_curvature_at_nodes(metric)
        
        # Для каждой пары узлов: (запутанность, расстояние, кривизна)
        n_nodes = np.prod(self.grid_shape)
        
        # Преобразуем индексы в координаты
        coords = []
        for idx in range(n_nodes):
            i = idx // (self.grid_shape[1] * self.grid_shape[2] * self.grid_shape[3])
            remainder = idx % (self.grid_shape[1] * self.grid_shape[2] * self.grid_shape[3])
            j = remainder // (self.grid_shape[2] * self.grid_shape[3])
            remainder = remainder % (self.grid_shape[2] * self.grid_shape[3])
            k = remainder // self.grid_shape[3]
            l = remainder % self.grid_shape[3]
            coords.append([i, j, k, l])
        
        coords = np.array(coords)
        
        # Евклидовы расстояния между узлами
        distances = squareform(pdist(coords[:, 1:]))  # только пространственные координаты
        
        # Корреляция Пирсона
        entanglement_flat = self.entanglement_matrix.cpu().numpy().flatten()
        distances_flat = distances.flatten()
        curvature_pairs = []
        
        for i in range(n_nodes):
            for j in range(i+1, n_nodes):
                avg_curvature = (curvature[i] + curvature[j]) / 2
                curvature_pairs.append(avg_curvature.item())
        
        curvature_pairs = np.array(curvature_pairs)
        
        # Корреляции
        from scipy.stats import pearsonr, spearmanr
        
        # Запутанность vs расстояние
        corr_ent_dist, p_ent_dist = pearsonr(entanglement_flat, distances_flat)
        
        # Запутанность vs кривизна
        corr_ent_curv, p_ent_curv = pearsonr(entanglement_flat, curvature_pairs)
        
        # Кривизна vs расстояние
        corr_curv_dist, p_curv_dist = pearsonr(curvature_pairs, distances_flat)
        
        results = {
            'correlation_entanglement_distance': corr_ent_dist,
            'p_value_ent_dist': p_ent_dist,
            'correlation_entanglement_curvature': corr_ent_curv,
            'p_value_ent_curv': p_ent_curv,
            'correlation_curvature_distance': corr_curv_dist,
            'p_value_curv_dist': p_curv_dist,
            'mean_entanglement': np.mean(entanglement_flat),
            'mean_curvature': np.mean(curvature_pairs),
            'max_entanglement': np.max(entanglement_flat),
            'max_curvature': np.max(curvature_pairs)
        }
        
        return results
    
    def detect_wormholes(self, threshold_entanglement: float = 0.5,
                        threshold_curvature: float = 1.0) -> List[Dict]:
        """
        Детектирование микро-кротовых нор.
        
        Критерии:
        1. Высокая взаимная информация (I > threshold)
        2. Высокая локальная кривизна
        3. Пространственное разделение узлов
        """
        if self.entanglement_matrix is None:
            self.build_entanglement_matrix()
        
        n_nodes = np.prod(self.grid_shape)
        wormholes = []
        
        # Преобразуем индексы в координаты
        def idx_to_coords(idx):
            i = idx // (self.grid_shape[1] * self.grid_shape[2] * self.grid_shape[3])
            remainder = idx % (self.grid_shape[1] * self.grid_shape[2] * self.grid_shape[3])
            j = remainder // (self.grid_shape[2] * self.grid_shape[3])
            remainder = remainder % (self.grid_shape[2] * self.grid_shape[3])
            k = remainder // self.grid_shape[3]
            l = remainder % self.grid_shape[3]
            return (i, j, k, l)
        
        # Вычисляем кривизну если метрика доступна
        if self.metric is not None:
            curvature = self.compute_curvature_at_nodes(self.metric)
        else:
            curvature = torch.zeros(n_nodes, dtype=self.dtype, device=self.device)
        
        # Поиск пар с высокой запутанностью
        for i in range(n_nodes):
            for j in range(i+1, n_nodes):
                I_ij = self.entanglement_matrix[i, j].item()
                
                if I_ij > threshold_entanglement:
                    coords_i = idx_to_coords(i)
                    coords_j = idx_to_coords(j)
                    
                    # Пространственное расстояние
                    spatial_dist = np.sqrt(sum((coords_i[k] - coords_j[k])**2 for k in range(1, 4)))
                    
                    # Средняя кривизна
                    avg_curvature = (curvature[i] + curvature[j]) / 2
                    
                    if avg_curvature.item() > threshold_curvature and spatial_dist > 1:
                        wormhole = {
                            'node_i': i,
                            'node_j': j,
                            'coords_i': coords_i,
                            'coords_j': coords_j,
                            'entanglement': I_ij,
                            'curvature': avg_curvature.item(),
                            'spatial_distance': spatial_dist,
                            'throat_radius': self._estimate_throat_radius(I_ij, avg_curvature.item())
                        }
                        wormholes.append(wormhole)
        
        self.wormholes = wormholes
        return wormholes
    
    def _estimate_throat_radius(self, entanglement: float, curvature: float) -> float:
        """
        Оценка радиуса горловины кротовой норы.
        
        Используем соотношение: r_throat ~ √(I / R)
        где I - взаимная информация, R - кривизна
        """
        if curvature > 0:
            r_throat = np.sqrt(entanglement / curvature) * self.l_P
        else:
            r_throat = self.l_P
        
        return r_throat
    
    def compute_holographic_entropy(self, region_indices: List[int]) -> float:
        """
        Вычисление голографической энтропии для региона.
        
        Голографический принцип: S = A / (4 l_P²)
        где A - площадь границы региона
        """
        # Преобразуем индексы в координаты
        coords = []
        for idx in region_indices:
            i = idx // (self.grid_shape[1] * self.grid_shape[2] * self.grid_shape[3])
            remainder = idx % (self.grid_shape[1] * self.grid_shape[2] * self.grid_shape[3])
            j = remainder // (self.grid_shape[2] * self.grid_shape[3])
            remainder = remainder % (self.grid_shape[2] * self.grid_shape[3])
            k = remainder // self.grid_shape[3]
            l = remainder % self.grid_shape[3]
            coords.append([j, k, l])  # только пространственные
        
        coords = np.array(coords)
        
        # Оценка площади границы (упрощенно через выпуклую оболочку)
        from scipy.spatial import ConvexHull
        
        if len(coords) >= 4:
            try:
                hull = ConvexHull(coords)
                area = hull.area * (self.l_P**2)
            except:
                # Если не удается построить выпуклую оболочку
                area = len(region_indices) * (self.l_P**2)
        else:
            area = len(region_indices) * (self.l_P**2)
        
        # Голографическая энтропия
        S_holographic = area / (4 * self.l_P**2)
        
        return S_holographic
    
    def compute_entanglement_entropy(self, region_indices: List[int]) -> float:
        """
        Вычисление энтропии запутанности для региона.
        S_ent = -Tr(ρ_A log ρ_A)
        """
        # Редуцированная матрица плотности для региона
        region_states = self.quantum_states[region_indices]
        
        # Совместное состояние региона (упрощенно)
        psi_region = region_states[0]
        for i in range(1, len(region_states)):
            psi_region = torch.kron(psi_region, region_states[i])
        
        rho_region = torch.outer(psi_region, psi_region.conj())
        
        # Энтропия фон Неймана
        S_ent = self._von_neumann_entropy(rho_region)
        
        return S_ent.real.item()
    
    def verify_holographic_principle(self, n_regions: int = 10) -> Dict:
        """
        Проверка голографического принципа:
        S_entanglement ≈ S_holographic
        """
        n_nodes = np.prod(self.grid_shape)
        results = []
        
        print(f"Проверка голографического принципа для {n_regions} регионов...")
        
        for _ in range(n_regions):
            # Случайный регион
            region_size = np.random.randint(4, min(20, n_nodes//2))
            region_indices = np.random.choice(n_nodes, region_size, replace=False).tolist()
            
            # Энтропии
            S_ent = self.compute_entanglement_entropy(region_indices)
            S_holo = self.compute_holographic_entropy(region_indices)
            
            results.append({
                'region_size': region_size,
                'S_entanglement': S_ent,
                'S_holographic': S_holo,
                'ratio': S_ent / S_holo if S_holo > 0 else 0
            })
        
        # Статистика
        ratios = [r['ratio'] for r in results if r['ratio'] > 0]
        
        summary = {
            'mean_ratio': np.mean(ratios),
            'std_ratio': np.std(ratios),
            'median_ratio': np.median(ratios),
            'results': results
        }
        
        return summary
    
    def save_entanglement_data(self, filename: str):
        """Сохранение данных о запутанности"""
        with h5py.File(filename, 'w') as f:
            f.create_dataset('quantum_states', data=self.quantum_states.cpu().numpy())
            
            if self.entanglement_matrix is not None:
                f.create_dataset('entanglement_matrix', data=self.entanglement_matrix.cpu().numpy())
            
            if self.wormholes:
                # Сохраняем информацию о кротовых норах
                wh_data = np.array([[wh['node_i'], wh['node_j'], wh['entanglement'], 
                                     wh['curvature'], wh['spatial_distance'], wh['throat_radius']]
                                    for wh in self.wormholes])
                f.create_dataset('wormholes', data=wh_data)
            
            f.attrs['grid_shape'] = self.grid_shape
            f.attrs['n_wormholes'] = len(self.wormholes)


if __name__ == "__main__":
    print("="*70)
    print("ТЕСТ: Квантовая запутанность и геометрия (ER=EPR)")
    print("="*70)
    
    # Инициализация (малая сетка для теста)
    qeg = QuantumEntanglementGeometry(grid_shape=(3, 3, 3, 3))
    
    # Построение матрицы запутанности
    qeg.build_entanglement_matrix()
    
    # Тестовая метрика
    metric = torch.randn((3, 3, 3, 3, 4, 4), dtype=torch.float64)
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for l in range(3):
                    metric[i,j,k,l] = torch.eye(4, dtype=torch.float64)
                    metric[i,j,k,l] += torch.randn((4,4), dtype=torch.float64) * 0.1
    
    # Корреляция запутанность-кривизна
    print("\nКорреляция запутанности и кривизны...")
    corr_results = qeg.correlate_entanglement_curvature(metric)
    
    print(f"\nРезультаты корреляции:")
    print(f"  Запутанность vs Кривизна: r = {corr_results['correlation_entanglement_curvature']:.4f}")
    print(f"  p-value: {corr_results['p_value_ent_curv']:.4e}")
    print(f"  Средняя запутанность: {corr_results['mean_entanglement']:.4f}")
    print(f"  Средняя кривизна: {corr_results['mean_curvature']:.4e}")
    
    # Детектирование кротовых нор
    print("\nПоиск микро-кротовых нор...")
    wormholes = qeg.detect_wormholes(threshold_entanglement=0.3, threshold_curvature=0.01)
    
    print(f"Обнаружено кротовых нор: {len(wormholes)}")
    for i, wh in enumerate(wormholes[:3]):
        print(f"\nКротовая нора {i+1}:")
        print(f"  Узлы: {wh['node_i']} ↔ {wh['node_j']}")
        print(f"  Запутанность: {wh['entanglement']:.4f}")
        print(f"  Кривизна: {wh['curvature']:.4e}")
        print(f"  Расстояние: {wh['spatial_distance']:.2f} узлов")
        print(f"  Радиус горловины: {wh['throat_radius']:.4e} м")
    
    # Проверка голографического принципа
    print("\nПроверка голографического принципа...")
    holo_results = qeg.verify_holographic_principle(n_regions=5)
    
    print(f"\nГолографический принцип:")
    print(f"  Среднее отношение S_ent/S_holo: {holo_results['mean_ratio']:.4f}")
    print(f"  Стандартное отклонение: {holo_results['std_ratio']:.4f}")
    
    # Сохранение
    qeg.save_entanglement_data("quantum_entanglement.h5")
    print("\nДанные сохранены в: quantum_entanglement.h5")
