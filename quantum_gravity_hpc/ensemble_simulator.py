import torch
import numpy as np
from engine import batch_geodesic
from logger import TrajectoryLogger
import torch.nn.functional as F
from typing import Tuple, Optional
import h5py

class EnsembleSimulator:
    """
    Симулятор ансамбля частиц для анализа квантовой диффузии.
    Запускает облако частиц через флуктуирующую метрику.
    """
    
    def __init__(self, grid_shape=(8, 8, 8, 8), n_particles=1000, 
                 device='cpu', dtype=torch.float64):
        self.grid_shape = grid_shape
        self.n_particles = n_particles
        self.device = device
        self.dtype = dtype
        
        # Генерация метрического поля с квантовыми флуктуациями
        self.metric_grid = self._generate_quantum_metric()
        
        print(f"Инициализация ансамбля:")
        print(f"  Частиц: {n_particles}")
        print(f"  Сетка метрики: {grid_shape}")
        print(f"  Устройство: {device}")
    
    def _generate_quantum_metric(self, fluctuation_amplitude=0.05):
        """
        Генерация метрики с квантовыми флуктуациями через FFT.
        Спектр: 1/k² (красный шум)
        """
        print("Генерация квантовой метрики...")
        
        # Базовая метрика Минковского
        eta = torch.diag(torch.tensor([-1.0, 1.0, 1.0, 1.0], dtype=self.dtype))
        
        # Создаем сетку метрики
        grid = torch.zeros((*self.grid_shape, 4, 4), dtype=self.dtype, device=self.device)
        
        # Заполняем базовой метрикой
        for i in range(self.grid_shape[0]):
            for j in range(self.grid_shape[1]):
                for k in range(self.grid_shape[2]):
                    for l in range(self.grid_shape[3]):
                        grid[i, j, k, l] = eta
        
        # Добавляем флуктуации через FFT
        for mu in range(4):
            for nu in range(mu, 4):  # только верхний треугольник (симметрия)
                # Генерация в k-пространстве
                k_modes = torch.fft.fftfreq(self.grid_shape[0], device=self.device)
                Kx, Ky, Kz, Kt = torch.meshgrid(k_modes, k_modes, k_modes, k_modes, indexing='ij')
                K_sq = Kx**2 + Ky**2 + Kz**2 + Kt**2
                
                # Спектр 1/k² с отсечками
                spectrum = 1.0 / (K_sq + 1e-2)  # IR cutoff
                spectrum *= torch.exp(-K_sq * 10.0)  # UV cutoff (планковский фильтр)
                
                # Комплексные гауссовы коэффициенты
                real_part = torch.randn(self.grid_shape, dtype=self.dtype, device=self.device)
                imag_part = torch.randn(self.grid_shape, dtype=self.dtype, device=self.device)
                complex_modes = torch.complex(real_part, imag_part) * torch.sqrt(spectrum)
                
                # Обратное FFT для получения физического поля
                fluctuation = torch.fft.ifftn(complex_modes).real
                fluctuation = fluctuation * fluctuation_amplitude
                
                # Добавляем к метрике
                grid[..., mu, nu] += fluctuation
                if mu != nu:
                    grid[..., nu, mu] += fluctuation  # симметрия
        
        print(f"  Амплитуда флуктуаций: {fluctuation_amplitude}")
        print(f"  Средняя флуктуация g_00: {torch.std(grid[..., 0, 0]):.4f}")
        
        return grid
    
    def _initialize_particle_cloud(self, center=(4.0, 4.0, 4.0), 
                                   radius=0.5, velocity_spread=0.1):
        """
        Инициализация облака частиц с гауссовым распределением.
        
        Args:
            center: центр облака в координатах сетки
            radius: радиус облака (σ гауссиана)
            velocity_spread: разброс скоростей
        """
        particles = torch.zeros((self.n_particles, 8), dtype=self.dtype, device=self.device)
        
        # Позиции: гауссово распределение вокруг центра
        for i in range(3):
            particles[:, i+1] = torch.randn(self.n_particles, dtype=self.dtype, device=self.device) * radius + center[i]
        
        # Временная координата
        particles[:, 0] = 0.0
        
        # Скорости: малый разброс вокруг нуля (покоящееся облако)
        particles[:, 4] = 1.0  # u^0 ≈ c (нерелятивистское приближение)
        for i in range(3):
            particles[:, i+5] = torch.randn(self.n_particles, dtype=self.dtype, device=self.device) * velocity_spread
        
        return particles
    
    def get_batch_metrics(self, particles):
        """
        Интерполяция метрики для всех частиц через grid_sample.
        """
        N = particles.shape[0]
        
        # Преобразуем метрику в формат для grid_sample
        # [8, 8, 8, 8, 16] -> [16, 8, 8, 8]
        metric_flat = self.metric_grid.reshape(*self.grid_shape, 16)
        grid_input = metric_flat[0].permute(3, 0, 1, 2).unsqueeze(0)  # [1, 16, 8, 8, 8]
        
        # Нормализуем координаты к [-1, 1] для grid_sample
        coords = particles[:, 1:4].clone()
        for i in range(3):
            coords[:, i] = 2.0 * coords[:, i] / self.grid_shape[i+1] - 1.0
        
        # grid_sample требует [N, D, H, W, 3]
        grid_coords = coords.view(1, 1, 1, N, 3)
        
        # Интерполяция
        g_batch_raw = F.grid_sample(grid_input, grid_coords, 
                                     mode='bilinear', align_corners=True)
        g_batch = g_batch_raw.view(16, N).permute(1, 0)
        
        return g_batch.view(N, 4, 4)
    
    def run_ensemble(self, n_steps=100, log_filename="ensemble_results.h5"):
        """
        Запуск ансамблевой симуляции.
        """
        print(f"\nЗапуск ансамблевой симуляции на {n_steps} шагов...")
        print("="*60)
        
        # Инициализация
        particles = self._initialize_particle_cloud()
        logger = TrajectoryLogger(log_filename, num_particles=self.n_particles)
        
        # Начальная статистика
        initial_radius = torch.mean(torch.norm(particles[:, 1:4], dim=1))
        initial_vel_std = torch.std(particles[:, 5:8])
        
        print(f"Начальные условия:")
        print(f"  Радиус облака: {initial_radius:.4f}")
        print(f"  σ(скорость): {initial_vel_std:.4f}")
        print()
        
        # Основной цикл
        for step in range(n_steps):
            # Получаем локальные метрики для всех частиц
            g_locals = self.get_batch_metrics(particles)
            
            # Эволюция через геодезические
            particles = batch_geodesic(particles, g_locals)
            
            # Логирование
            logger.log_step(particles)
            
            # Статистика каждые 10 шагов
            if step % 10 == 0:
                mean_r = torch.mean(torch.norm(particles[:, 1:4], dim=1))
                std_r = torch.std(torch.norm(particles[:, 1:4], dim=1))
                vel_std = torch.std(particles[:, 5:8])
                
                print(f"Шаг {step:3d}: R={mean_r:.4f} ± {std_r:.4f}, σ(v)={vel_std:.4f}")
        
        logger.close()
        
        # Финальная статистика
        final_radius = torch.mean(torch.norm(particles[:, 1:4], dim=1))
        final_vel_std = torch.std(particles[:, 5:8])
        
        print()
        print("="*60)
        print("Симуляция завершена!")
        print(f"  Начальный радиус: {initial_radius:.4f}")
        print(f"  Финальный радиус: {final_radius:.4f}")
        print(f"  Рост радиуса: {(final_radius - initial_radius):.4f}")
        print(f"  Начальная σ(v): {initial_vel_std:.4f}")
        print(f"  Финальная σ(v): {final_vel_std:.4f}")
        print(f"  Рост дисперсии: {(final_vel_std / initial_vel_std - 1)*100:.2f}%")
        print(f"\nДанные сохранены в: {log_filename}")
        
        return {
            'initial_radius': initial_radius.item(),
            'final_radius': final_radius.item(),
            'radius_growth': (final_radius - initial_radius).item(),
            'initial_vel_std': initial_vel_std.item(),
            'final_vel_std': final_vel_std.item(),
            'diffusion_coefficient': (final_vel_std / initial_vel_std).item()
        }


class BackReactionSimulator(EnsembleSimulator):
    """
    Расширенный симулятор с обратным влиянием частиц на метрику.
    Реализует упрощенное уравнение Эйнштейна: G_μν = 8πG T_μν
    """
    
    def __init__(self, grid_shape=(8, 8, 8, 8), n_particles=1000,
                 coupling_strength=0.01, device='cpu', dtype=torch.float64):
        super().__init__(grid_shape, n_particles, device, dtype)
        self.coupling_strength = coupling_strength
        self.G_newton = 6.67430e-11  # гравитационная постоянная
        
        print(f"  Обратное влияние: включено")
        print(f"  Сила связи: {coupling_strength}")
    
    def compute_energy_momentum_tensor(self, particles):
        """
        Вычисление тензора энергии-импульса T^μν на сетке.
        Используем PIC (Particle-In-Cell) подход.
        """
        T = torch.zeros((*self.grid_shape, 4, 4), dtype=self.dtype, device=self.device)
        
        # Плотность энергии и импульса в каждой ячейке
        for p_idx in range(self.n_particles):
            # Позиция частицы
            pos = particles[p_idx, 1:4]
            vel = particles[p_idx, 4:8]
            
            # Индексы ближайшей ячейки
            i = int(torch.clamp(pos[0], 0, self.grid_shape[1]-1))
            j = int(torch.clamp(pos[1], 0, self.grid_shape[2]-1))
            k = int(torch.clamp(pos[2], 0, self.grid_shape[3]-1))
            
            # T^μν = ρ u^μ u^ν (для пылевидной материи)
            # Упрощение: ρ = 1 (единичная масса)
            for mu in range(4):
                for nu in range(4):
                    T[0, i, j, k, mu, nu] += vel[mu] * vel[nu]
        
        # Нормировка на объем ячейки
        T /= self.n_particles
        
        return T
    
    def update_metric_with_backreaction(self, particles):
        """
        Обновление метрики с учетом обратного влияния.
        Δg_μν = α * T_μν (упрощенное уравнение Эйнштейна)
        """
        # Вычисляем тензор энергии-импульса
        T = self.compute_energy_momentum_tensor(particles)
        
        # Обновляем метрику
        # В полной ОТО: G_μν = 8πG/c⁴ T_μν
        # Упрощение: δg_μν = α * T_μν
        delta_g = self.coupling_strength * T
        
        # Добавляем к существующей метрике
        self.metric_grid += delta_g
        
        # Нормализация для стабильности
        # Убеждаемся что g_00 остается отрицательной
        self.metric_grid[..., 0, 0] = torch.clamp(self.metric_grid[..., 0, 0], -2.0, -0.5)
        
        return delta_g
    
    def run_with_backreaction(self, n_steps=100, update_metric_every=5,
                              log_filename="backreaction_results.h5"):
        """
        Запуск симуляции с обратным влиянием.
        """
        print(f"\nЗапуск симуляции с обратным влиянием...")
        print(f"  Обновление метрики каждые {update_metric_every} шагов")
        print("="*60)
        
        particles = self._initialize_particle_cloud()
        logger = TrajectoryLogger(log_filename, num_particles=self.n_particles)
        
        # Дополнительное логирование метрики
        metric_log = h5py.File(log_filename.replace('.h5', '_metric.h5'), 'w')
        metric_dataset = metric_log.create_dataset(
            'metric_trace',
            shape=(0,),
            maxshape=(None,),
            dtype='float64'
        )
        
        for step in range(n_steps):
            # Получаем метрики
            g_locals = self.get_batch_metrics(particles)
            
            # Эволюция частиц
            particles = batch_geodesic(particles, g_locals)
            
            # Обратное влияние
            if step % update_metric_every == 0 and step > 0:
                delta_g = self.update_metric_with_backreaction(particles)
                
                # Логируем изменение метрики
                trace_delta = torch.mean(torch.trace(delta_g[0, :, :, :, :, :].reshape(-1, 4, 4)))
                metric_dataset.resize((metric_dataset.shape[0] + 1,))
                metric_dataset[-1] = trace_delta.item()
                
                if step % 10 == 0:
                    print(f"  Шаг {step}: Обновление метрики, Δ(trace) = {trace_delta:.6f}")
            
            # Логирование частиц
            logger.log_step(particles)
            
            if step % 10 == 0:
                mean_r = torch.mean(torch.norm(particles[:, 1:4], dim=1))
                print(f"Шаг {step:3d}: R={mean_r:.4f}")
        
        logger.close()
        metric_log.close()
        
        print("\n" + "="*60)
        print("Симуляция с обратным влиянием завершена!")
        print(f"Данные сохранены в:")
        print(f"  Частицы: {log_filename}")
        print(f"  Метрика: {log_filename.replace('.h5', '_metric.h5')}")
        
        return log_filename


def compare_with_without_backreaction(n_particles=500, n_steps=50):
    """
    Сравнение симуляций с обратным влиянием и без него.
    """
    print("\n" + "="*60)
    print("СРАВНЕНИЕ: С ОБРАТНЫМ ВЛИЯНИЕМ vs БЕЗ")
    print("="*60)
    
    # 1. Без обратного влияния
    print("\n1. Симуляция БЕЗ обратного влияния:")
    sim_no_back = EnsembleSimulator(n_particles=n_particles)
    results_no_back = sim_no_back.run_ensemble(
        n_steps=n_steps,
        log_filename="no_backreaction.h5"
    )
    
    # 2. С обратным влиянием
    print("\n2. Симуляция С обратным влиянием:")
    sim_with_back = BackReactionSimulator(
        n_particles=n_particles,
        coupling_strength=0.01
    )
    sim_with_back.run_with_backreaction(
        n_steps=n_steps,
        update_metric_every=5,
        log_filename="with_backreaction.h5"
    )
    
    print("\n" + "="*60)
    print("СРАВНИТЕЛЬНЫЙ АНАЛИЗ")
    print("="*60)
    print(f"Без обратного влияния:")
    print(f"  Рост радиуса: {results_no_back['radius_growth']:.4f}")
    print(f"  Коэффициент диффузии: {results_no_back['diffusion_coefficient']:.4f}")
    
    # Анализ с обратным влиянием
    from advanced_analysis import QuantumGravityAnalyzer
    analyzer_back = QuantumGravityAnalyzer("with_backreaction.h5")
    mean_radii_back, _ = analyzer_back.compute_cluster_radius()
    radius_growth_back = mean_radii_back[-1] - mean_radii_back[0]
    
    print(f"\nС обратным влиянием:")
    print(f"  Рост радиуса: {radius_growth_back:.4f}")
    print(f"  Разница: {(radius_growth_back - results_no_back['radius_growth']):.4f}")
    
    # Визуализация сравнения
    import matplotlib.pyplot as plt
    
    analyzer_no_back = QuantumGravityAnalyzer("no_backreaction.h5")
    mean_radii_no_back, _ = analyzer_no_back.compute_cluster_radius()
    
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.plot(mean_radii_no_back, 'b-', linewidth=2, label='Без обратного влияния')
    plt.plot(mean_radii_back, 'r-', linewidth=2, label='С обратным влиянием')
    plt.xlabel('Шаг симуляции')
    plt.ylabel('Средний радиус кластера')
    plt.title('Сравнение эволюции радиуса')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 2, 2)
    difference = mean_radii_back - mean_radii_no_back
    plt.plot(difference, 'g-', linewidth=2)
    plt.xlabel('Шаг симуляции')
    plt.ylabel('Разница радиусов')
    plt.title('Эффект обратного влияния')
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("backreaction_comparison.png", dpi=300)
    print(f"\nГрафик сравнения сохранен: backreaction_comparison.png")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = "ensemble"
    
    if mode == "ensemble":
        # Простая ансамблевая симуляция
        sim = EnsembleSimulator(n_particles=1000)
        sim.run_ensemble(n_steps=100, log_filename="ensemble_results.h5")
        
    elif mode == "backreaction":
        # Симуляция с обратным влиянием
        sim = BackReactionSimulator(n_particles=500, coupling_strength=0.01)
        sim.run_with_backreaction(n_steps=50, log_filename="backreaction_results.h5")
        
    elif mode == "compare":
        # Сравнение обоих режимов
        compare_with_without_backreaction(n_particles=500, n_steps=50)
    
    else:
        print("Использование:")
        print("  python ensemble_simulator.py ensemble      # Ансамблевая симуляция")
        print("  python ensemble_simulator.py backreaction  # С обратным влиянием")
        print("  python ensemble_simulator.py compare       # Сравнение обоих")
