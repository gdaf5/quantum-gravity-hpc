"""
Проверка готовности системы для запуска экспериментов диссертации.
Проверяет все зависимости, файлы и создает отчет о статусе.
"""

import sys
import os
import importlib
import subprocess
from datetime import datetime

class SystemReadinessChecker:
    """
    Проверка готовности системы к запуску экспериментов.
    """
    
    def __init__(self):
        self.checks = []
        self.warnings = []
        self.errors = []
        
    def check_python_version(self):
        """Проверка версии Python"""
        version = sys.version_info
        
        if version.major >= 3 and version.minor >= 8:
            self.checks.append(("Python версия", f"{version.major}.{version.minor}.{version.micro}", "OK"))
            return True
        else:
            self.errors.append(f"Python версия {version.major}.{version.minor} < 3.8 (требуется 3.8+)")
            self.checks.append(("Python версия", f"{version.major}.{version.minor}.{version.micro}", "ОШИБКА"))
            return False
    
    def check_dependencies(self):
        """Проверка установленных библиотек"""
        required = {
            'torch': 'PyTorch',
            'numpy': 'NumPy',
            'h5py': 'HDF5',
            'matplotlib': 'Matplotlib',
            'scipy': 'SciPy'
        }
        
        all_ok = True
        
        for module, name in required.items():
            try:
                mod = importlib.import_module(module)
                version = getattr(mod, '__version__', 'unknown')
                self.checks.append((name, version, "OK"))
            except ImportError:
                self.errors.append(f"{name} ({module}) не установлен")
                self.checks.append((name, "не установлен", "ОШИБКА"))
                all_ok = False
        
        return all_ok
    
    def check_torch_device(self):
        """Проверка доступности GPU"""
        try:
            import torch
            
            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(0)
                self.checks.append(("GPU (CUDA)", device_name, "OK"))
                self.warnings.append("GPU доступен - рекомендуется использовать для ускорения")
            else:
                self.checks.append(("GPU (CUDA)", "недоступен", "ПРЕДУПРЕЖДЕНИЕ"))
                self.warnings.append("GPU недоступен - симуляции будут выполняться на CPU (медленнее)")
            
            return True
        except:
            return False
    
    def check_required_files(self):
        """Проверка наличия необходимых файлов"""
        required_files = [
            'engine.py',
            'main.py',
            'logger.py',
            'analyze.py',
            'advanced_analysis.py',
            'ensemble_simulator.py',
            'run_all_experiments.py',
            'create_dissertation_pdf.py',
            'README.md',
            'EXPERIMENT_GUIDE.md'
        ]
        
        all_ok = True
        
        for file in required_files:
            if os.path.exists(file):
                size = os.path.getsize(file)
                self.checks.append((f"Файл: {file}", f"{size} байт", "OK"))
            else:
                self.errors.append(f"Отсутствует файл: {file}")
                self.checks.append((f"Файл: {file}", "отсутствует", "ОШИБКА"))
                all_ok = False
        
        return all_ok
    
    def check_disk_space(self):
        """Проверка свободного места на диске"""
        try:
            import shutil
            
            total, used, free = shutil.disk_usage(".")
            free_gb = free / (1024**3)
            
            if free_gb > 1.0:
                self.checks.append(("Свободное место", f"{free_gb:.2f} GB", "OK"))
                return True
            else:
                self.warnings.append(f"Мало свободного места: {free_gb:.2f} GB (рекомендуется > 1 GB)")
                self.checks.append(("Свободное место", f"{free_gb:.2f} GB", "ПРЕДУПРЕЖДЕНИЕ"))
                return True
        except:
            self.checks.append(("Свободное место", "не удалось проверить", "ПРЕДУПРЕЖДЕНИЕ"))
            return True
    
    def check_existing_results(self):
        """Проверка существующих результатов"""
        h5_files = [f for f in os.listdir('.') if f.endswith('.h5')]
        
        if h5_files:
            self.checks.append(("Существующие .h5 файлы", f"{len(h5_files)} найдено", "ИНФО"))
            self.warnings.append(f"Найдено {len(h5_files)} файлов результатов - они будут перезаписаны")
            
            for h5_file in h5_files:
                size = os.path.getsize(h5_file) / 1024
                self.checks.append((f"  -> {h5_file}", f"{size:.2f} KB", "ИНФО"))
        else:
            self.checks.append(("Существующие .h5 файлы", "не найдено", "ИНФО"))
        
        return True
    
    def estimate_runtime(self):
        """Оценка времени выполнения"""
        estimates = {
            'Быстрый тест (--quick)': '~5 минут',
            'Полный набор экспериментов': '~10-15 минут',
            'Расширенные эксперименты': '~30-60 минут'
        }
        
        for name, time in estimates.items():
            self.checks.append((f"Оценка: {name}", time, "ИНФО"))
        
        return True
    
    def run_all_checks(self):
        """Запуск всех проверок"""
        print("="*70)
        print("ПРОВЕРКА ГОТОВНОСТИ СИСТЕМЫ")
        print("="*70)
        print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Директория: {os.getcwd()}")
        print("="*70)
        print()
        
        checks_to_run = [
            ("Версия Python", self.check_python_version),
            ("Зависимости", self.check_dependencies),
            ("GPU/CUDA", self.check_torch_device),
            ("Файлы проекта", self.check_required_files),
            ("Дисковое пространство", self.check_disk_space),
            ("Существующие результаты", self.check_existing_results),
            ("Оценка времени", self.estimate_runtime)
        ]
        
        for name, check_func in checks_to_run:
            print(f"Проверка: {name}...", end=" ")
            try:
                result = check_func()
                print("[OK]" if result else "[FAIL]")
            except Exception as e:
                print(f"ОШИБКА: {e}")
                self.errors.append(f"Ошибка при проверке {name}: {e}")
        
        print()
        self.print_summary()
        
        return len(self.errors) == 0
    
    def print_summary(self):
        """Вывод итогового отчета"""
        print("="*70)
        print("РЕЗУЛЬТАТЫ ПРОВЕРКИ")
        print("="*70)
        print()
        
        # Таблица проверок
        print(f"{'Компонент':<40} {'Статус':<20} {'Результат':<10}")
        print("-"*70)
        
        for component, status, result in self.checks:
            # Цветовое кодирование (если терминал поддерживает)
            if result == "OK":
                result_str = "[OK]"
            elif result == "ОШИБКА":
                result_str = "[ОШИБКА]"
            elif result == "ПРЕДУПРЕЖДЕНИЕ":
                result_str = "[!]"
            else:
                result_str = "[i]"
            
            print(f"{component:<40} {status:<20} {result_str:<10}")
        
        print()
        print("="*70)
        
        # Ошибки
        if self.errors:
            print("ОШИБКИ:")
            print("-"*70)
            for error in self.errors:
                print(f"  [X] {error}")
            print()
        
        # Предупреждения
        if self.warnings:
            print("ПРЕДУПРЕЖДЕНИЯ:")
            print("-"*70)
            for warning in self.warnings:
                print(f"  [!] {warning}")
            print()
        
        # Итоговый статус
        print("="*70)
        if not self.errors:
            print("СТАТУС: ГОТОВО К ЗАПУСКУ [OK]")
            print()
            print("Рекомендуемые команды:")
            print("  1. Быстрый тест:")
            print("     python run_all_experiments.py --quick")
            print()
            print("  2. Полный набор экспериментов:")
            print("     python run_all_experiments.py")
            print()
            print("  3. Создание PDF отчета:")
            print("     python create_dissertation_pdf.py")
        else:
            print("СТАТУС: ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ ОШИБОК [FAIL]")
            print()
            print("Для установки зависимостей:")
            print("  pip install torch numpy h5py matplotlib scipy")
        
        print("="*70)
    
    def save_report(self, filename="system_check_report.txt"):
        """Сохранение отчета в файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("ОТЧЕТ О ПРОВЕРКЕ ГОТОВНОСТИ СИСТЕМЫ\n")
            f.write("="*70 + "\n")
            f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Директория: {os.getcwd()}\n")
            f.write(f"Python: {sys.version}\n")
            f.write("="*70 + "\n\n")
            
            f.write("РЕЗУЛЬТАТЫ ПРОВЕРОК:\n")
            f.write("-"*70 + "\n")
            for component, status, result in self.checks:
                f.write(f"{component:<40} {status:<20} {result:<10}\n")
            
            if self.errors:
                f.write("\n" + "="*70 + "\n")
                f.write("ОШИБКИ:\n")
                f.write("-"*70 + "\n")
                for error in self.errors:
                    f.write(f"  - {error}\n")
            
            if self.warnings:
                f.write("\n" + "="*70 + "\n")
                f.write("ПРЕДУПРЕЖДЕНИЯ:\n")
                f.write("-"*70 + "\n")
                for warning in self.warnings:
                    f.write(f"  - {warning}\n")
            
            f.write("\n" + "="*70 + "\n")
            if not self.errors:
                f.write("СТАТУС: ГОТОВО К ЗАПУСКУ\n")
            else:
                f.write("СТАТУС: ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ ОШИБОК\n")
            f.write("="*70 + "\n")
        
        print(f"\nОтчет сохранен: {filename}")


def main():
    """Главная функция"""
    checker = SystemReadinessChecker()
    
    success = checker.run_all_checks()
    
    # Сохранение отчета
    checker.save_report()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
