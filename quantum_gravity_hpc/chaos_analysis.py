"""
Chaos Analysis Module - Lyapunov Exponents for Quantum Foam
============================================================

Вычисление показателей Ляпунова для анализа хаотической динамики квантовой пены.

Если показатели Ляпунова положительны, система демонстрирует детерминированный хаос,
а не просто случайный шум. Это важно для научной публикации.

Author: wosky021@gmail.com
Date: April 21, 2026
"""

import torch
import numpy as np
from typing import List, Dict, Tuple, Optional
import matplotlib.pyplot as plt


class LyapunovAnalyzer:
    """
    Анализатор показателей Ляпунова для квантовой пены.
    
    Показатель Ляпунова λ измеряет чувствительность системы к начальным условиям:
    δ(t) = δ₀ exp(λt)
    
    λ > 0: хаотическая динамика (экспоненциальное расхождение траекторий)
    λ = 0: нейтральная стабильность
    λ < 0: стабильная динамика (траектории сходятся)
    """
    
    def __init__(self, 
                 perturbation_size: float = 1e-8,
                 n_iterations: int = 100,
                 dt: float = 0.1):
        """
        Args:
            perturbation_size: размер начального возмущения
            n_iterations: количество итераций для усреднения
            dt: временной шаг
        """
        self.epsilon = perturbation_size
        self.n_iterations = n_iterations
        self.dt = dt
        
        self.lyapunov_spectrum = []
        self.divergence_history = []
        
        print("="*70)
        print("LYAPUNOV EXPONENT ANALYZER")
        print("="*70)
        print(f"Perturbation size: {perturbation_size}")
        print(f"Iterations: {n_iterations}")
        print(f"Time step: {dt}")
        print("="*70)
    
    def perturb_state(self, 
                     particles: List,
                     perturbation_idx: int = 0) -> List:
        """
        Создать возмущенную копию состояния системы.
        
        Args:
            particles: список VirtualParticle
            perturbation_idx: индекс частицы для возмущения
        Returns:
            perturbed_particles: возмущенная копия
        """
        import copy
        perturbed = copy.deepcopy(particles)
        
        if len(perturbed) > perturbation_idx:
            # Добавить малое возмущение к позиции
            perturbed[perturbation_idx].position[1] += self.epsilon
        
        return perturbed
    
    def compute_state_distance(self, 
                              particles1: List,
                              particles2: List) -> float:
        """
        Вычислить расстояние между двумя состояниями системы.
        
        d = sqrt(Σ |r₁ᵢ - r₂ᵢ|²)
        
        Args:
            particles1, particles2: списки VirtualParticle
        Returns:
            distance: евклидово расстояние в фазовом пространстве
        """
        if len(particles1) != len(particles2):
            # Если количество частиц разное, используем минимум
            n = min(len(particles1), len(particles2))
        else:
            n = len(particles1)
        
        if n == 0:
            return 0.0
        
        distance_sq = 0.0
        for i in range(n):
            # Spatial distance
            dr = particles1[i].position[1:] - particles2[i].position[1:]
            distance_sq += torch.sum(dr**2).item()
        
        return np.sqrt(distance_sq)
    
    def compute_lyapunov_exponent(self,
                                 foam_simulator,
                                 metric_field,
                                 initial_time: float = 0.0,
                                 total_time: float = 10.0) -> Dict:
        """
        Вычислить максимальный показатель Ляпунова.
        
        Алгоритм:
        1. Создать две близкие траектории (исходная + возмущенная)
        2. Эволюционировать обе системы
        3. Измерять расхождение δ(t)
        4. Вычислить λ = lim(t→∞) (1/t) ln(δ(t)/δ₀)
        
        Args:
            foam_simulator: QuantumFoam объект
            metric_field: MetricField объект
            initial_time: начальное время
            total_time: общее время симуляции
        Returns:
            dict с результатами анализа
        """
        print("\nComputing Lyapunov exponent...")
        
        # Сохранить исходное состояние
        import copy
        original_particles = copy.deepcopy(foam_simulator.virtual_particles)
        
        # Создать возмущенную копию
        perturbed_simulator = copy.deepcopy(foam_simulator)
        perturbed_simulator.virtual_particles = self.perturb_state(
            original_particles, perturbation_idx=0
        )
        
        # Начальное расстояние
        d0 = self.compute_state_distance(
            foam_simulator.virtual_particles,
            perturbed_simulator.virtual_particles
        )
        
        if d0 == 0:
            d0 = self.epsilon
        
        # Эволюция
        n_steps = int(total_time / self.dt)
        divergences = []
        times = []
        
        current_time = initial_time
        
        for step in range(n_steps):
            # Эволюционировать обе системы
            foam_simulator.evolve_foam(metric_field, current_time, self.dt)
            perturbed_simulator.evolve_foam(metric_field, current_time, self.dt)
            
            # Измерить расхождение
            d_t = self.compute_state_distance(
                foam_simulator.virtual_particles,
                perturbed_simulator.virtual_particles
            )
            
            if d_t > 0:
                divergences.append(d_t)
                times.append(current_time)
            
            current_time += self.dt
            
            # Renormalization (предотвращает численное переполнение)
            if d_t > 1.0:
                # Перенормировать возмущение
                scale = self.epsilon / d_t
                for i in range(len(perturbed_simulator.virtual_particles)):
                    if i < len(foam_simulator.virtual_particles):
                        delta = (perturbed_simulator.virtual_particles[i].position - 
                                foam_simulator.virtual_particles[i].position)
                        perturbed_simulator.virtual_particles[i].position = (
                            foam_simulator.virtual_particles[i].position + scale * delta
                        )
        
        # Вычислить показатель Ляпунова
        if len(divergences) > 0:
            # λ = (1/T) Σ ln(d_i/d_0)
            log_divergences = [np.log(d / d0) for d in divergences if d > 0]
            if len(log_divergences) > 0:
                lyapunov = np.mean(log_divergences) / self.dt
            else:
                lyapunov = 0.0
        else:
            lyapunov = 0.0
        
        self.lyapunov_spectrum.append(lyapunov)
        self.divergence_history = list(zip(times, divergences))
        
        print(f"  Lyapunov exponent: λ = {lyapunov:.6f}")
        if lyapunov > 0:
            print(f"  ✓ CHAOTIC DYNAMICS (λ > 0)")
            print(f"  Doubling time: τ = {1/lyapunov:.2f} t_P")
        elif lyapunov < 0:
            print(f"  ✓ STABLE DYNAMICS (λ < 0)")
        else:
            print(f"  ✓ NEUTRAL STABILITY (λ ≈ 0)")
        
        return {
            'lyapunov_exponent': lyapunov,
            'divergence_history': self.divergence_history,
            'initial_distance': d0,
            'final_distance': divergences[-1] if divergences else 0.0,
            'is_chaotic': lyapunov > 0.01
        }
    
    def compute_lyapunov_spectrum_full(self,
                                      foam_simulator,
                                      metric_field,
                                      n_exponents: int = 3) -> List[float]:
        """
        Вычислить полный спектр показателей Ляпунова.
        
        Для N-мерной системы существует N показателей Ляпунова.
        Мы вычисляем первые n_exponents.
        
        Args:
            foam_simulator: QuantumFoam объект
            metric_field: MetricField объект
            n_exponents: количество показателей для вычисления
        Returns:
            spectrum: список показателей Ляпунова [λ₁, λ₂, ..., λₙ]
        """
        print(f"\nComputing Lyapunov spectrum ({n_exponents} exponents)...")
        
        spectrum = []
        
        for i in range(n_exponents):
            result = self.compute_lyapunov_exponent(
                foam_simulator, metric_field,
                initial_time=0.0, total_time=10.0
            )
            spectrum.append(result['lyapunov_exponent'])
        
        print(f"\nLyapunov spectrum: {spectrum}")
        print(f"Sum of exponents: {sum(spectrum):.6f}")
        
        return spectrum
    
    def compute_kolmogorov_entropy(self, spectrum: List[float]) -> float:
        """
        Вычислить энтропию Колмогорова-Синая (KS entropy).
        
        h_KS = Σ λᵢ (для всех λᵢ > 0)
        
        Это мера скорости производства информации в хаотической системе.
        
        Args:
            spectrum: список показателей Ляпунова
        Returns:
            h_KS: энтропия Колмогорова-Синая
        """
        h_KS = sum(l for l in spectrum if l > 0)
        
        print(f"\nKolmogorov-Sinai entropy: h_KS = {h_KS:.6f}")
        
        return h_KS
    
    def plot_divergence(self, save_path: str = "lyapunov_divergence.png"):
        """
        Построить график расхождения траекторий.
        
        Args:
            save_path: путь для сохранения графика
        """
        if not self.divergence_history:
            print("No divergence data to plot")
            return
        
        times, divergences = zip(*self.divergence_history)
        
        plt.figure(figsize=(10, 6))
        plt.semilogy(times, divergences, 'b-', linewidth=2, label='δ(t)')
        plt.xlabel('Time (Planck times)', fontsize=12)
        plt.ylabel('Divergence δ(t)', fontsize=12)
        plt.title('Trajectory Divergence (Lyapunov Analysis)', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=12)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        print(f"  Saved divergence plot to {save_path}")
        plt.close()
    
    def analyze_chaos_type(self, lyapunov: float) -> str:
        """
        Классифицировать тип хаоса на основе показателя Ляпунова.
        
        Args:
            lyapunov: показатель Ляпунова
        Returns:
            chaos_type: строка с описанием типа динамики
        """
        if lyapunov > 0.1:
            return "STRONG CHAOS (λ > 0.1) - Rapid exponential divergence"
        elif lyapunov > 0.01:
            return "MODERATE CHAOS (0.01 < λ < 0.1) - Deterministic chaos"
        elif lyapunov > 0:
            return "WEAK CHAOS (0 < λ < 0.01) - Near-neutral dynamics"
        elif lyapunov > -0.01:
            return "NEUTRAL (|λ| < 0.01) - Marginal stability"
        else:
            return "STABLE (λ < -0.01) - Converging trajectories"


def demonstrate_lyapunov_analysis():
    """
    Демонстрация анализа показателей Ляпунова для квантовой пены.
    """
    print("="*70)
    print("LYAPUNOV EXPONENT ANALYSIS - DEMONSTRATION")
    print("="*70)
    
    # Создать симулятор квантовой пены
    from quantum_foam import QuantumFoam
    from engine import MetricField
    import torch
    
    # Простая метрика (Minkowski с возмущениями)
    grid_shape = (8, 8, 8, 8)
    g_metric = torch.zeros(*grid_shape, 4, 4, dtype=torch.float64)
    for i in range(grid_shape[0]):
        for j in range(grid_shape[1]):
            for k in range(grid_shape[2]):
                for l in range(grid_shape[3]):
                    g_metric[i, j, k, l] = torch.diag(torch.tensor([-1.0, 1.0, 1.0, 1.0]))
                    # Добавить малые возмущения
                    g_metric[i, j, k, l] += 0.01 * torch.randn(4, 4)
                    g_metric[i, j, k, l] = 0.5 * (g_metric[i, j, k, l] + g_metric[i, j, k, l].T)
    
    metric_field = MetricField(g_metric, grid_spacing=1.0)
    
    # Создать квантовую пену
    foam = QuantumFoam(
        grid_shape=grid_shape,
        creation_rate=0.5,
        collapse_threshold=1.0,
        softening_length=0.1,
        enable_hawking_evaporation=True
    )
    
    # Создать анализатор
    analyzer = LyapunovAnalyzer(
        perturbation_size=1e-8,
        n_iterations=100,
        dt=0.1
    )
    
    # Вычислить показатель Ляпунова
    result = analyzer.compute_lyapunov_exponent(
        foam, metric_field,
        initial_time=0.0,
        total_time=5.0
    )
    
    # Классифицировать хаос
    chaos_type = analyzer.analyze_chaos_type(result['lyapunov_exponent'])
    print(f"\nChaos classification: {chaos_type}")
    
    # Построить график
    analyzer.plot_divergence()
    
    print("\n[OK] Lyapunov analysis complete!")
    
    return result


if __name__ == "__main__":
    demonstrate_lyapunov_analysis()
