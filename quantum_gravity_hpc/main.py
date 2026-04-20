import torch
import torch.nn.functional as F
from engine import batch_geodesic
from logger import TrajectoryLogger

def get_batch_metrics(particles, grid):
    """
    Интерполирует метрику для всех частиц сразу через grid_sample.
    grid shape: [8, 8, 8, 8, 4, 4]
    """
    N = particles.shape[0]
    
    # grid [8, 8, 8, 8, 16] - 5 dim
    # grid_sample [Batch, Channel, D, H, W]
    # grid [8, 8, 8, 8, 16] -> permute(4, 0, 1, 2, 3) -> [16, 8, 8, 8, 8]
    # Нам нужно 3D: D,H,W = 8,8,8. t=8. C=16. 
    # Берем срез t=0: [0, 8, 8, 8, 16] -> permute(4, 1, 2, 3) -> [16, 8, 8, 8]
    grid_input = grid[0].permute(3, 0, 1, 2).unsqueeze(0) 
    
    # grid_coords [1, 1, 1, N, 3]
    grid_coords = (particles[:, 1:4] / 5.0).view(1, 1, 1, N, 3)
    
    g_batch_raw = F.grid_sample(grid_input, grid_coords, align_corners=True)
    g_batch = g_batch_raw.view(16, N).permute(1, 0)
    
    return g_batch.view(N, 4, 4)

def run_hpc_simulation():
    print("Запуск HPC-симуляции (GridSample + vmap)...")
    
    N = 100
    grid_size = 8
    # 4*4=16 компонент метрики в последнем измерении
    grid = torch.rand((grid_size, grid_size, grid_size, grid_size, 16), dtype=torch.float64)
    
    logger = TrajectoryLogger("cluster_experiment.h5", num_particles=N)
    particles = torch.randn((N, 8), dtype=torch.float64, requires_grad=False)
    
    # 5 шагов
    for step in range(5):
        g_locals = get_batch_metrics(particles, grid)
        particles = batch_geodesic(particles, g_locals)
        logger.log_step(particles)
        
        mean_r = torch.mean(torch.norm(particles[:, 1:4], dim=1))
        print(f"Шаг {step}. Радиус={mean_r:.2f}")
    
    logger.close()
    print(f"Симуляция завершена.")

if __name__ == "__main__":
    run_hpc_simulation()