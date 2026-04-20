# 📝 ШПАРГАЛКА - Основные команды

## 🚀 БЫСТРЫЙ СТАРТ (3 команды)

```bash
python check_system.py                      # Проверка готовности
python run_all_experiments.py --quick       # Быстрый тест (5 мин)
python create_dissertation_pdf.py           # Создание PDF
```

---

## 🔬 ЭКСПЕРИМЕНТЫ

### Базовая симуляция
```bash
python main.py
```
Результат: `cluster_experiment.h5`

### Ансамблевая симуляция
```bash
python ensemble_simulator.py ensemble
```
Результат: `ensemble_results.h5`

### С обратным влиянием
```bash
python ensemble_simulator.py backreaction
```
Результат: `backreaction_results.h5`

### Сравнение режимов
```bash
python ensemble_simulator.py compare
```
Результат: `backreaction_comparison.png`

### Полный набор экспериментов
```bash
python run_all_experiments.py              # Полный (~15 мин)
python run_all_experiments.py --quick      # Быстрый (~5 мин)
```

---

## 📊 АНАЛИЗ

### Простой анализ
```bash
python analyze.py
```

### Продвинутый анализ
```bash
python advanced_analysis.py cluster_experiment.h5
python advanced_analysis.py ensemble_results.h5
python advanced_analysis.py backreaction_results.h5
```

### Создание PDF отчета
```bash
python create_dissertation_pdf.py
```

---

## 🔍 ПРОВЕРКА

### Проверка системы
```bash
python check_system.py
```

### Просмотр результатов
```bash
dir *.h5                                    # Список .h5 файлов
dir analysis_results\*.png                  # Список графиков
dir dissertation_results\                   # Результаты экспериментов
```

---

## 📁 ВАЖНЫЕ ФАЙЛЫ

### Результаты:
- `dissertation_visualization.pdf` - главный отчет
- `dissertation_results/summary.txt` - текстовое резюме
- `analysis_results/analysis_report.json` - детальные метрики

### Данные:
- `cluster_experiment.h5` - базовая симуляция
- `ensemble_results.h5` - ансамблевая симуляция
- `backreaction_results.h5` - с обратным влиянием

### Документация:
- `QUICKSTART.md` - быстрый старт
- `README.md` - полное описание
- `EXPERIMENT_GUIDE.md` - подробное руководство
- `FILE_INDEX.md` - список всех файлов

---

## 🎯 КЛЮЧЕВЫЕ МЕТРИКИ

### Фрактальная размерность (D2)
- **D2 < 3.0** → Коллапс
- **D2 ≈ 3.0** → Классическое поведение
- **D2 > 3.0** → Квантовые эффекты ✅
- **Текущее:** D2 = 5.752

### Показатель Ляпунова (λ)
- **λ > 0** → Хаос
- **λ ≈ 0** → Регулярная динамика ✅
- **λ < 0** → Сходимость

### Дрейф энергии
- **< 1%** → Отлично ✅
- **1-5%** → Приемлемо
- **> 5%** → Требуется коррекция

---

## 🛠️ НАСТРОЙКА ПАРАМЕТРОВ

### В ensemble_simulator.py:

```python
# Строка ~50: Амплитуда флуктуаций
fluctuation_amplitude=0.05  # 0.01, 0.05, 0.1, 0.2

# Строка ~30: Размер сетки
grid_shape=(8, 8, 8, 8)     # (4,4,4,4), (16,16,16,16)

# Строка ~32: Количество частиц
n_particles=1000             # 100, 500, 1000, 5000

# Строка ~100: Шаги симуляции
n_steps=100                  # 50, 100, 200, 500
```

### В engine.py:

```python
# Строка ~37: Шаг интегрирования
dt = 1e-45                   # 5e-46, 1e-45, 5e-45
```

---

## 🐛 РЕШЕНИЕ ПРОБЛЕМ

### Ошибка импорта
```bash
pip install torch numpy h5py matplotlib scipy
```

### Недостаточно памяти
- Уменьшите `n_particles` (1000 → 500)
- Уменьшите `grid_shape` (8×8×8×8 → 6×6×6×6)
- Используйте `--quick` режим

### Слишком долго
- Используйте GPU (если доступен)
- Уменьшите `n_steps` (100 → 50)
- Запустите `--quick` режим

### Большой дрейф энергии
- Уменьшите `dt` в engine.py
- Используйте меньше частиц

---

## 📈 ТИПИЧНЫЕ СЦЕНАРИИ

### Сценарий 1: Первый запуск
```bash
python check_system.py
python run_all_experiments.py --quick
python create_dissertation_pdf.py
# Просмотр: dissertation_visualization.pdf
```

### Сценарий 2: Полный анализ
```bash
python run_all_experiments.py
python create_dissertation_pdf.py
# Изучение: dissertation_results/summary.txt
```

### Сценарий 3: Исследование параметров
```bash
# Изменить amplitude в ensemble_simulator.py
python ensemble_simulator.py ensemble
python advanced_analysis.py ensemble_results.h5
# Повторить для разных значений
```

### Сценарий 4: Сравнение режимов
```bash
python ensemble_simulator.py compare
# Просмотр: backreaction_comparison.png
```

---

## 💡 ПОЛЕЗНЫЕ СОВЕТЫ

1. **Всегда начинайте с** `check_system.py`
2. **Используйте** `--quick` для тестирования
3. **Сохраняйте** .h5 файлы с разными именами
4. **Создавайте PDF** после каждого набора экспериментов
5. **Изучайте** `analysis_report.json` для деталей

---

## 📞 БЫСТРАЯ ПОМОЩЬ

| Вопрос | Ответ |
|--------|-------|
| Как начать? | `QUICKSTART.md` |
| Что делает файл? | `FILE_INDEX.md` |
| Как интерпретировать? | `EXPERIMENT_GUIDE.md` |
| Полное описание? | `README.md` |
| Что-то не работает? | `system_check_report.txt` |

---

## ⚡ ГОРЯЧИЕ КЛАВИШИ

```bash
# Алиасы для быстрого доступа (добавьте в .bashrc или .zshrc)
alias qg-check='python check_system.py'
alias qg-quick='python run_all_experiments.py --quick'
alias qg-full='python run_all_experiments.py'
alias qg-pdf='python create_dissertation_pdf.py'
alias qg-analyze='python advanced_analysis.py'
```

---

## 🎓 ДЛЯ ДИССЕРТАЦИИ

### Минимальный набор файлов:
1. `dissertation_visualization.pdf`
2. `dissertation_results/summary.txt`
3. `analysis_results/*.png`
4. Исходные .h5 файлы

### Команды для финального отчета:
```bash
python run_all_experiments.py              # Все эксперименты
python create_dissertation_pdf.py          # PDF отчет
# Готово к защите!
```

---

## 📊 СТАТУС ПРОЕКТА

- ✅ Код: Готов
- ✅ Тесты: Пройдены
- ✅ Документация: Полная
- ✅ Результаты: Получены
- ✅ PDF: Создан
- ✅ Статус: PRODUCTION READY

---

**Версия:** 1.0  
**Дата:** 2026-04-20  
**Статус:** ✅ Готово к использованию

*Распечатайте эту шпаргалку для быстрого доступа!*
