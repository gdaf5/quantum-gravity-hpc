"""
Модуль 5: Сравнение с теоретическими пределами.
Анализ scale-dependence, спектральный анализ, сравнение с Loop Quantum Gravity и String Theory.
"""

import torch
import numpy as np
from typing import Tuple, List, Dict, Optional
import h5py
from scipy.stats import linregress
from scipy.signal import welch, periodogram
from scipy.optimize import curve_fit

class TheoreticalComparison:
    """
    Сравнение результатов симуляции с теоретическими предсказаниями:
    - Loop Quantum Gravity (LQG)
    - String Theory
    - Asymptotic Safety
    """
    
    def __init__(self, device='cpu', dtype=torch.float64):
        self.device = device
        self.dtype = dtype
        
        # Физические константы
        self.l_P = 1.616e-35
        self.t_P = 5.39e-44
        self.c = 3e8
        
        # Теоретические предсказания
        self.lqg_spectral_dimension = 2.0  # на планковском масштабе
        self.classical_dimension = 3.0  # на макроскопическом масштабе
        
        print("Инициализация сравнения с теорией:")
        print("  Loop Quantum Gravity: D_spectral = 2.0 (Planck scale)")
        print("  Classical: D = 3.0 (macroscopic)")
    
    def compute_scale_dependent_dimension(self, 
                                         trajectory_bundle: torch.Tensor,
                                         scales: Optional[np.ndarray] = None) -> Dict:
        """
        Вычисление зависимости фрактальной размерности от масштаба.
        
        Ожидается переход: D2(l_P) ≈ 5.5 → D2(l_macro) ≈ 3.0
        
        Args:
            trajectory_bundle: [N_particles, N_steps, 8]
            scales: массив масштабов для анализа
        """
        if scales is None:
            # Логарифмическая шкала от планковской длины до макроскопической
            scales = np.logspace(np.log10(self.l_P), np.log10(self.l_P * 1e10), 20)
        
        dimensions = []
        
        print(f"Вычисление D2 на {len(scales)} масштабах...")
        
        for scale in scales:
            # Огрубление данных до данного масштаба
            coarse_positions = self._coarse_grain(trajectory_bundle, scale)
            
            # Вычисление фрактальной размерности на этом масштабе
            D2 = self._compute_correlation_dimension(coarse_positions)
            
            dimensions.append(D2)
        
        # Аппроксимация перехода
        # Модель: D(l) = D_planck + (D_classical - D_planck) * (1 - exp(-l/l_transition))
        def transition_model(l, D_planck, D_classical, l_transition):
            return D_planck + (D_classical - D_planck) * (1 - np.exp(-l / l_transition))
        
        try:
            popt, pcov = curve_fit(transition_model, scales, dimensions,
                                  p0=[5.0, 3.0, self.l_P * 1e5],
                                  bounds=([2.0, 2.5, self.l_P], [10.0, 4.0, self.l_P * 1e15]))
            
            D_planck_fit, D_classical_fit, l_transition_fit = popt
            fit_success = True
        except:
            D_planck_fit, D_classical_fit, l_transition_fit = np.nan, np.nan, np.nan
            fit_success = False
        
        results = {
            'scales': scales,
            'dimensions': np.array(dimensions),
            'D_planck_scale': dimensions[0],
            'D_macro_scale': dimensions[-1],
            'transition_scale': l_transition_fit if fit_success else np.nan,
            'D_planck_fit': D_planck_fit if fit_success else np.nan,
            'D_classical_fit': D_classical_fit if fit_success else np.nan,
            'fit_success': fit_success
        }
        
        return results
    
    def _coarse_grain(self, trajectory_bundle: torch.Tensor, scale: float) -> np.ndarray:
        """Огрубление траекторий до заданного масштаба"""
        # Берем финальные позиции
        positions = trajectory_bundle[:, -1, 1:4].cpu().numpy()
        
        # Квантование координат до масштаба scale
        coarse_positions = np.floor(positions / scale) * scale
        
        return coarse_positions
    
    def _compute_correlation_dimension(self, positions: np.ndarray,
                                      eps_min: float = None,
                                      eps_max: float = None,
                                      n_eps: int = 15) -> float:
        """Вычисление корреляционной размерности D2"""
        from scipy.spatial.distance import pdist
        
        if eps_min is None:
            eps_min = self.l_P
        if eps_max is None:
            eps_max = np.max(pdist(positions)) / 2
        
        distances = pdist(positions)
        
        eps_range = np.logspace(np.log10(eps_min), np.log10(eps_max), n_eps)
        correlation_sum = []
        
        for eps in eps_range:
            count = np.sum(distances < eps)
            N = len(positions)
            C = 2 * count / (N * (N - 1)) if N > 1 else 0
            correlation_sum.append(C + 1e-10)
        
        # Линейная регрессия в log-log
        log_eps = np.log10(eps_range)
        log_C = np.log10(correlation_sum)
        
        # Используем среднюю часть
        mid_start = n_eps // 4
        mid_end = 3 * n_eps // 4
        
        if mid_end > mid_start:
            slope, _, _, _, _ = linregress(log_eps[mid_start:mid_end], log_C[mid_start:mid_end])
            return slope
        else:
            return 3.0
    
    def analyze_power_spectrum(self, metric_fluctuations: torch.Tensor) -> Dict:
        """
        Спектральный анализ флуктуаций метрики.
        
        Сравнение с предсказаниями:
        - LQG: P(k) ~ k^(-3) на планковском масштабе
        - String Theory: P(k) ~ k^(-2) (гауссов шум)
        - Classical GR: P(k) ~ k^(-5/3) (турбулентность Колмогорова)
        """
        # Преобразуем в numpy
        fluctuations = metric_fluctuations.cpu().numpy()
        
        # Берем одну компоненту метрики (например, g_00)
        if fluctuations.ndim >= 5:
            signal = fluctuations[..., 0, 0].flatten()
        else:
            signal = fluctuations.flatten()
        
        # Вычисляем спектр мощности
        frequencies, power = periodogram(signal, fs=1.0/self.t_P)
        
        # Убираем нулевую частоту
        frequencies = frequencies[1:]
        power = power[1:]
        
        # Аппроксимация степенным законом P(f) ~ f^α
        log_freq = np.log10(frequencies)
        log_power = np.log10(power)
        
        # Линейная регрессия
        slope, intercept, r_value, p_value, std_err = linregress(log_freq, log_power)
        
        # Сравнение с теорией
        lqg_prediction = -3.0
        string_prediction = -2.0
        kolmogorov_prediction = -5.0/3.0
        
        # Какая теория ближе?
        distances = {
            'LQG': abs(slope - lqg_prediction),
            'String Theory': abs(slope - string_prediction),
            'Kolmogorov': abs(slope - kolmogorov_prediction)
        }
        
        best_match = min(distances, key=distances.get)
        
        results = {
            'spectral_index': slope,
            'r_squared': r_value**2,
            'p_value': p_value,
            'frequencies': frequencies,
            'power': power,
            'lqg_prediction': lqg_prediction,
            'string_prediction': string_prediction,
            'kolmogorov_prediction': kolmogorov_prediction,
            'best_match': best_match,
            'distance_to_lqg': distances['LQG'],
            'distance_to_string': distances['String Theory'],
            'distance_to_kolmogorov': distances['Kolmogorov']
        }
        
        return results
    
    def compute_spectral_dimension(self, trajectory_bundle: torch.Tensor,
                                   diffusion_times: Optional[np.ndarray] = None) -> Dict:
        """
        Вычисление спектральной размерности через диффузию.
        
        D_s = -2 d(log P) / d(log σ)
        
        где P - вероятность возврата, σ - время диффузии
        
        LQG предсказывает: D_s → 2 при σ → 0 (планковский масштаб)
        """
        if diffusion_times is None:
            diffusion_times = np.logspace(np.log10(self.t_P), np.log10(self.t_P * 1e5), 15)
        
        return_probabilities = []
        
        print(f"Вычисление спектральной размерности...")
        
        for sigma in diffusion_times:
            # Симуляция диффузии на время σ
            P_return = self._simulate_diffusion_return(trajectory_bundle, sigma)
            return_probabilities.append(P_return)
        
        # Вычисляем спектральную размерность
        log_sigma = np.log10(diffusion_times)
        log_P = np.log10(np.array(return_probabilities) + 1e-10)
        
        # D_s = -2 d(log P) / d(log σ)
        slope, _, r_value, _, _ = linregress(log_sigma, log_P)
        D_spectral = -2 * slope
        
        results = {
            'spectral_dimension': D_spectral,
            'diffusion_times': diffusion_times,
            'return_probabilities': np.array(return_probabilities),
            'r_squared': r_value**2,
            'lqg_prediction': 2.0,
            'classical_prediction': 3.0,
            'deviation_from_lqg': abs(D_spectral - 2.0),
            'deviation_from_classical': abs(D_spectral - 3.0)
        }
        
        return results
    
    def _simulate_diffusion_return(self, trajectory_bundle: torch.Tensor, 
                                   diffusion_time: float) -> float:
        """
        Симуляция диффузии и вычисление вероятности возврата.
        
        P(σ) = вероятность вернуться в начальную точку за время σ
        """
        N_particles = trajectory_bundle.shape[0]
        N_steps = trajectory_bundle.shape[1]
        
        # Начальные позиции
        initial_positions = trajectory_bundle[:, 0, 1:4].cpu().numpy()
        
        # Находим шаг времени, соответствующий diffusion_time
        step_idx = int(diffusion_time / self.t_P)
        step_idx = min(step_idx, N_steps - 1)
        
        # Позиции после диффузии
        final_positions = trajectory_bundle[:, step_idx, 1:4].cpu().numpy()
        
        # Расстояния от начальных позиций
        distances = np.linalg.norm(final_positions - initial_positions, axis=1)
        
        # Вероятность возврата (в пределах планковской длины)
        threshold = self.l_P * 10
        P_return = np.sum(distances < threshold) / N_particles
        
        return P_return
    
    def compare_with_asymptotic_safety(self, curvature_history: List[float]) -> Dict:
        """
        Сравнение с Asymptotic Safety.
        
        Предсказание: гравитационная константа G течет к фиксированной точке
        на высоких энергиях (малых масштабах).
        """
        # Эффективная гравитационная константа через кривизну
        # G_eff ~ R^(-1)
        
        curvatures = np.array(curvature_history)
        G_eff = 1.0 / (curvatures + 1e-10)
        
        # Нормализация к G_Newton
        G_newton = 6.67430e-11
        G_eff_normalized = G_eff / np.mean(G_eff) * G_newton
        
        # Проверяем наличие фиксированной точки
        # Ищем плато в G_eff(scale)
        
        # Производная
        dG_dt = np.gradient(G_eff_normalized)
        
        # Фиксированная точка: dG/dt ≈ 0
        fixed_point_indices = np.where(np.abs(dG_dt) < np.std(dG_dt) * 0.1)[0]
        
        if len(fixed_point_indices) > 0:
            fixed_point_value = np.mean(G_eff_normalized[fixed_point_indices])
            has_fixed_point = True
        else:
            fixed_point_value = np.nan
            has_fixed_point = False
        
        results = {
            'G_effective': G_eff_normalized,
            'has_fixed_point': has_fixed_point,
            'fixed_point_value': fixed_point_value,
            'G_newton': G_newton,
            'ratio_to_newton': fixed_point_value / G_newton if has_fixed_point else np.nan,
            'flow_stability': np.std(dG_dt)
        }
        
        return results
    
    def generate_comparison_report(self, 
                                  trajectory_bundle: torch.Tensor,
                                  metric_fluctuations: torch.Tensor,
                                  curvature_history: List[float]) -> Dict:
        """
        Генерация полного отчета сравнения с теорией.
        """
        print("="*70)
        print("СРАВНЕНИЕ С ТЕОРЕТИЧЕСКИМИ ПРЕДСКАЗАНИЯМИ")
        print("="*70)
        
        report = {}
        
        # 1. Scale-dependence
        print("\n1. Зависимость от масштаба...")
        report['scale_dependence'] = self.compute_scale_dependent_dimension(trajectory_bundle)
        
        # 2. Спектральный анализ
        print("\n2. Спектральный анализ...")
        report['power_spectrum'] = self.analyze_power_spectrum(metric_fluctuations)
        
        # 3. Спектральная размерность
        print("\n3. Спектральная размерность...")
        report['spectral_dimension'] = self.compute_spectral_dimension(trajectory_bundle)
        
        # 4. Asymptotic Safety
        print("\n4. Asymptotic Safety...")
        report['asymptotic_safety'] = self.compare_with_asymptotic_safety(curvature_history)
        
        return report
    
    def print_comparison_summary(self, report: Dict):
        """Вывод резюме сравнения"""
        print("\n" + "="*70)
        print("РЕЗЮМЕ СРАВНЕНИЯ С ТЕОРИЕЙ")
        print("="*70)
        
        # Scale-dependence
        sd = report['scale_dependence']
        print(f"\n1. ЗАВИСИМОСТЬ ОТ МАСШТАБА:")
        print(f"   D2(планковский масштаб) = {sd['D_planck_scale']:.3f}")
        print(f"   D2(макроскопический) = {sd['D_macro_scale']:.3f}")
        if sd['fit_success']:
            print(f"   Масштаб перехода: {sd['transition_scale']:.3e} м")
            print(f"   Ожидается: переход от ~5.5 к 3.0 ✓" if 4.0 < sd['D_planck_scale'] < 7.0 and 2.5 < sd['D_macro_scale'] < 3.5 else "   Отклонение от ожидаемого")
        
        # Спектральный анализ
        ps = report['power_spectrum']
        print(f"\n2. СПЕКТРАЛЬНЫЙ АНАЛИЗ:")
        print(f"   Спектральный индекс: α = {ps['spectral_index']:.3f}")
        print(f"   R² = {ps['r_squared']:.4f}")
        print(f"   Лучшее совпадение: {ps['best_match']}")
        print(f"   Расстояние до LQG (α=-3): {ps['distance_to_lqg']:.3f}")
        print(f"   Расстояние до String Theory (α=-2): {ps['distance_to_string']:.3f}")
        
        # Спектральная размерность
        spd = report['spectral_dimension']
        print(f"\n3. СПЕКТРАЛЬНАЯ РАЗМЕРНОСТЬ:")
        print(f"   D_spectral = {spd['spectral_dimension']:.3f}")
        print(f"   LQG предсказание: {spd['lqg_prediction']:.1f}")
        print(f"   Классическое: {spd['classical_prediction']:.1f}")
        print(f"   Отклонение от LQG: {spd['deviation_from_lqg']:.3f}")
        
        # Asymptotic Safety
        asf = report['asymptotic_safety']
        print(f"\n4. ASYMPTOTIC SAFETY:")
        if asf['has_fixed_point']:
            print(f"   Фиксированная точка обнаружена: G* = {asf['fixed_point_value']:.3e} м³/(кг·с²)")
            print(f"   Отношение G*/G_Newton = {asf['ratio_to_newton']:.3f}")
        else:
            print(f"   Фиксированная точка не обнаружена")
        print(f"   Стабильность потока: {asf['flow_stability']:.3e}")
        
        print("\n" + "="*70)
    
    def save_comparison(self, report: Dict, filename: str):
        """Сохранение результатов сравнения"""
        with h5py.File(filename, 'w') as f:
            # Scale-dependence
            sd = report['scale_dependence']
            f.create_dataset('scale_dependence/scales', data=sd['scales'])
            f.create_dataset('scale_dependence/dimensions', data=sd['dimensions'])
            f.attrs['D_planck_scale'] = sd['D_planck_scale']
            f.attrs['D_macro_scale'] = sd['D_macro_scale']
            
            # Power spectrum
            ps = report['power_spectrum']
            f.create_dataset('power_spectrum/frequencies', data=ps['frequencies'])
            f.create_dataset('power_spectrum/power', data=ps['power'])
            f.attrs['spectral_index'] = ps['spectral_index']
            f.attrs['best_match'] = ps['best_match']
            
            # Spectral dimension
            spd = report['spectral_dimension']
            f.create_dataset('spectral_dimension/diffusion_times', data=spd['diffusion_times'])
            f.create_dataset('spectral_dimension/return_probabilities', data=spd['return_probabilities'])
            f.attrs['spectral_dimension'] = spd['spectral_dimension']
            
            # Asymptotic safety
            asf = report['asymptotic_safety']
            f.create_dataset('asymptotic_safety/G_effective', data=asf['G_effective'])
            f.attrs['has_fixed_point'] = asf['has_fixed_point']


if __name__ == "__main__":
    print("="*70)
    print("ТЕСТ: Сравнение с теоретическими предсказаниями")
    print("="*70)
    
    # Инициализация
    comparison = TheoreticalComparison()
    
    # Тестовые данные
    N_particles = 50
    N_steps = 20
    trajectory_bundle = torch.randn((N_particles, N_steps, 8), dtype=torch.float64)
    trajectory_bundle[:, :, 0] = torch.linspace(0, comparison.t_P * N_steps, N_steps)
    trajectory_bundle[:, :, 1:4] *= comparison.l_P * 100
    
    metric_fluctuations = torch.randn((8, 8, 8, 8, 4, 4), dtype=torch.float64) * 0.1
    
    curvature_history = np.random.randn(100) * 1e50 + 1e51
    
    # Полный отчет
    report = comparison.generate_comparison_report(
        trajectory_bundle,
        metric_fluctuations,
        curvature_history.tolist()
    )
    
    # Вывод резюме
    comparison.print_comparison_summary(report)
    
    # Сохранение
    comparison.save_comparison(report, "theoretical_comparison.h5")
    print("\nРезультаты сохранены в: theoretical_comparison.h5")
