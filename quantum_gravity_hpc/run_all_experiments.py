"""
Полный набор экспериментов для докторской диссертации.
Запускает все симуляции и генерирует комплексный отчет.
"""

import os
import sys
import time
import json
from datetime import datetime
import subprocess

class DissertationExperimentSuite:
    """
    Автоматизированный набор экспериментов для диссертации.
    """
    
    def __init__(self, output_dir="dissertation_results"):
        self.output_dir = output_dir
        self.results = {}
        self.start_time = None
        
        # Создаем директорию для результатов
        os.makedirs(output_dir, exist_ok=True)
        
        print("="*70)
        print("ПОЛНЫЙ НАБОР ЭКСПЕРИМЕНТОВ ДЛЯ ДОКТОРСКОЙ ДИССЕРТАЦИИ")
        print("="*70)
        print(f"Директория результатов: {output_dir}")
        print(f"Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
    
    def run_experiment(self, name, command, description):
        """Запуск одного эксперимента"""
        print(f"\n{'='*70}")
        print(f"ЭКСПЕРИМЕНТ: {name}")
        print(f"Описание: {description}")
        print(f"{'='*70}")
        
        start = time.time()
        
        try:
            # Запуск команды
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            elapsed = time.time() - start
            
            # Сохранение результатов
            self.results[name] = {
                'description': description,
                'command': command,
                'elapsed_time': elapsed,
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            if result.returncode == 0:
                print(f"\n[OK] Эксперимент завершен успешно за {elapsed:.2f} сек")
            else:
                print(f"\n[ОШИБКА] Эксперимент завершился с ошибкой")
                print(f"Код возврата: {result.returncode}")
                if result.stderr:
                    print(f"Ошибка: {result.stderr[:500]}")
            
            return result.returncode == 0
            
        except Exception as e:
            elapsed = time.time() - start
            print(f"\n[ИСКЛЮЧЕНИЕ] Ошибка при выполнении: {e}")
            
            self.results[name] = {
                'description': description,
                'command': command,
                'elapsed_time': elapsed,
                'success': False,
                'error': str(e)
            }
            
            return False
    
    def experiment_1_baseline(self):
        """Эксперимент 1: Базовая симуляция (контроль)"""
        return self.run_experiment(
            name="1_baseline",
            command=f"{sys.executable} main.py",
            description="Базовая симуляция 100 частиц на 5 шагов (контрольная группа)"
        )
    
    def experiment_2_ensemble_small(self):
        """Эксперимент 2: Малый ансамбль"""
        return self.run_experiment(
            name="2_ensemble_small",
            command=f"{sys.executable} ensemble_simulator.py ensemble",
            description="Ансамбль 1000 частиц на 100 шагов (квантовая диффузия)"
        )
    
    def experiment_3_backreaction(self):
        """Эксперимент 3: С обратным влиянием"""
        return self.run_experiment(
            name="3_backreaction",
            command=f"{sys.executable} ensemble_simulator.py backreaction",
            description="500 частиц с обратным влиянием на метрику"
        )
    
    def experiment_4_comparison(self):
        """Эксперимент 4: Сравнительный анализ"""
        return self.run_experiment(
            name="4_comparison",
            command=f"{sys.executable} ensemble_simulator.py compare",
            description="Сравнение режимов с/без обратного влияния"
        )
    
    def analyze_all_results(self):
        """Анализ всех результатов"""
        print(f"\n{'='*70}")
        print("АНАЛИЗ ВСЕХ РЕЗУЛЬТАТОВ")
        print(f"{'='*70}")
        
        h5_files = [
            "cluster_experiment.h5",
            "ensemble_results.h5",
            "backreaction_results.h5",
            "no_backreaction.h5",
            "with_backreaction.h5"
        ]
        
        analysis_results = {}
        
        for h5_file in h5_files:
            if os.path.exists(h5_file):
                print(f"\nАнализ {h5_file}...")
                
                success = self.run_experiment(
                    name=f"analysis_{h5_file.replace('.h5', '')}",
                    command=f"{sys.executable} advanced_analysis.py {h5_file}",
                    description=f"Продвинутый анализ {h5_file}"
                )
                
                # Читаем JSON отчет если есть
                json_path = f"analysis_results/analysis_report.json"
                if os.path.exists(json_path):
                    try:
                        with open(json_path, 'r') as f:
                            report = json.load(f)
                            analysis_results[h5_file] = report
                    except Exception as e:
                        print(f"Ошибка чтения {json_path}: {e}")
        
        return analysis_results
    
    def generate_summary_report(self, analysis_results):
        """Генерация итогового отчета"""
        print(f"\n{'='*70}")
        print("ГЕНЕРАЦИЯ ИТОГОВОГО ОТЧЕТА")
        print(f"{'='*70}")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_experiments': len(self.results),
            'successful_experiments': sum(1 for r in self.results.values() if r['success']),
            'total_time': sum(r['elapsed_time'] for r in self.results.values()),
            'experiments': self.results,
            'analysis_results': analysis_results
        }
        
        # Сохранение в JSON
        report_path = os.path.join(self.output_dir, 'full_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nJSON отчет сохранен: {report_path}")
        
        # Генерация текстового отчета
        txt_path = os.path.join(self.output_dir, 'summary.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("ИТОГОВЫЙ ОТЧЕТ ЭКСПЕРИМЕНТОВ\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Всего экспериментов: {report['total_experiments']}\n")
            f.write(f"Успешных: {report['successful_experiments']}\n")
            f.write(f"Общее время: {report['total_time']:.2f} сек ({report['total_time']/60:.2f} мин)\n\n")
            
            f.write("РЕЗУЛЬТАТЫ ПО ЭКСПЕРИМЕНТАМ:\n")
            f.write("-"*70 + "\n\n")
            
            for name, result in self.results.items():
                f.write(f"Эксперимент: {name}\n")
                f.write(f"  Описание: {result['description']}\n")
                f.write(f"  Статус: {'OK' if result['success'] else 'ОШИБКА'}\n")
                f.write(f"  Время: {result['elapsed_time']:.2f} сек\n")
                f.write("\n")
            
            # Ключевые метрики
            if analysis_results:
                f.write("\n" + "="*70 + "\n")
                f.write("КЛЮЧЕВЫЕ МЕТРИКИ ДЛЯ ДИССЕРТАЦИИ\n")
                f.write("="*70 + "\n\n")
                
                for h5_file, metrics in analysis_results.items():
                    f.write(f"\n{h5_file}:\n")
                    f.write("-"*70 + "\n")
                    
                    if 'fractal_dimension' in metrics:
                        f.write(f"  Фрактальная размерность D2: {metrics['fractal_dimension']:.4f}\n")
                    
                    if 'lyapunov_exponent' in metrics:
                        f.write(f"  Показатель Ляпунова: {metrics['lyapunov_exponent']:.6f}\n")
                    
                    if 'energy_drift_percent' in metrics:
                        f.write(f"  Дрейф энергии: {metrics['energy_drift_percent']:.4f}%\n")
                    
                    if 'radius_growth_rate' in metrics:
                        f.write(f"  Скорость роста радиуса: {metrics['radius_growth_rate']:.6f}\n")
                    
                    if 'velocity_dispersion_final' in metrics:
                        vd = metrics['velocity_dispersion_final']
                        f.write(f"  Финальная дисперсия скорости:\n")
                        f.write(f"    vx: {vd.get('vx', 0):.6e}\n")
                        f.write(f"    vy: {vd.get('vy', 0):.6e}\n")
                        f.write(f"    vz: {vd.get('vz', 0):.6e}\n")
        
        print(f"Текстовый отчет сохранен: {txt_path}")
        
        return report
    
    def print_final_summary(self, report):
        """Вывод финального резюме"""
        print(f"\n{'='*70}")
        print("ФИНАЛЬНОЕ РЕЗЮМЕ")
        print(f"{'='*70}")
        
        print(f"\nВсего экспериментов: {report['total_experiments']}")
        print(f"Успешных: {report['successful_experiments']}")
        print(f"Неудачных: {report['total_experiments'] - report['successful_experiments']}")
        print(f"Общее время: {report['total_time']:.2f} сек ({report['total_time']/60:.2f} мин)")
        
        print(f"\nРезультаты сохранены в: {self.output_dir}/")
        print("  - full_report.json - полный JSON отчет")
        print("  - summary.txt - текстовое резюме")
        print("  - analysis_results/ - графики и анализ")
        
        if report['analysis_results']:
            print("\nКлючевые находки:")
            
            # Находим максимальную фрактальную размерность
            max_d2 = 0
            max_d2_file = ""
            
            for h5_file, metrics in report['analysis_results'].items():
                if 'fractal_dimension' in metrics:
                    d2 = metrics['fractal_dimension']
                    if d2 > max_d2:
                        max_d2 = d2
                        max_d2_file = h5_file
            
            if max_d2 > 0:
                print(f"  - Максимальная фрактальная размерность: D2 = {max_d2:.4f}")
                print(f"    (в файле: {max_d2_file})")
                
                if max_d2 > 3.0:
                    print(f"    -> Обнаружены нелокальные квантовые эффекты!")
                    print(f"    -> Превышение над классическим значением: {(max_d2 - 3.0):.4f}")
        
        print(f"\n{'='*70}")
        print("ВСЕ ЭКСПЕРИМЕНТЫ ЗАВЕРШЕНЫ")
        print(f"{'='*70}\n")
    
    def run_all(self):
        """Запуск всех экспериментов"""
        self.start_time = time.time()
        
        # Последовательность экспериментов
        experiments = [
            self.experiment_1_baseline,
            self.experiment_2_ensemble_small,
            self.experiment_3_backreaction,
            self.experiment_4_comparison
        ]
        
        # Запуск экспериментов
        for i, experiment in enumerate(experiments, 1):
            print(f"\n\nПрогресс: {i}/{len(experiments)}")
            experiment()
            
            # Небольшая пауза между экспериментами
            time.sleep(1)
        
        # Анализ результатов
        analysis_results = self.analyze_all_results()
        
        # Генерация отчета
        report = self.generate_summary_report(analysis_results)
        
        # Финальное резюме
        self.print_final_summary(report)
        
        return report


def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Полный набор экспериментов для докторской диссертации'
    )
    parser.add_argument(
        '--output-dir',
        default='dissertation_results',
        help='Директория для результатов (по умолчанию: dissertation_results)'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Быстрый режим (только базовые эксперименты)'
    )
    
    args = parser.parse_args()
    
    # Создание и запуск набора экспериментов
    suite = DissertationExperimentSuite(output_dir=args.output_dir)
    
    if args.quick:
        print("\n[БЫСТРЫЙ РЕЖИМ] Запуск только базовых экспериментов\n")
        suite.experiment_1_baseline()
        analysis_results = suite.analyze_all_results()
        report = suite.generate_summary_report(analysis_results)
        suite.print_final_summary(report)
    else:
        report = suite.run_all()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
