import numpy as np
import matplotlib.pyplot as plt
import os

def create_animation(data_dir="plots"):
    # Создаем папку для кадров
    if not os.path.exists("frames"):
        os.makedirs("frames")
        
    # Получаем список файлов и сортируем их
    files = sorted([f for f in os.listdir(data_dir) if f.endswith('.npy')])
    
    if not files:
        print(f"Файлы не найдены в папке {data_dir}. Сначала запусти симуляцию.")
        return

    print(f"Найдено {len(files)} файлов. Генерирую кадры...")
    
    for i, file in enumerate(files):
        data = np.load(os.path.join(data_dir, file))
        
        plt.figure(figsize=(8, 6))
        # Визуализируем phi (конформный фактор)
        # origin='lower' важно для правильной ориентации осей
        im = plt.imshow(data, cmap='inferno', origin='lower')
        plt.colorbar(im, label='Amplitude of Phi')
        plt.title(f"Gravitational Wave Propagation - Step {i*20}")
        plt.xlabel("X")
        plt.ylabel("Y")
        
        plt.savefig(f"frames/frame_{i:04d}.png")
        plt.close()
    print("Кадры готовы в папке 'frames'! Можешь собрать их в GIF.")

if __name__ == "__main__":
    create_animation()
