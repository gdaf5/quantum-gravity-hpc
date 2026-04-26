import sys
import os
import importlib
import inspect

# Add parent directory to path to find scientific modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_module_method(module_name, class_name=None, method_name=None):
    try:
        mod = importlib.import_module(module_name)
        print(f"Module '{module_name}' loaded.")
        
        obj = mod
        if class_name:
            cls = getattr(mod, class_name)
            obj = cls()
            print(f"Class '{class_name}' instantiated.")
            
        method = getattr(obj, method_name)
        print(f"Running method '{method_name}'...")
        result = method()
        print("Done.")
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    # Example usage: python runner.py demo_simple QuantumEntanglementGeometrySimple run_analysis
    module = sys.argv[1]
    cls = sys.argv[2] if len(sys.argv) > 2 else None
    meth = sys.argv[3] if len(sys.argv) > 3 else 'run'
    run_module_method(module, cls, meth)
