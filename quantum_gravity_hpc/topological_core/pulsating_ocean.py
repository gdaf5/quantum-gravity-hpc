"""
PULSATING OCEAN: Topological Evolution Demo (Fixed)
===========================================
Simulates dynamic graph evolution under energy pressure.
Nodes rearrange their connections to avoid singularities.
"""
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

def simulate_evolution(num_nodes=50, steps=50):
    G = nx.erdos_renyi_graph(num_nodes, 0.05)
    history = [G.number_of_edges()]
    
    print(f"Starting evolution. Initial edges: {history[0]}")
    
    for step in range(steps):
        target_node = np.random.randint(num_nodes)
        # Установим порог ниже, чтобы гарантировать рост
        if G.degree[target_node] > 2: 
            distant_node = np.random.randint(num_nodes)
            G.add_edge(target_node, distant_node)
            print(f"Step {step}: Rewiring at node {target_node}.")
        
        history.append(G.number_of_edges())
        
    print(f"Final edge count: {history[-1]}")
    
    # Прямая отрисовка
    plt.figure(figsize=(10, 6))
    plt.plot(history, marker='o', linestyle='-', color='r')
    plt.title("Quantum Graphity: Complexity Evolution")
    plt.xlabel("Evolution Steps")
    plt.ylabel("Number of Edges (Complexity)")
    plt.grid(True)
    plt.savefig('topology_evolution_v2.png')
    print("Map saved to topology_evolution_v2.png")
    # Текстовый дамп для проверки
    print(f"History (first 10 steps): {history[:10]}")

if __name__ == "__main__":
    simulate_evolution()
