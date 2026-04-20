import h5py
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
from scipy.spatial.distance import pdist, squareform
import json
from datetime import datetime

class QuantumGravityAnalyzer:
    """
    Продвинутый анализатор результатов симуляции квантовой гравитации.
    """
    
    def __init__(self, h5_filename):
        self.filename = h5_filename
        self.data = None
        self.metadata = {}
        self.load_data()
        
    def load_data(self):
        """Загрузка данных из HDF5 файла"""
        print(f"Загрузка данных из {self.filename}...")
        
        with h5py.File(self.filename, 'r') as f:
            self.data = f['particles'][:]  # [steps, particles, 8]
            
            # Загрузка метаданных если есть
            for key in f.attrs.keys():
                self.metadata[key] = f.attrs[key]
        
        self.n_steps, self.n_particles, self.n_dims = self.data.shape
        print(f"  Шагов: {self.n_steps}")
        print(f"  Частиц: {self.n_particles}")
        print(f"  Размерность: {self.n_dims}")
        
        if self.metadata:
            print(f"  Метаданные: {self.metadata}")
    
    def extract_positions(self):
        """Извлечение координат (x, y, z)"""
        return self.data[:, :, 1:4]
    
    def extract_velocities(self):
        """Извлечение скоростей (vx, vy, vz)"""
        return self.data[:, :, 5:8]
    
    def compute_cluster_radius(self):
        """Вычисление среднего радиуса кластера"""
        positions = self.extract_positions()
        radii = np.linalg.norm(positions, axis=2)
        mean_radii = np.mean(radii, axis=1)
        std_radii = np.std(radii, axis=1)
        return mean_radii, std_radii
    
    def compute_center_of_mass(self):
        """Вычисление центра масс на каждом шаге"""
        positions = self.extract_positions()
        return np.mean(positions, axis=1)  # [steps, 3]
    
    def compute_velocity_dispersion(self):
        """Дисперсия скоростей (квантовая диффузия)"""
        velocities = self.extract_velocities()
        mean_vel = np.mean(velocities, axis=1, keepdims=True)
        dispersion = np.mean((velocities - mean_vel)**2, axis=1)
        return dispersion  # [steps, 3]
    
    def compute_fractal_dimension(self, step=-1, eps_min=1e-3, eps_max=10.0, n_eps=20):
        """
        Корреляционная размерность D₂ для фазового облака.
        D₂ = d(log C(ε)) / d(log ε)
        """
        positions = self.extract_positions()[step]  # [particles, 3]
        
        # Парные расстояния
        distances = pdist(positions)
        
        eps_range = np.logspace(np.log10(eps_min), np.log10(eps_max), n_eps)
        correlation_sum = []
        
        for eps in eps_range:
            count = np.sum(distances < eps)
            N = len(positions)
            C = 2 * count / (N * (N - 1)) if N > 1 else 0
            correlation_sum.append(C + 1e-10)  # избегаем log(0)
        
        # Линейная регрессия в log-log пространстве
        log_eps = np.log10(eps_range)
        log_C = np.log10(correlation_sum)
        
        # Используем среднюю часть для фитинга
        mid_start = n_eps // 4
        mid_end = 3 * n_eps // 4
        
        slope, intercept, r_value, _, _ = linregress(
            log_eps[mid_start:mid_end], 
            log_C[mid_start:mid_end]
        )
        
        return slope, r_value**2, (eps_range, correlation_sum)
    
    def compute_energy_conservation(self):
        """Проверка сохранения энергии (для диагностики)"""
        velocities = self.extract_velocities()
        
        # Кинетическая энергия (нерелятивистское приближение)
        kinetic = 0.5 * np.sum(velocities**2, axis=2)  # [steps, particles]
        total_energy = np.sum(kinetic, axis=1)  # [steps]
        
        energy_drift = (total_energy - total_energy[0]) / total_energy[0]
        return total_energy, energy_drift
    
    def compute_phase_space_volume(self):
        """Объем фазового пространства (мера хаотичности)"""
        positions = self.extract_positions()
        velocities = self.extract_velocities()
        
        volumes = []
        for step in range(self.n_steps):
            # Ковариационная матрица в фазовом пространстве (6D)
            phase_coords = np.concatenate([positions[step], velocities[step]], axis=1)
            cov_matrix = np.cov(phase_coords.T)
            
            # Объем ~ sqrt(det(Σ))
            det = np.linalg.det(cov_matrix)
            volume = np.sqrt(np.abs(det)) if det > 0 else 0
            volumes.append(volume)
        
        return np.array(volumes)
    
    def compute_lyapunov_exponent(self, n_pairs=10):
        """
        Оценка максимального показателя Ляпунова.
        Мера экспоненциального расхождения близких траекторий.
        """
        positions = self.extract_positions()
        
        # Выбираем случайные пары близких частиц
        np.random.seed(42)
        pairs = []
        
        for _ in range(n_pairs):
            i, j = np.random.choice(self.n_particles, 2, replace=False)
            pairs.append((i, j))
        
        # Вычисляем расхождение траекторий
        divergences = []
        for i, j in pairs:
            distances = np.linalg.norm(positions[:, i, :] - positions[:, j, :], axis=1)
            
            # Избегаем log(0)
            distances = np.maximum(distances, 1e-10)
            divergences.append(distances)
        
        divergences = np.array(divergences)  # [n_pairs, steps]
        mean_divergence = np.mean(divergences, axis=0)
        
        # Ляпунов: λ ≈ d(log(δ)) / dt
        log_div = np.log(mean_divergence)
        time_steps = np.arange(self.n_steps)
        
        # Линейная регрессия (только растущая часть)
        if len(time_steps) > 10:
            slope, _, r_value, _, _ = linregress(time_steps[5:], log_div[5:])
            return slope, r_value**2, mean_divergence
        else:
            return 0, 0, mean_divergence
    
    def generate_full_report(self, output_dir="analysis_results"):
        """Генерация полного отчета с визуализациями"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        print("\n" + "="*60)
        print("ГЕНЕРАЦИЯ ПОЛНОГО ОТЧЕТА")
        print("="*60)
        
        report = {
            'filename': self.filename,
            'timestamp': str(datetime.now()),
            'n_steps': int(self.n_steps),
            'n_particles': int(self.n_particles),
            'metadata': self.metadata
        }
        
        # 1. Эволюция радиуса кластера
        print("\n1. Анализ радиуса кластера...")
        mean_radii, std_radii = self.compute_cluster_radius()
        
        plt.figure(figsize=(12, 5))
        
        plt.subplot(1, 2, 1)
        plt.plot(mean_radii, 'b-', linewidth=2)
        plt.fill_between(range(len(mean_radii)), 
                         mean_radii - std_radii, 
                         mean_radii + std_radii, 
                         alpha=0.3)
        plt.xlabel('Шаг симуляции')
        plt.ylabel('Радиус кластера')
        plt.title('Эволюция размера кластера')
        plt.grid(True, alpha=0.3)
        
        plt.subplot(1, 2, 2)
        plt.plot(std_radii, 'r-', linewidth=2)
        plt.xlabel('Шаг симуляции')
        plt.ylabel('σ(радиус)')
        plt.title('Дисперсия радиуса (размытие)')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/cluster_evolution.png", dpi=300)
        plt.close()
        
        report['mean_radius_final'] = float(mean_radii[-1])
        report['radius_growth_rate'] = float((mean_radii[-1] - mean_radii[0]) / self.n_steps)
        
        # 2. Дисперсия скоростей (квантовая диффузия)
        print("2. Анализ дисперсии скоростей...")
        vel_dispersion = self.compute_velocity_dispersion()
        
        plt.figure(figsize=(10, 6))
        plt.plot(vel_dispersion[:, 0], label='σ²(vx)', linewidth=2)
        plt.plot(vel_dispersion[:, 1], label='σ²(vy)', linewidth=2)
        plt.plot(vel_dispersion[:, 2], label='σ²(vz)', linewidth=2)
        plt.xlabel('Шаг симуляции')
        plt.ylabel('Дисперсия скорости')
        plt.title('Квантовая диффузия импульса')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.yscale('log')
        plt.savefig(f"{output_dir}/velocity_dispersion.png", dpi=300)
        plt.close()
        
        report['velocity_dispersion_final'] = {
            'vx': float(vel_dispersion[-1, 0]),
            'vy': float(vel_dispersion[-1, 1]),
            'vz': float(vel_dispersion[-1, 2])
        }
        
        # 3. Фрактальная размерность
        print("3. Вычисление фрактальной размерности...")
        D2, r2, (eps_range, corr_sum) = self.compute_fractal_dimension()
        
        plt.figure(figsize=(10, 6))
        plt.loglog(eps_range, corr_sum, 'bo-', linewidth=2, markersize=6)
        plt.xlabel('ε (масштаб)')
        plt.ylabel('C(ε) (корреляционная сумма)')
        plt.title(f'Фрактальная размерность D₂ = {D2:.3f} (R² = {r2:.3f})')
        plt.grid(True, alpha=0.3)
        plt.savefig(f"{output_dir}/fractal_dimension.png", dpi=300)
        plt.close()
        
        report['fractal_dimension'] = float(D2)
        report['fractal_fit_r2'] = float(r2)
        
        # 4. Сохранение энергии
        print("4. Проверка сохранения энергии...")
        total_energy, energy_drift = self.compute_energy_conservation()
        
        plt.figure(figsize=(12, 5))
        
        plt.subplot(1, 2, 1)
        plt.plot(total_energy, 'g-', linewidth=2)
        plt.xlabel('Шаг симуляции')
        plt.ylabel('Полная энергия')
        plt.title('Эволюция энергии системы')
        plt.grid(True, alpha=0.3)
        
        plt.subplot(1, 2, 2)
        plt.plot(energy_drift * 100, 'r-', linewidth=2)
        plt.xlabel('Шаг симуляции')
        plt.ylabel('Дрейф энергии (%)')
        plt.title('Относительный дрейф энергии')
        plt.grid(True, alpha=0.3)
        plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/energy_conservation.png", dpi=300)
        plt.close()
        
        report['energy_drift_percent'] = float(energy_drift[-1] * 100)
        
        # 5. Объем фазового пространства
        print("5. Анализ фазового пространства...")
        phase_volumes = self.compute_phase_space_volume()
        
        plt.figure(figsize=(10, 6))
        plt.semilogy(phase_volumes, 'purple', linewidth=2)
        plt.xlabel('Шаг симуляции')
        plt.ylabel('Объем фазового пространства')
        plt.title('Эволюция фазового объема (теорема Лиувилля)')
        plt.grid(True, alpha=0.3)
        plt.savefig(f"{output_dir}/phase_space_volume.png", dpi=300)
        plt.close()
        
        report['phase_volume_ratio'] = float(phase_volumes[-1] / phase_volumes[0])
        
        # 6. Показатель Ляпунова
        print("6. Вычисление показателя Ляпунова...")
        lyapunov, lyap_r2, divergence = self.compute_lyapunov_exponent()
        
        plt.figure(figsize=(10, 6))
        plt.semilogy(divergence, 'orange', linewidth=2)
        plt.xlabel('Шаг симуляции')
        plt.ylabel('Среднее расхождение траекторий')
        plt.title(f'Показатель Ляпунова λ = {lyapunov:.4f} (R² = {lyap_r2:.3f})')
        plt.grid(True, alpha=0.3)
        plt.savefig(f"{output_dir}/lyapunov_exponent.png", dpi=300)
        plt.close()
        
        report['lyapunov_exponent'] = float(lyapunov)
        report['lyapunov_fit_r2'] = float(lyap_r2)
        
        # 7. Финальное распределение частиц
        print("7. Визуализация финального распределения...")
        positions = self.extract_positions()
        
        fig = plt.figure(figsize=(15, 5))
        
        # XY проекция
        ax1 = fig.add_subplot(131)
        ax1.scatter(positions[-1, :, 0], positions[-1, :, 1], s=1, alpha=0.5)
        ax1.set_xlabel('X')
        ax1.set_ylabel('Y')
        ax1.set_title('Проекция XY')
        ax1.set_aspect('equal')
        ax1.grid(True, alpha=0.3)
        
        # XZ проекция
        ax2 = fig.add_subplot(132)
        ax2.scatter(positions[-1, :, 0], positions[-1, :, 2], s=1, alpha=0.5)
        ax2.set_xlabel('X')
        ax2.set_ylabel('Z')
        ax2.set_title('Проекция XZ')
        ax2.set_aspect('equal')
        ax2.grid(True, alpha=0.3)
        
        # YZ проекция
        ax3 = fig.add_subplot(133)
        ax3.scatter(positions[-1, :, 1], positions[-1, :, 2], s=1, alpha=0.5)
        ax3.set_xlabel('Y')
        ax3.set_ylabel('Z')
        ax3.set_title('Проекция YZ')
        ax3.set_aspect('equal')
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/final_distribution.png", dpi=300)
        plt.close()
        
        # 8. Сохранение отчета в JSON
        report_path = f"{output_dir}/analysis_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\n" + "="*60)
        print("ОТЧЕТ ЗАВЕРШЕН")
        print("="*60)
        print(f"\nРезультаты сохранены в: {output_dir}/")
        print(f"  - Графики: *.png")
        print(f"  - JSON отчет: analysis_report.json")
        print("\nКлючевые метрики:")
        print(f"  Фрактальная размерность: D2 = {D2:.3f}")
        print(f"  Показатель Ляпунова: lambda = {lyapunov:.4f}")
        print(f"  Дрейф энергии: {energy_drift[-1]*100:.2f}%")
        print(f"  Рост радиуса: {report['radius_growth_rate']:.4f} ед/шаг")
        
        return report


def compare_simulations(h5_files, labels=None):
    """Сравнение нескольких симуляций"""
    if labels is None:
        labels = [f"Sim {i+1}" for i in range(len(h5_files))]
    
    plt.figure(figsize=(15, 10))
    
    for idx, (h5_file, label) in enumerate(zip(h5_files, labels)):
        analyzer = QuantumGravityAnalyzer(h5_file)
        
        # Радиус кластера
        plt.subplot(2, 2, 1)
        mean_radii, _ = analyzer.compute_cluster_radius()
        plt.plot(mean_radii, label=label, linewidth=2)
        
        # Дисперсия скоростей
        plt.subplot(2, 2, 2)
        vel_disp = analyzer.compute_velocity_dispersion()
        plt.plot(np.mean(vel_disp, axis=1), label=label, linewidth=2)
        
        # Энергия
        plt.subplot(2, 2, 3)
        energy, _ = analyzer.compute_energy_conservation()
        plt.plot(energy / energy[0], label=label, linewidth=2)
        
        # Фазовый объем
        plt.subplot(2, 2, 4)
        phase_vol = analyzer.compute_phase_space_volume()
        plt.plot(phase_vol / phase_vol[0], label=label, linewidth=2)
    
    plt.subplot(2, 2, 1)
    plt.xlabel('Шаг')
    plt.ylabel('Радиус кластера')
    plt.title('Сравнение радиусов')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 2, 2)
    plt.xlabel('Шаг')
    plt.ylabel('Средняя дисперсия скорости')
    plt.title('Сравнение диффузии')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.yscale('log')
    
    plt.subplot(2, 2, 3)
    plt.xlabel('Шаг')
    plt.ylabel('Нормированная энергия')
    plt.title('Сравнение сохранения энергии')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 2, 4)
    plt.xlabel('Шаг')
    plt.ylabel('Нормированный объем')
    plt.title('Сравнение фазовых объемов')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("comparison_report.png", dpi=300)
    plt.show()


if __name__ == "__main__":
    import sys
    
    # Использование: python advanced_analysis.py <h5_file>
    if len(sys.argv) > 1:
        h5_file = sys.argv[1]
    else:
        # По умолчанию используем существующий файл
        h5_file = "cluster_experiment.h5"
    
    print("="*60)
    print("ПРОДВИНУТЫЙ АНАЛИЗ КВАНТОВОЙ ГРАВИТАЦИИ")
    print("="*60)
    
    analyzer = QuantumGravityAnalyzer(h5_file)
    report = analyzer.generate_full_report()
    
    print("\n[OK] Анализ завершен успешно!")
