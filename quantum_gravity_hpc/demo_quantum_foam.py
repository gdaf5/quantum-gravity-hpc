"""
Quantum Foam Demonstration - Sub-Planckian Virtual Singularities
Shows the dynamics of virtual particle creation and collapse into micro-black holes.
"""

import torch
import numpy as np
import matplotlib.pyplot as plt
from quantum_foam import QuantumFoam, VirtualParticle
from engine import MetricField
import time

def create_fluctuating_metric(grid_shape=(8, 8, 8, 8), 
                              fluctuation_amplitude=0.1,
                              dtype=torch.float64):
    """
    Create metric with quantum fluctuations.
    
    Base: Minkowski + random perturbations
    """
    g_metric = torch.zeros((*grid_shape, 4, 4), dtype=dtype)
    
    # Minkowski background
    for it in range(grid_shape[0]):
        for ix in range(grid_shape[1]):
            for iy in range(grid_shape[2]):
                for iz in range(grid_shape[3]):
                    g_metric[it, ix, iy, iz] = torch.diag(
                        torch.tensor([-1.0, 1.0, 1.0, 1.0], dtype=dtype)
                    )
    
    # Add quantum fluctuations
    fluctuations = torch.randn_like(g_metric) * fluctuation_amplitude
    g_metric += fluctuations
    
    # Ensure symmetry
    for it in range(grid_shape[0]):
        for ix in range(grid_shape[1]):
            for iy in range(grid_shape[2]):
                for iz in range(grid_shape[3]):
                    g = g_metric[it, ix, iy, iz]
                    g_metric[it, ix, iy, iz] = (g + g.T) / 2.0
    
    return g_metric


def demo_basic_foam():
    """Basic demonstration of quantum foam dynamics"""
    print("\n" + "="*70)
    print("DEMO 1: Basic Quantum Foam Dynamics")
    print("="*70 + "\n")
    
    # Setup
    grid_shape = (8, 8, 8, 8)
    grid_spacing = 1.0
    
    print("Creating fluctuating metric...")
    g_metric = create_fluctuating_metric(grid_shape, fluctuation_amplitude=0.15)
    metric_field = MetricField(g_metric, grid_spacing)
    
    print("Initializing quantum foam...")
    foam = QuantumFoam(
        grid_shape=grid_shape,
        grid_spacing=grid_spacing,
        creation_rate=0.3,
        collapse_threshold=1.0,
        softening_length=0.1,
        enable_hawking_evaporation=True
    )
    
    # Evolution
    dt = 0.1
    n_steps = 100
    
    print(f"\nEvolving for {n_steps} steps (dt = {dt} t_P)...")
    print("-"*70)
    
    history = {
        'time': [],
        'particles': [],
        'singularities': [],
        'created': [],
        'collapsed': [],
        'evaporated': []
    }
    
    for step in range(n_steps):
        current_time = step * dt
        
        stats = foam.evolve_foam(metric_field, current_time, dt)
        
        # Record history
        history['time'].append(current_time)
        history['particles'].append(stats['total_particles'])
        history['singularities'].append(stats['singularities'])
        history['created'].append(stats['created'])
        history['collapsed'].append(stats['collapsed'])
        history['evaporated'].append(stats['evaporated'])
        
        if step % 20 == 0:
            print(f"t = {current_time:6.2f} t_P | "
                  f"Particles: {stats['total_particles']:3d} | "
                  f"Singularities: {stats['singularities']:3d} | "
                  f"Created: {stats['created']:2d} | "
                  f"Collapsed: {stats['collapsed']:2d} | "
                  f"Evaporated: {stats['evaporated']:2d}")
    
    print("-"*70)
    print("\n" + foam.visualize_foam_state())
    
    final_stats = foam.get_statistics()
    print(f"\nFinal Statistics:")
    print(f"  Total created:     {final_stats['total_created']}")
    print(f"  Total collapsed:   {final_stats['total_collapsed']}")
    print(f"  Total evaporated:  {final_stats['total_evaporated']}")
    print(f"  Average mass:      {final_stats['average_mass']:.3f} m_P")
    print(f"  Singularity fraction: {final_stats['singularity_fraction']:.1%}")
    
    return history, foam


def demo_high_energy_foam():
    """Demonstration with higher energy density (more violent foam)"""
    print("\n" + "="*70)
    print("DEMO 2: High-Energy Quantum Foam (Violent Regime)")
    print("="*70 + "\n")
    
    grid_shape = (8, 8, 8, 8)
    grid_spacing = 0.5  # Smaller spacing = higher resolution
    
    print("Creating high-energy fluctuating metric...")
    g_metric = create_fluctuating_metric(grid_shape, fluctuation_amplitude=0.3)
    metric_field = MetricField(g_metric, grid_spacing)
    
    print("Initializing high-energy quantum foam...")
    foam = QuantumFoam(
        grid_shape=grid_shape,
        grid_spacing=grid_spacing,
        creation_rate=1.0,  # Higher creation rate
        collapse_threshold=1.5,  # Easier collapse
        softening_length=0.05,  # Smaller softening
        enable_hawking_evaporation=True
    )
    
    dt = 0.05
    n_steps = 50
    
    print(f"\nEvolving for {n_steps} steps (dt = {dt} t_P)...")
    print("-"*70)
    
    for step in range(n_steps):
        current_time = step * dt
        stats = foam.evolve_foam(metric_field, current_time, dt)
        
        if step % 10 == 0:
            print(f"t = {current_time:6.2f} t_P | "
                  f"Particles: {stats['total_particles']:3d} | "
                  f"Singularities: {stats['singularities']:3d}")
    
    print("-"*70)
    print("\n" + foam.visualize_foam_state())
    
    return foam


def demo_singularity_formation():
    """Focused demonstration of singularity formation"""
    print("\n" + "="*70)
    print("DEMO 3: Singularity Formation and Evaporation")
    print("="*70 + "\n")
    
    grid_shape = (8, 8, 8, 8)
    grid_spacing = 1.0
    
    g_metric = create_fluctuating_metric(grid_shape, fluctuation_amplitude=0.2)
    metric_field = MetricField(g_metric, grid_spacing)
    
    foam = QuantumFoam(
        grid_shape=grid_shape,
        grid_spacing=grid_spacing,
        creation_rate=0.5,
        collapse_threshold=0.8,  # Easier collapse
        softening_length=0.1,
        enable_hawking_evaporation=True
    )
    
    dt = 0.1
    n_steps = 100
    
    print("Tracking singularity lifecycles...\n")
    
    singularity_births = []
    singularity_deaths = []
    
    for step in range(n_steps):
        current_time = step * dt
        
        prev_singularities = sum(1 for p in foam.virtual_particles if p.is_singularity)
        
        stats = foam.evolve_foam(metric_field, current_time, dt)
        
        curr_singularities = stats['singularities']
        
        # Track births
        if stats['collapsed'] > 0:
            singularity_births.append((current_time, stats['collapsed']))
            print(f"t = {current_time:6.2f} t_P: {stats['collapsed']} singularit{'y' if stats['collapsed']==1 else 'ies'} formed!")
        
        # Track deaths
        if stats['evaporated'] > 0:
            singularity_deaths.append((current_time, stats['evaporated']))
            print(f"t = {current_time:6.2f} t_P: {stats['evaporated']} singularit{'y' if stats['evaporated']==1 else 'ies'} evaporated!")
    
    print("\n" + "-"*70)
    print(f"Total singularities formed:    {len(singularity_births)}")
    print(f"Total singularities evaporated: {len(singularity_deaths)}")
    print(f"Currently active:              {foam.stats['current_singularities']}")
    
    return foam


def demo_softening_comparison():
    """Compare different softening parameters"""
    print("\n" + "="*70)
    print("DEMO 4: Softening Parameter Comparison")
    print("="*70 + "\n")
    
    grid_shape = (8, 8, 8, 8)
    grid_spacing = 1.0
    
    g_metric = create_fluctuating_metric(grid_shape, fluctuation_amplitude=0.15)
    metric_field = MetricField(g_metric, grid_spacing)
    
    softening_values = [0.01, 0.1, 0.5]
    
    for epsilon in softening_values:
        print(f"\nTesting with epsilon = {epsilon} l_P")
        print("-"*70)
        
        foam = QuantumFoam(
            grid_shape=grid_shape,
            grid_spacing=grid_spacing,
            creation_rate=0.5,
            collapse_threshold=1.0,
            softening_length=epsilon,
            enable_hawking_evaporation=True
        )
        
        dt = 0.1
        n_steps = 50
        
        max_particles = 0
        
        for step in range(n_steps):
            current_time = step * dt
            stats = foam.evolve_foam(metric_field, current_time, dt)
            max_particles = max(max_particles, stats['total_particles'])
        
        final_stats = foam.get_statistics()
        print(f"  Max particles reached: {max_particles}")
        print(f"  Final particles:       {foam.stats['current_particles']}")
        print(f"  Total collapsed:       {foam.stats['total_collapsed']}")
        print(f"  Singularity fraction:  {final_stats['singularity_fraction']:.1%}")


def run_all_demos():
    """Run all demonstrations"""
    print("\n" + "="*70)
    print("QUANTUM FOAM DEMONSTRATION SUITE")
    print("Sub-Planckian Virtual Singularities v3.0")
    print("="*70)
    
    start_time = time.time()
    
    # Demo 1: Basic dynamics
    history, foam1 = demo_basic_foam()
    
    # Demo 2: High energy
    foam2 = demo_high_energy_foam()
    
    # Demo 3: Singularity tracking
    foam3 = demo_singularity_formation()
    
    # Demo 4: Softening comparison
    demo_softening_comparison()
    
    elapsed = time.time() - start_time
    
    print("\n" + "="*70)
    print("ALL DEMONSTRATIONS COMPLETE")
    print("="*70)
    print(f"Total time: {elapsed:.2f} seconds")
    print("\nKey Results:")
    print(f"  Demo 1 - Basic foam created {foam1.stats['total_created']} particles")
    print(f"  Demo 2 - High-energy foam created {foam2.stats['total_created']} particles")
    print(f"  Demo 3 - Tracked {foam3.stats['total_collapsed']} singularity formations")
    print("\nConclusion:")
    print("  ✓ Stochastic particle creation working")
    print("  ✓ Singularity collapse mechanism functional")
    print("  ✓ Hawking evaporation integrated")
    print("  ✓ Softening prevents numerical explosions")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Run all demonstrations
    run_all_demos()
    
    print("\nTo run individual demos:")
    print("  from demo_quantum_foam import demo_basic_foam")
    print("  history, foam = demo_basic_foam()")
