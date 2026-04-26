import sys
import os
import numpy as np
# Add parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from holographic_core.mesh_engine import AdaptiveMesh
from holographic_core.tensor_engine import TensorEngine

def test_integration():
    print("Testing Pro-Stack Integration...")
    
    # 1. Test Tensor Engine
    te = TensorEngine(n_sites=16)
    entropy = te.get_entanglement_entropy(8)
    print(f"Entropy at site 8: {entropy:.4f}")
    
    # 2. Test Mesh Engine
    # Create dummy entanglement field
    field = np.random.rand(10, 10, 10)
    mesh = AdaptiveMesh(bounds=np.array([[0,10],[0,10],[0,10]]))
    points = mesh.generate_mesh(field)
    print(f"Generated {len(points)} mesh points based on entanglement.")
    
    print("Integration test passed.")

if __name__ == "__main__":
    test_integration()
