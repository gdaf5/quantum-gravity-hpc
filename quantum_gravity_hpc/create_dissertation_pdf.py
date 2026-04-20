"""
Комплексная визуализация всех результатов для презентации диссертации.
Создает единый PDF отчет со всеми графиками и метриками.
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import h5py
from datetime import datetime

class DissertationVisualizer:
    """
    Создание комплексной визуализации для диссертации.
    """
    
    def __init__(self, results_dir="dissertation_results"):
        self.results_dir = results_dir
        self.h5_files = []
        self.reports = {}
        
        # Поиск всех .h5 файлов
        for file in os.listdir('.'):
            if file.endswith('.h5'):
                self.h5_files.append(file)
        
        print(f"Найдено {len(self.h5_files)} файлов симуляций")
        
        # Загрузка JSON отчетов
        if os.path.exists('analysis_results/analysis_report.json'):
            with open('analysis_results/analysis_report.json', 'r') as f:
                self.reports['main'] = json.load(f)
    
    def create_title_page(self, pdf):
        """Титульная страница"""
        fig = plt.figure(figsize=(11, 8.5))
        fig.text(0.5, 0.7, 'Квантовая гравитация на планковском масштабе',
                ha='center', fontsize=24, weight='bold')
        fig.text(0.5, 0.6, 'Численное моделирование стохастической динамики',
                ha='center', fontsize=16)
        fig.text(0.5, 0.5, 'квантово-метрических флуктуаций',
                ha='center', fontsize=16)
        
        fig.text(0.5, 0.35, f'Дата: {datetime.now().strftime("%Y-%m-%d")}',
                ha='center', fontsize=12)
        fig.text(0.5, 0.3, f'Файлов симуляций: {len(self.h5_files)}',
                ha='center', fontsize=12)
        
        # Ключевые параметры
        params_text = """
        Параметры симуляции:
        • Планковская длина: 1.616 × 10⁻³⁵ м
        • Планковское время: 5.39 × 10⁻⁴⁴ с
        • Размер сетки: 8×8×8×8
        • Интегратор: Velocity Verlet (симплектический)
        • Точность: float64 (двойная)
        """
        
        fig.text(0.5, 0.15, params_text, ha='center', fontsize=10,
                family='monospace', verticalalignment='top')
        
        plt.axis('off')
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def plot_all_trajectories(self, pdf):
        """Сравнение траекторий из всех симуляций"""
        if not self.h5_files:
            return
        
        fig = plt.figure(figsize=(11, 8.5))
        
        for idx, h5_file in enumerate(self.h5_files[:4]):  # максимум 4
            try:
                with h5py.File(h5_file, 'r') as f:
                    data = f['particles'][:]
                    positions = data[:, :, 1:4]
                    
                    # Средний радиус
                    radii = np.linalg.norm(positions, axis=2)
                    mean_radii = np.mean(radii, axis=1)
                    std_radii = np.std(radii, axis=1)
                    
                    ax = plt.subplot(2, 2, idx + 1)
                    ax.plot(mean_radii, linewidth=2, label='Средний радиус')
                    ax.fill_between(range(len(mean_radii)),
                                   mean_radii - std_radii,
                                   mean_radii + std_radii,
                                   alpha=0.3)
                    ax.set_xlabel('Шаг симуляции')
                    ax.set_ylabel('Радиус кластера')
                    ax.set_title(h5_file)
                    ax.grid(True, alpha=0.3)
                    ax.legend()
            
            except Exception as e:
                print(f"Ошибка при обработке {h5_file}: {e}")
        
        plt.suptitle('Эволюция радиуса кластера', fontsize=16, weight='bold')
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def plot_fractal_dimensions(self, pdf):
        """Сравнение фрактальных размерностей"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))
        
        # Данные для графика
        simulations = []
        d2_values = []
        
        for h5_file in self.h5_files:
            try:
                with h5py.File(h5_file, 'r') as f:
                    data = f['particles'][:]
                    positions = data[-1, :, 1:4]  # финальные позиции
                    
                    # Быстрый расчет D2
                    from scipy.spatial.distance import pdist
                    distances = pdist(positions)
                    
                    eps_range = np.logspace(-1, 1, 10)
                    corr_sum = []
                    
                    for eps in eps_range:
                        count = np.sum(distances < eps)
                        N = len(positions)
                        C = 2 * count / (N * (N - 1)) if N > 1 else 0
                        corr_sum.append(C + 1e-10)
                    
                    log_eps = np.log10(eps_range)
                    log_C = np.log10(corr_sum)
                    
                    from scipy.stats import linregress
                    slope, _, _, _, _ = linregress(log_eps[2:8], log_C[2:8])
                    
                    simulations.append(h5_file.replace('.h5', ''))
                    d2_values.append(slope)
            
            except Exception as e:
                print(f"Ошибка D2 для {h5_file}: {e}")
        
        # График 1: Столбчатая диаграмма
        if simulations:
            colors = ['blue' if d < 3 else 'red' if d > 3 else 'green' 
                     for d in d2_values]
            ax1.bar(range(len(simulations)), d2_values, color=colors, alpha=0.7)
            ax1.axhline(y=3.0, color='black', linestyle='--', 
                       label='Классическое значение (D=3)')
            ax1.set_xticks(range(len(simulations)))
            ax1.set_xticklabels(simulations, rotation=45, ha='right')
            ax1.set_ylabel('Фрактальная размерность D2')
            ax1.set_title('Сравнение фрактальных размерностей')
            ax1.legend()
            ax1.grid(True, alpha=0.3, axis='y')
        
        # График 2: Интерпретация
        ax2.text(0.5, 0.8, 'Интерпретация фрактальной размерности:',
                ha='center', fontsize=12, weight='bold', transform=ax2.transAxes)
        
        interpretation = """
        D2 < 3.0: Коллапс в нижнюю размерность
                  (сильная гравитационная связь)
        
        D2 ≈ 3.0: Классическое поведение
                  (слабые квантовые эффекты)
        
        D2 > 3.0: Нелокальные квантовые эффекты
                  (квантовая пена активна)
        
        D2 >> 3.0: Сильная квантовая диффузия
                   (доминирование флуктуаций)
        """
        
        ax2.text(0.1, 0.5, interpretation, fontsize=10,
                family='monospace', verticalalignment='top',
                transform=ax2.transAxes)
        
        if d2_values:
            max_d2 = max(d2_values)
            ax2.text(0.5, 0.1, f'Максимальное D2 = {max_d2:.3f}',
                    ha='center', fontsize=11, weight='bold',
                    transform=ax2.transAxes,
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
        
        ax2.axis('off')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def plot_phase_space_evolution(self, pdf):
        """Эволюция фазового пространства"""
        if not self.h5_files:
            return
        
        h5_file = self.h5_files[0]  # берем первый файл
        
        try:
            with h5py.File(h5_file, 'r') as f:
                data = f['particles'][:]
                
                fig = plt.figure(figsize=(11, 8.5))
                
                # 4 временных среза
                n_steps = data.shape[0]
                time_slices = [0, n_steps//3, 2*n_steps//3, n_steps-1]
                
                for idx, step in enumerate(time_slices):
                    ax = plt.subplot(2, 2, idx + 1, projection='3d')
                    
                    positions = data[step, :, 1:4]
                    
                    ax.scatter(positions[:, 0], positions[:, 1], positions[:, 2],
                              s=1, alpha=0.5, c=positions[:, 2], cmap='viridis')
                    
                    ax.set_xlabel('X')
                    ax.set_ylabel('Y')
                    ax.set_zlabel('Z')
                    ax.set_title(f'Шаг {step} / {n_steps-1}')
                
                plt.suptitle(f'Эволюция фазового пространства ({h5_file})',
                           fontsize=14, weight='bold')
                plt.tight_layout()
                pdf.savefig(fig, bbox_inches='tight')
                plt.close()
        
        except Exception as e:
            print(f"Ошибка при построении фазового пространства: {e}")
    
    def plot_velocity_distributions(self, pdf):
        """Распределения скоростей"""
        if not self.h5_files:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
        axes = axes.flatten()
        
        for idx, h5_file in enumerate(self.h5_files[:4]):
            try:
                with h5py.File(h5_file, 'r') as f:
                    data = f['particles'][:]
                    
                    # Начальные и финальные скорости
                    vel_initial = data[0, :, 5:8].flatten()
                    vel_final = data[-1, :, 5:8].flatten()
                    
                    ax = axes[idx]
                    ax.hist(vel_initial, bins=30, alpha=0.5, label='Начальные', density=True)
                    ax.hist(vel_final, bins=30, alpha=0.5, label='Финальные', density=True)
                    ax.set_xlabel('Скорость')
                    ax.set_ylabel('Плотность вероятности')
                    ax.set_title(h5_file)
                    ax.legend()
                    ax.grid(True, alpha=0.3)
            
            except Exception as e:
                print(f"Ошибка распределения скоростей для {h5_file}: {e}")
        
        plt.suptitle('Распределения скоростей (квантовая диффузия)',
                    fontsize=14, weight='bold')
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def plot_summary_metrics(self, pdf):
        """Сводная таблица метрик"""
        fig = plt.figure(figsize=(11, 8.5))
        ax = fig.add_subplot(111)
        
        # Собираем метрики
        metrics_data = []
        
        for h5_file in self.h5_files:
            try:
                with h5py.File(h5_file, 'r') as f:
                    data = f['particles'][:]
                    
                    n_steps = data.shape[0]
                    n_particles = data.shape[1]
                    
                    # Радиус
                    positions = data[:, :, 1:4]
                    radii = np.linalg.norm(positions, axis=2)
                    mean_radius_initial = np.mean(radii[0])
                    mean_radius_final = np.mean(radii[-1])
                    radius_growth = mean_radius_final - mean_radius_initial
                    
                    # Скорости
                    velocities = data[:, :, 5:8]
                    vel_std_initial = np.std(velocities[0])
                    vel_std_final = np.std(velocities[-1])
                    diffusion_coeff = vel_std_final / vel_std_initial if vel_std_initial > 0 else 0
                    
                    metrics_data.append([
                        h5_file.replace('.h5', ''),
                        n_steps,
                        n_particles,
                        f"{mean_radius_initial:.3f}",
                        f"{mean_radius_final:.3f}",
                        f"{radius_growth:.3f}",
                        f"{diffusion_coeff:.3f}"
                    ])
            
            except Exception as e:
                print(f"Ошибка метрик для {h5_file}: {e}")
        
        if metrics_data:
            # Создаем таблицу
            columns = ['Симуляция', 'Шаги', 'Частицы', 'R_0', 'R_final', 'ΔR', 'D_coeff']
            
            table = ax.table(cellText=metrics_data, colLabels=columns,
                           cellLoc='center', loc='center',
                           bbox=[0, 0, 1, 1])
            
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 2)
            
            # Стилизация заголовков
            for i in range(len(columns)):
                table[(0, i)].set_facecolor('#4CAF50')
                table[(0, i)].set_text_props(weight='bold', color='white')
            
            # Чередующиеся цвета строк
            for i in range(1, len(metrics_data) + 1):
                for j in range(len(columns)):
                    if i % 2 == 0:
                        table[(i, j)].set_facecolor('#f0f0f0')
        
        ax.axis('off')
        ax.set_title('Сводная таблица метрик', fontsize=16, weight='bold', pad=20)
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def create_pdf_report(self, output_file="dissertation_visualization.pdf"):
        """Создание полного PDF отчета"""
        print(f"\nСоздание PDF отчета: {output_file}")
        print("="*60)
        
        with PdfPages(output_file) as pdf:
            print("1. Титульная страница...")
            self.create_title_page(pdf)
            
            print("2. Сравнение траекторий...")
            self.plot_all_trajectories(pdf)
            
            print("3. Фрактальные размерности...")
            self.plot_fractal_dimensions(pdf)
            
            print("4. Эволюция фазового пространства...")
            self.plot_phase_space_evolution(pdf)
            
            print("5. Распределения скоростей...")
            self.plot_velocity_distributions(pdf)
            
            print("6. Сводная таблица...")
            self.plot_summary_metrics(pdf)
            
            # Метаданные PDF
            d = pdf.infodict()
            d['Title'] = 'Квантовая гравитация: Численное моделирование'
            d['Author'] = 'Докторская диссертация'
            d['Subject'] = 'Стохастическая динамика квантово-метрических флуктуаций'
            d['Keywords'] = 'Квантовая гравитация, Планковский масштаб, Численное моделирование'
            d['CreationDate'] = datetime.now()
        
        print(f"\n[OK] PDF отчет создан: {output_file}")
        print(f"Размер файла: {os.path.getsize(output_file) / 1024:.2f} KB")
        
        return output_file


def main():
    """Главная функция"""
    print("="*60)
    print("ВИЗУАЛИЗАЦИЯ РЕЗУЛЬТАТОВ ДИССЕРТАЦИИ")
    print("="*60)
    
    visualizer = DissertationVisualizer()
    
    if not visualizer.h5_files:
        print("\n[ОШИБКА] Не найдено файлов симуляций (.h5)")
        print("Запустите сначала: python run_all_experiments.py")
        return 1
    
    # Создание PDF отчета
    pdf_file = visualizer.create_pdf_report()
    
    print("\n" + "="*60)
    print("ВИЗУАЛИЗАЦИЯ ЗАВЕРШЕНА")
    print("="*60)
    print(f"\nОткройте файл: {pdf_file}")
    print("\nДля презентации диссертации используйте:")
    print("  - dissertation_visualization.pdf - полный отчет")
    print("  - analysis_results/*.png - отдельные графики")
    print("  - dissertation_results/summary.txt - текстовое резюме")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
