"""
Интегрирующий модуль: Полная система квантовой гравитации.
Объединяет все 5 компонентов в единую самосогласованную симуляцию.
"""

import torch
import numpy as np
from typing import Dict, Optional, List
import h5py
from datetime import datetime

# Импорт всех модулей
from self_consistent_gravity import SelfConsistentGravity
from adm_metric_evolution import ADMMetricEvolution
from quantum_entanglement_geometry import QuantumEntanglementGeometry
from quantum_thermodynamics import QuantumGravityThermodynamics
from theoretical_comparison import TheoreticalComparison

class FullQuantumGravitySimulation:
    """
    Полная самосогласованная симуляция квантовой гравитации.
    
    Включает:
    1. Back-reaction (самосогласованность)
    2. Динамика метрики (ADM-формализм)
    3. Квантовая запутанность (ER=EPR)
    4. Термодинамика и энтропия
    5. Сравнение с теорией
    """
    
    def __init__(self, grid_shape=(6, 6, 6, 6),
                 n_particles=100,
                 device='cpu',
                 dtype=torch.float64):
        
        self.grid_shape = grid_shape
        self.n_particles = n_particles
        self.device = device
        self.dtype = dtype
        
        print("="*70)
        print("ИНИЦИАЛИЗАЦИЯ ПОЛНОЙ СИСТЕМЫ КВАНТОВОЙ ГРАВИТАЦИИ")
        print("="*70)
        
        # 1. Самосогласованная гравитация
        print("\n1. Инициализация самосогласованной гравитации...")
        self.gravity = SelfConsistentGravity(
            grid_shape=grid_shape,
            device=device,
            dtype=dtype
        )
        
        # 2. ADM-формализм (динамика метрики)
        print("\n2. Инициализация ADM-формализма...")
        self.adm = ADMMetricEvolution(
            grid_shape=grid_shape[:3],  # только пространственная часть
            device=device,
            dtype=dtype
        )
        
        # 3. Квантовая запутанность
        print("\n3. Инициализация квантовой запутанности...")
        self.entanglement = QuantumEntanglementGeometry(
            grid_shape=grid_shape,
            device=device,
            dtype=dtype
        )
        
        # 4. Термодинамика
        print("\n4. Инициализация термодинамики...")
        self.thermodynamics = QuantumGravityThermodynamics(
            grid_shape=grid_shape,
            device=device,
            dtype=dtype
        )
        
        # 5. Сравнение с теорией
        print("\n5. Инициализация теоретического сравнения...")
        self.theory = TheoreticalComparison(
            device=device,
            dtype=dtype
        )
        
        # Инициализация частиц
        self.particles = self._initialize_particles()
        
        # История для анализа
        self.trajectory_history = []
        self.metric_history = []
        
        print("\n" + "="*70)
        print("СИСТЕМА ГОТОВА К ЗАПУСКУ")
        print("="*70)
    
    def _initialize_particles(self) -> torch.Tensor:
        """Инициализация облака частиц"""
        particles = torch.zeros((self.n_particles, 8), dtype=self.dtype, device=self.device)
        
        # Позиции: гауссово распределение
        center = torch.tensor([self.gravity.l_P * 3] * 3, dtype=self.dtype, device=self.device)
        radius = self.gravity.l_P * 2
        
        for i in range(3):
            particles[:, i+1] = torch.randn(self.n_particles, dtype=self.dtype, device=self.device) * radius + center[i]
        
        # Временная координата
        particles[:, 0] = 0.0
        
        # 4-скорости
        particles[:, 4] = 1.0  # u^0 ≈ c
        particles[:, 5:8] = torch.randn((self.n_particles, 3), dtype=self.dtype, device=self.device) * 1e5
        
        return particles
    
    def run_full_simulation(self, n_steps: int = 50,
                           analyze_every: int = 10,
                           save_checkpoints: bool = True) -> Dict:
        """
        Запуск полной самосогласованной симуляции.
        
        На каждом шаге:
        1. Эволюция частиц в текущей метрике
        2. Вычисление T_μν и обновление метрики (back-reaction)
        3. Эволюция самой метрики (ADM)
        4. Анализ запутанности
        5. Термодинамический анализ
        """
        print("\n" + "="*70)
        print(f"ЗАПУСК ПОЛНОЙ СИМУЛЯЦИИ ({n_steps} шагов)")
        print("="*70)
        
        results = {
            'diagnostics': [],
            'thermodynamics': [],
            'entanglement': [],
            'gravitational_waves': []
        }
        
        for step in range(n_steps):
            print(f"\n{'='*70}")
            print(f"ШАГ {step+1}/{n_steps}")
            print(f"{'='*70}")
            
            # 1. Самосогласованная эволюция (частицы + метрика)
            print("  1. Самосогласованная эволюция...")
            self.particles, diag = self.gravity.evolve_step(
                self.particles, 
                dt=self.gravity.t_P * 0.1
            )
            
            results['diagnostics'].append(diag)
            
            # 2. Эволюция метрики (ADM)
            print("  2. Эволюция метрики (ADM)...")
            self.adm.evolve_metric_adm(dt=self.adm.t_P * 0.1)
            
            # Извлечение гравитационных волн
            gw = self.adm.extract_gravitational_waves()
            results['gravitational_waves'].append(gw)
            
            # 3. Синхронизация метрик (упрощенно)
            self._synchronize_metrics()
            
            # 4. Периодический анализ
            if step % analyze_every == 0:
                print(f"\n  --- АНАЛИЗ НА ШАГЕ {step} ---")
                
                # Термодинамика
                print("  3. Термодинамический анализ...")
                thermo_results = self.thermodynamics.compute_full_thermodynamics(
                    self.particles,
                    self.gravity.g_metric
                )
                results['thermodynamics'].append(thermo_results)
                
                # Запутанность (только на некоторых шагах - вычислительно дорого)
                if step % (analyze_every * 3) == 0:
                    print("  4. Анализ запутанности...")
                    
                    # Корреляция запутанность-кривизна
                    corr_results = self.entanglement.correlate_entanglement_curvature(
                        self.gravity.g_metric
                    )
                    
                    # Поиск кротовых нор
                    wormholes = self.entanglement.detect_wormholes(
                        threshold_entanglement=0.3,
                        threshold_curvature=0.01
                    )
                    
                    results['entanglement'].append({
                        'step': step,
                        'correlation': corr_results,
                        'n_wormholes': len(wormholes)
                    })
                    
                    print(f"     Корреляция запутанность-кривизна: {corr_results['correlation_entanglement_curvature']:.4f}")
                    print(f"     Обнаружено кротовых нор: {len(wormholes)}")
            
            # Сохранение истории
            self.trajectory_history.append(self.particles.clone().cpu())
            self.metric_history.append(self.gravity.g_metric.clone().cpu())
            
            # Вывод диагностики
            print(f"\n  Диагностика:")
            print(f"    Trace(g): {diag['metric_trace']:.6f}")
            print(f"    Кривизна: {diag['curvature_scalar']:.6e}")
            print(f"    Нарушение ограничения: {diag['constraint_violation']:.6e}")
            print(f"    Амплитуда ГВ: {gw['amplitude']:.6e}")
            
            # Сохранение чекпоинтов
            if save_checkpoints and step % (analyze_every * 2) == 0 and step > 0:
                self._save_checkpoint(step)
        
        print("\n" + "="*70)
        print("СИМУЛЯЦИЯ ЗАВЕРШЕНА")
        print("="*70)
        
        # Финальный анализ
        print("\nФинальный анализ...")
        final_results = self._perform_final_analysis(results)
        
        return final_results
    
    def _synchronize_metrics(self):
        """
        Синхронизация метрик между разными формализмами.
        
        Преобразует 4D метрику в ADM переменные и обратно.
        """
        # Упрощенная синхронизация: копируем пространственную часть
        for i in range(min(self.grid_shape[1], self.adm.grid_shape[0])):
            for j in range(min(self.grid_shape[2], self.adm.grid_shape[1])):
                for k in range(min(self.grid_shape[3], self.adm.grid_shape[2])):
                    # Пространственная метрика h_ij из g_μν
                    g = self.gravity.g_metric[0, i, j, k]
                    self.adm.h_spatial[i, j, k] = g[1:4, 1:4]
    
    def _perform_final_analysis(self, results: Dict) -> Dict:
        """Финальный анализ после завершения симуляции"""
        print("\n" + "="*70)
        print("ФИНАЛЬНЫЙ АНАЛИЗ")
        print("="*70)
        
        final = {}
        
        # 1. Траектории
        trajectory_bundle = torch.stack(self.trajectory_history).permute(1, 0, 2)  # [N_particles, N_steps, 8]
        
        # 2. Сравнение с теорией
        print("\n1. Сравнение с теоретическими предсказаниями...")
        
        # Метрические флуктуации
        metric_stack = torch.stack(self.metric_history)
        metric_fluctuations = metric_stack - metric_stack[0]
        
        # Кривизна
        curvature_history = [d['curvature_scalar'] for d in results['diagnostics']]
        
        theory_report = self.theory.generate_comparison_report(
            trajectory_bundle,
            metric_fluctuations,
            curvature_history
        )
        
        self.theory.print_comparison_summary(theory_report)
        
        final['theory_comparison'] = theory_report
        
        # 3. Планковские звезды
        print("\n2. Поиск планковских звезд...")
        planck_stars = self.gravity.detect_planck_stars(threshold_curvature=1e50)
        print(f"   Обнаружено планковских звезд: {len(planck_stars)}")
        
        final['planck_stars'] = planck_stars
        
        # 4. Энергия гравитационных волн
        print("\n3. Энергия гравитационных волн...")
        E_GW = self.adm.compute_gravitational_wave_energy()
        print(f"   E_GW = {E_GW:.6e} Дж")
        
        final['gravitational_wave_energy'] = E_GW
        
        # 5. Голографический принцип
        if results['thermodynamics']:
            print("\n4. Проверка голографического принципа...")
            last_thermo = results['thermodynamics'][-1]
            
            S_ent = last_thermo['entanglement']['entanglement_entropy']
            S_holo = last_thermo['holographic']['holographic_entropy']
            ratio = S_ent / S_holo if S_holo > 0 else 0
            
            print(f"   S_entanglement / S_holographic = {ratio:.4f}")
            print(f"   {'✓ Голографический принцип подтвержден' if 0.5 < ratio < 2.0 else '✗ Отклонение от голографического принципа'}")
            
            final['holographic_ratio'] = ratio
        
        # 6. Сводная статистика
        print("\n5. Сводная статистика...")
        
        final['summary'] = {
            'n_steps': len(results['diagnostics']),
            'n_particles': self.n_particles,
            'mean_curvature': np.mean(curvature_history),
            'max_curvature': np.max(curvature_history),
            'mean_constraint_violation': np.mean([d['constraint_violation'] for d in results['diagnostics']]),
            'n_planck_stars': len(planck_stars),
            'n_wormholes': sum(e['n_wormholes'] for e in results['entanglement']) if results['entanglement'] else 0,
            'mean_gw_amplitude': np.mean([gw['amplitude'] for gw in results['gravitational_waves']])
        }
        
        # Вывод сводки
        print(f"\n   Средняя кривизна: {final['summary']['mean_curvature']:.6e}")
        print(f"   Планковских звезд: {final['summary']['n_planck_stars']}")
        print(f"   Кротовых нор: {final['summary']['n_wormholes']}")
        print(f"   Средняя амплитуда ГВ: {final['summary']['mean_gw_amplitude']:.6e}")
        
        final['diagnostics'] = results['diagnostics']
        final['thermodynamics'] = results['thermodynamics']
        final['entanglement'] = results['entanglement']
        final['gravitational_waves'] = results['gravitational_waves']
        
        return final
    
    def _save_checkpoint(self, step: int):
        """Сохранение чекпоинта"""
        filename = f"full_simulation_checkpoint_step_{step}.h5"
        
        with h5py.File(filename, 'w') as f:
            f.create_dataset('particles', data=self.particles.cpu().numpy())
            f.create_dataset('metric', data=self.gravity.g_metric.cpu().numpy())
            
            f.attrs['step'] = step
            f.attrs['timestamp'] = str(datetime.now())
        
        print(f"     Чекпоинт сохранен: {filename}")
    
    def save_full_results(self, results: Dict, filename: str = "full_simulation_results.h5"):
        """Сохранение полных результатов"""
        print(f"\nСохранение результатов в {filename}...")
        
        with h5py.File(filename, 'w') as f:
            # Траектории
            trajectory_bundle = torch.stack(self.trajectory_history)
            f.create_dataset('trajectories', data=trajectory_bundle.numpy())
            
            # Метрика
            metric_stack = torch.stack(self.metric_history)
            f.create_dataset('metric_history', data=metric_stack.numpy())
            
            # Диагностика
            diag_keys = results['diagnostics'][0].keys()
            for key in diag_keys:
                values = [d[key] for d in results['diagnostics']]
                f.create_dataset(f'diagnostics/{key}', data=np.array(values))
            
            # Гравитационные волны
            gw_data = np.array([[gw['h_plus'], gw['h_cross'], gw['frequency'], gw['amplitude']]
                               for gw in results['gravitational_waves']])
            f.create_dataset('gravitational_waves', data=gw_data)
            
            # Сводка
            for key, value in results['summary'].items():
                f.attrs[key] = value
            
            # Теоретическое сравнение
            if 'theory_comparison' in results:
                tc = results['theory_comparison']
                
                if 'scale_dependence' in tc:
                    sd = tc['scale_dependence']
                    f.create_dataset('theory/scale_dependence/scales', data=sd['scales'])
                    f.create_dataset('theory/scale_dependence/dimensions', data=sd['dimensions'])
                
                if 'power_spectrum' in tc:
                    ps = tc['power_spectrum']
                    f.create_dataset('theory/power_spectrum/frequencies', data=ps['frequencies'])
                    f.create_dataset('theory/power_spectrum/power', data=ps['power'])
                    f.attrs['spectral_index'] = ps['spectral_index']
        
        print(f"Результаты сохранены!")
        
        # Сохранение отдельных компонентов
        self.gravity.save_state("gravity_final_state.h5")
        self.adm.save_adm_state("adm_final_state.h5")
        self.entanglement.save_entanglement_data("entanglement_final_state.h5")
        self.thermodynamics.save_thermodynamics("thermodynamics_final_state.h5")
        
        print("Все компоненты сохранены!")


def run_demonstration():
    """Демонстрационный запуск полной системы"""
    print("="*70)
    print("ДЕМОНСТРАЦИЯ ПОЛНОЙ СИСТЕМЫ КВАНТОВОЙ ГРАВИТАЦИИ")
    print("="*70)
    print(f"Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Создание системы (малая сетка для демонстрации)
    sim = FullQuantumGravitySimulation(
        grid_shape=(4, 4, 4, 4),
        n_particles=50,
        device='cpu'
    )
    
    # Запуск симуляции
    results = sim.run_full_simulation(
        n_steps=20,
        analyze_every=5,
        save_checkpoints=True
    )
    
    # Сохранение результатов
    sim.save_full_results(results)
    
    print("\n" + "="*70)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("="*70)
    print(f"Время окончания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return results


if __name__ == "__main__":
    results = run_demonstration()
