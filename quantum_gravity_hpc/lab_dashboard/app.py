import streamlit as st
import sys
import os
import io
import importlib
import contextlib

# Add parent directory to path to find scientific modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Quantum INC Lab", layout="wide")

st.title("🌌 Quantum INC Lab")
st.sidebar.header("Параметры эксперимента")

# 1. Динамический выбор метода
# Сопоставление имен модулей в корне проекта
methods = {
    "Quantum Foam Demo": "demo_quantum_foam",
    "It from Qubit": "it_from_qubit_advanced",
    "ML Einstein Solver": "ml_metric_predictor"
}
selected_method = st.sidebar.selectbox("Выберите метод:", list(methods.keys()))

# 2. Регулировка сетки
grid_size = st.sidebar.slider("Размер сетки (N^4)", 2, 12, 6)
foam_density = st.sidebar.slider("Плотность пены", 0.0, 1.0, 0.3)

# 3. Консоль
st.subheader("Системная консоль")
console_output = st.empty()

if st.sidebar.button("Запустить симуляцию"):
    output_buffer = io.StringIO()
    with contextlib.redirect_stdout(output_buffer):
        try:
            # Динамическая загрузка модуля из родительской папки
            module_name = methods[selected_method]
            mod = importlib.import_module(module_name)
            
            # Список потенциальных точек входа
            entry_points = [
                'run_all_demos', 'demonstrate_quantum_foam', 
                'run_all_tests', 'run', 'main', 'demonstrate'
            ]
            
            called = False
            for func_name in entry_points:
                if hasattr(mod, func_name):
                    getattr(mod, func_name)()
                    called = True
                    break
            
            if not called:
                print(f"Ошибка: В модуле {module_name} не найдена ни одна из точек входа: {entry_points}")

                
        except Exception as e:
            print(f"Ошибка выполнения: {e}")
            
    console_output.code(output_buffer.getvalue())

st.sidebar.markdown("---")
st.sidebar.info("Интерфейс работает в режиме 'sandbox'. Все файлы остаются на месте.")
