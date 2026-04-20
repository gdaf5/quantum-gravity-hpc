import h5py
import numpy as np
import matplotlib.pyplot as plt

def analyze_simulation(filename="cluster_experiment.h5"):
    print(f"Анализ данных из {filename}...")
    
    with h5py.File(filename, 'r') as f:
        dataset = f['particles']
        data = dataset[:] # [steps, particles, 8]
        
    # 1. Вычисляем радиус кластера для каждого шага
    # particles[:, 1:4] - это координаты x, y, z
    positions = data[:, :, 1:4]
    radii = np.linalg.norm(positions, axis=2)
    mean_radii = np.mean(radii, axis=1)
    
    # 2. Визуализация
    plt.figure(figsize=(10, 6))
    plt.plot(mean_radii)
    plt.title("Эволюция радиуса кластера")
    plt.xlabel("Шаг симуляции")
    plt.ylabel("Средний радиус кластера")
    plt.grid(True)
    plt.savefig("cluster_evolution.png")
    print("График 'cluster_evolution.png' сохранен.")
    
    # 3. Доп. анализ: плотность частиц
    plt.figure(figsize=(10, 6))
    plt.scatter(positions[-1, :, 0], positions[-1, :, 1], s=1, alpha=0.5)
    plt.title("Распределение частиц на последнем шаге (проекция XY)")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.savefig("final_distribution.png")
    print("График 'final_distribution.png' сохранен.")

if __name__ == "__main__":
    analyze_simulation()
