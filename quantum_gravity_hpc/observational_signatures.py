"""
Observational Signatures Module - Virtual Detector
===================================================

Модуль для вычисления наблюдаемых эффектов квантовой пены:
- Задержка распространения света
- Дисперсия гравитационных волн
- Модификация спектра CMB
- Эффекты на интерферометрах

Это мостик между теорией и экспериментом!

Author: wosky021@gmail.com
Date: April 21, 2026
"""

import torch
import numpy as np
from typing import List, Dict, Tuple, Optional
import matplotlib.pyplot as plt


class VirtualDetector:
    """
    Виртуальный детектор для измерения эффектов квантовой пены.
    
    Симулирует прохождение фотонов и гравитационных волн через
    квантовую пену и вычисляет наблюдаемые эффекты.
    """
    
    def __init__(self,
                 detector_position: torch.Tensor,
                 detector_size: float = 1.0,
                 time_resolution: float = 1e-44,  # Planck time
                 energy_resolution: float = 1e-19):  # GeV
        """
        Args:
            detector_position: [4] позиция детектора (t, x, y, z)
            detector_size: размер детектора в планковских длинах
            time_resolution: временное разрешение
            energy_resolution: энергетическое разрешение
        """
        self.position = detector_position
        self.size = detector_size
        self.time_res = time_resolution
        self.energy_res = energy_resolution
        
        # История измерений
        self.photon_arrivals = []
        self.gw_signals = []
        self.time_delays = []
        
        print("="*70)
        print("VIRTUAL DETECTOR - Observational Signatures")
        print("="*70)
        print(f"Position: {detector_position.numpy()}")
        print(f"Size: {detector_size} l_P")
        print(f"Time resolution: {time_resolution} s")
        print(f"Energy resolution: {energy_resolution} GeV")
        print("="*70)
    
    def propagate_photon(self,
                        initial_position: torch.Tensor,
                        initial_momentum: torch.Tensor,
                        metric_field,
                        foam_simulator,
                        max_steps: int = 1000) -> Dict:
        """
        Симулировать распространение фотона через квантовую пену.
        
        Фотон следует null-геодезической: ds² = 0
        Квантовая пена создает эффективный показатель преломления:
        n(E, L) ≈ 1 + α(E/E_P)(L/l_P)^β
        
        Args:
            initial_position: [4] начальная позиция
            initial_momentum: [4] начальный 4-импульс
            metric_field: MetricField объект
            foam_simulator: QuantumFoam объект
            max_steps: максимальное количество шагов
        Returns:
            dict с результатами распространения
        """
        print("\nPropagating photon through quantum foam...")
        
        # Текущее состояние
        x = initial_position.clone()
        p = initial_momentum.clone()
        
        # Энергия фотона
        E_photon = torch.abs(p[0]).item()
        
        # Траектория
        trajectory = [x.clone()]
        proper_times = [0.0]
        
        # Параметры дисперсии
        alpha = 1e-3  # коэффициент дисперсии
        beta = 2.0    # степень дисперсии
        
        # Планковская энергия
        E_planck = 1.0  # в планковских единицах
        
        dt = 0.01  # временной шаг
        proper_time = 0.0
        
        accumulated_delay = 0.0
        
        for step in range(max_steps):
            # Получить метрику в текущей точке
            g = metric_field.interpolate_metric(x)
            
            # Вычислить локальную плотность энергии пены
            rho_foam = foam_simulator.compute_local_energy_density(x, metric_field)
            
            # Эффективный показатель преломления
            # n ≈ 1 + α(E/E_P)(ρ/ρ_P)^β
            n_eff = 1.0 + alpha * (E_photon / E_planck) * (rho_foam ** beta)
            
            # Скорость света в среде: v = c/n
            v_eff = 1.0 / n_eff  # c = 1 в планковских единицах
            
            # Задержка времени
            delay = dt * (1.0 - v_eff)
            accumulated_delay += delay
            
            # Обновить позицию (упрощенно: прямолинейное движение)
            # В реальности нужно решать геодезическое уравнение
            direction = p[1:] / torch.norm(p[1:])
            x[1:] += direction * v_eff * dt
            x[0] += dt
            
            proper_time += dt
            
            # Сохранить траекторию
            trajectory.append(x.clone())
            proper_times.append(proper_time)
            
            # Проверить достижение детектора
            distance = torch.norm(x[1:] - self.position[1:]).item()
            if distance < self.size:
                print(f"  Photon reached detector at t = {proper_time:.6f} t_P")
                break
        
        # Вычислить наблюдаемую задержку
        # Δt = L × (n - 1) / c ≈ L × α(E/E_P)(ρ/ρ_P)^β
        path_length = torch.norm(x[1:] - initial_position[1:]).item()
        expected_delay = path_length * alpha * (E_photon / E_planck) * (rho_foam ** beta)
        
        self.time_delays.append(accumulated_delay)
        
        print(f"  Path length: {path_length:.6f} l_P")
        print(f"  Accumulated delay: {accumulated_delay:.6e} t_P")
        print(f"  Expected delay: {expected_delay:.6e} t_P")
        print(f"  Relative delay: Δt/t = {accumulated_delay/proper_time:.6e}")
        
        return {
            'trajectory': trajectory,
            'proper_times': proper_times,
            'accumulated_delay': accumulated_delay,
            'path_length': path_length,
            'final_position': x,
            'refractive_index': n_eff
        }
    
    def compute_gw_dispersion(self,
                             frequency: float,
                             distance: float,
                             foam_density: float) -> Dict:
        """
        Вычислить дисперсию гравитационных волн в квантовой пене.
        
        Дисперсионное соотношение:
        ω² = k²c² + α(kl_P)^n
        
        Это приводит к зависимости скорости от частоты:
        v_g = dω/dk ≈ c(1 - α(kl_P)^n / 2)
        
        Args:
            frequency: частота GW (в Hz)
            distance: расстояние до источника (в Mpc)
            foam_density: плотность квантовой пены (ρ/ρ_P)
        Returns:
            dict с результатами дисперсии
        """
        print(f"\nComputing GW dispersion for f = {frequency} Hz...")
        
        # Константы
        c = 3e8  # m/s
        l_P = 1.616e-35  # m
        
        # Волновое число
        k = 2 * np.pi * frequency / c
        
        # Параметры дисперсии
        alpha = 1e-3
        n = 2.0  # квадратичная дисперсия
        
        # Дисперсионная поправка
        dispersion_term = alpha * (k * l_P) ** n
        
        # Групповая скорость
        v_g = c * (1.0 - dispersion_term / 2.0)
        
        # Задержка времени на расстоянии L
        # Δt = L/v_g - L/c ≈ (L/c) × (dispersion_term / 2)
        L_meters = distance * 3.086e22  # Mpc to meters
        delay = (L_meters / c) * (dispersion_term / 2.0)
        
        # Зависимость от плотности пены
        delay_foam = delay * foam_density
        
        print(f"  Wave number: k = {k:.6e} m⁻¹")
        print(f"  Dispersion term: {dispersion_term:.6e}")
        print(f"  Group velocity: v_g = {v_g:.6e} m/s")
        print(f"  Time delay: Δt = {delay_foam:.6e} s")
        print(f"  Relative delay: Δt/t = {delay_foam / (L_meters/c):.6e}")
        
        return {
            'frequency': frequency,
            'wave_number': k,
            'dispersion_term': dispersion_term,
            'group_velocity': v_g,
            'time_delay': delay_foam,
            'distance': distance
        }
    
    def compute_cmb_spectral_distortion(self,
                                       foam_density: float,
                                       temperature: float = 2.725) -> Dict:
        """
        Вычислить искажение спектра CMB из-за квантовой пены.
        
        Квантовая пена может создавать:
        1. μ-искажения (энергетическая инжекция)
        2. y-искажения (компонизация)
        
        Args:
            foam_density: плотность квантовой пены (ρ/ρ_P)
            temperature: температура CMB (K)
        Returns:
            dict с параметрами искажения
        """
        print(f"\nComputing CMB spectral distortion...")
        
        # Параметры
        k_B = 1.381e-23  # J/K
        h = 6.626e-34    # J·s
        
        # Энергия, инжектированная квантовой пеной
        # ΔE/E ~ (ρ_foam / ρ_P) × (T_P / T_CMB)
        T_planck = 1.417e32  # K
        energy_injection = foam_density * (T_planck / temperature)
        
        # μ-параметр (химический потенциал)
        mu_distortion = 1.4e-8 * energy_injection
        
        # y-параметр (компонизация)
        y_distortion = 1e-9 * energy_injection
        
        print(f"  Temperature: T = {temperature} K")
        print(f"  Foam density: ρ/ρ_P = {foam_density:.6e}")
        print(f"  μ-distortion: μ = {mu_distortion:.6e}")
        print(f"  y-distortion: y = {y_distortion:.6e}")
        
        # Проверка наблюдаемости
        # Текущие пределы: |μ| < 9×10⁻⁵, |y| < 1.5×10⁻⁵
        mu_limit = 9e-5
        y_limit = 1.5e-5
        
        observable_mu = abs(mu_distortion) > mu_limit
        observable_y = abs(y_distortion) > y_limit
        
        print(f"  Observable (μ): {observable_mu} (limit: {mu_limit})")
        print(f"  Observable (y): {observable_y} (limit: {y_limit})")
        
        return {
            'mu_distortion': mu_distortion,
            'y_distortion': y_distortion,
            'observable_mu': observable_mu,
            'observable_y': observable_y,
            'energy_injection': energy_injection
        }
    
    def compute_interferometer_signal(self,
                                     arm_length: float,
                                     laser_wavelength: float,
                                     foam_density: float) -> Dict:
        """
        Вычислить сигнал на интерферометре (LIGO/Virgo/LISA).
        
        Квантовая пена создает эффективную "шумовую" метрику:
        δg_μν ~ (l_P / L)^α
        
        Это приводит к фазовому сдвигу:
        Δφ ~ (L / λ) × (l_P / L)^α
        
        Args:
            arm_length: длина плеча интерферометра (m)
            laser_wavelength: длина волны лазера (m)
            foam_density: плотность квантовой пены
        Returns:
            dict с параметрами сигнала
        """
        print(f"\nComputing interferometer signal...")
        
        # Планковская длина
        l_P = 1.616e-35  # m
        
        # Параметры
        alpha = 1.0  # степень подавления
        
        # Фазовый сдвиг
        phase_shift = (arm_length / laser_wavelength) * (l_P / arm_length) ** alpha * foam_density
        
        # Относительное изменение длины плеча
        delta_L_over_L = (l_P / arm_length) ** alpha * foam_density
        
        # Амплитуда деформации
        strain = delta_L_over_L
        
        print(f"  Arm length: L = {arm_length} m")
        print(f"  Wavelength: λ = {laser_wavelength} m")
        print(f"  Phase shift: Δφ = {phase_shift:.6e} rad")
        print(f"  Strain: h = {strain:.6e}")
        
        # Проверка наблюдаемости
        # LIGO sensitivity: h ~ 10⁻²³
        # LISA sensitivity: h ~ 10⁻²¹
        ligo_sensitivity = 1e-23
        lisa_sensitivity = 1e-21
        
        observable_ligo = abs(strain) > ligo_sensitivity
        observable_lisa = abs(strain) > lisa_sensitivity
        
        print(f"  Observable (LIGO): {observable_ligo} (sensitivity: {ligo_sensitivity})")
        print(f"  Observable (LISA): {observable_lisa} (sensitivity: {lisa_sensitivity})")
        
        return {
            'phase_shift': phase_shift,
            'strain': strain,
            'observable_ligo': observable_ligo,
            'observable_lisa': observable_lisa,
            'arm_length': arm_length,
            'wavelength': laser_wavelength
        }
    
    def generate_observational_report(self,
                                     foam_density: float = 0.1,
                                     save_path: str = "observational_signatures.txt") -> Dict:
        """
        Сгенерировать полный отчет о наблюдаемых эффектах.
        
        Args:
            foam_density: плотность квантовой пены (ρ/ρ_P)
            save_path: путь для сохранения отчета
        Returns:
            dict со всеми результатами
        """
        print("\n" + "="*70)
        print("GENERATING OBSERVATIONAL SIGNATURES REPORT")
        print("="*70)
        
        results = {}
        
        # 1. GW дисперсия (LIGO частоты)
        gw_ligo = self.compute_gw_dispersion(
            frequency=100.0,  # Hz
            distance=100.0,   # Mpc
            foam_density=foam_density
        )
        results['gw_ligo'] = gw_ligo
        
        # 2. GW дисперсия (LISA частоты)
        gw_lisa = self.compute_gw_dispersion(
            frequency=1e-3,   # Hz
            distance=1000.0,  # Mpc
            foam_density=foam_density
        )
        results['gw_lisa'] = gw_lisa
        
        # 3. CMB искажения
        cmb = self.compute_cmb_spectral_distortion(foam_density=foam_density)
        results['cmb'] = cmb
        
        # 4. LIGO интерферометр
        ligo = self.compute_interferometer_signal(
            arm_length=4000.0,      # m
            laser_wavelength=1064e-9,  # m (Nd:YAG)
            foam_density=foam_density
        )
        results['ligo'] = ligo
        
        # 5. LISA интерферометр
        lisa = self.compute_interferometer_signal(
            arm_length=2.5e9,       # m
            laser_wavelength=1064e-9,  # m
            foam_density=foam_density
        )
        results['lisa'] = lisa
        
        # Сохранить отчет
        with open(save_path, 'w') as f:
            f.write("="*70 + "\n")
            f.write("OBSERVATIONAL SIGNATURES OF QUANTUM FOAM\n")
            f.write("="*70 + "\n\n")
            f.write(f"Foam density: ρ/ρ_P = {foam_density:.6e}\n\n")
            
            f.write("1. GRAVITATIONAL WAVE DISPERSION\n")
            f.write("-" * 70 + "\n")
            f.write(f"LIGO band (100 Hz, 100 Mpc):\n")
            f.write(f"  Time delay: Δt = {gw_ligo['time_delay']:.6e} s\n")
            f.write(f"  Relative delay: {gw_ligo['time_delay'] / (100 * 3.086e22 / 3e8):.6e}\n\n")
            f.write(f"LISA band (1 mHz, 1000 Mpc):\n")
            f.write(f"  Time delay: Δt = {gw_lisa['time_delay']:.6e} s\n")
            f.write(f"  Relative delay: {gw_lisa['time_delay'] / (1000 * 3.086e22 / 3e8):.6e}\n\n")
            
            f.write("2. CMB SPECTRAL DISTORTIONS\n")
            f.write("-" * 70 + "\n")
            f.write(f"μ-distortion: {cmb['mu_distortion']:.6e}\n")
            f.write(f"y-distortion: {cmb['y_distortion']:.6e}\n")
            f.write(f"Observable: μ={cmb['observable_mu']}, y={cmb['observable_y']}\n\n")
            
            f.write("3. INTERFEROMETER SIGNALS\n")
            f.write("-" * 70 + "\n")
            f.write(f"LIGO strain: h = {ligo['strain']:.6e}\n")
            f.write(f"LIGO observable: {ligo['observable_ligo']}\n\n")
            f.write(f"LISA strain: h = {lisa['strain']:.6e}\n")
            f.write(f"LISA observable: {lisa['observable_lisa']}\n\n")
            
            f.write("="*70 + "\n")
            f.write("CONCLUSION\n")
            f.write("="*70 + "\n")
            f.write("These predictions can be tested with:\n")
            f.write("- Next-generation gravitational wave detectors\n")
            f.write("- CMB spectral missions (PIXIE, PRISM)\n")
            f.write("- Advanced interferometers (Einstein Telescope, Cosmic Explorer)\n")
        
        print(f"\n[OK] Report saved to {save_path}")
        
        return results


def demonstrate_observational_signatures():
    """
    Демонстрация вычисления наблюдаемых эффектов.
    """
    # Создать детектор
    detector_pos = torch.tensor([0.0, 0.0, 0.0, 0.0])
    detector = VirtualDetector(
        detector_position=detector_pos,
        detector_size=1.0
    )
    
    # Сгенерировать отчет
    results = detector.generate_observational_report(foam_density=0.1)
    
    print("\n[OK] Observational signatures computed!")
    
    return results


if __name__ == "__main__":
    demonstrate_observational_signatures()
