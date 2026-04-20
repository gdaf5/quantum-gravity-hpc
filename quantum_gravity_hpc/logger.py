import h5py
import torch
import numpy as np
from datetime import datetime

class TrajectoryLogger:
    """
    Эффективный логгер для сохранения данных в HDF5.
    Файл открывается один раз и держится открытым до завершения работы.
    """
    def __init__(self, filename="simulation_results.h5", num_particles=1000):
        self.filename = filename
        self.f = h5py.File(self.filename, 'w')
        self.f.attrs['created_at'] = str(datetime.now())
        self.dataset = self.f.create_dataset(
            "particles", 
            shape=(0, num_particles, 8), 
            maxshape=(None, num_particles, 8),
            chunks=True, compression="gzip"
        )
        
    def log_step(self, particles_tensor):
        data = particles_tensor.cpu().detach().numpy()
        # Добавляем новый шаг в датасет
        self.dataset.resize((self.dataset.shape[0] + 1, data.shape[0], data.shape[1]))
        self.dataset[-1, :, :] = data
        
    def close(self):
        self.f.close()
