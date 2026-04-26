"""
Quantum Gravity CLI - Command Line Interface
=============================================

Unified CLI для запуска всех модулей проекта квантовой гравитации.

Usage:
    python main_cli.py --mode pinn --epochs 100 --batch-size 32
    python main_cli.py --mode foam --density 0.5 --iterations 100
    python main_cli.py --mode chaos --time 10.0
    python main_cli.py --mode detector --foam-density 0.1

Author: wosky021@gmail.com
Date: April 21, 2026
"""

import argparse
import sys
import torch
import numpy as np


def run_pinn_training(args):
    """Run Physics-Informed Neural Network training."""
    print("="*70)
    print("RUNNING PINN TRAINING")
    print("="*70)
    
    from ml_metric_predictor import PhysicsInformedMetricPredictor, MetricPredictorTrainer
    
    # Create model
    model = PhysicsInformedMetricPredictor(
        grid_shape=tuple(args.grid_shape),
        hidden_dim=args.hidden_dim
    )
    
    # Create trainer
    trainer = MetricPredictorTrainer(
        model,
        learning_rate=args.learning_rate,
        checkpoint_dir=args.checkpoint_dir,
        checkpoint_interval=args.checkpoint_interval
    )
    
    # Train
    trainer.train(
        n_epochs=args.epochs,
        batch_size=args.batch_size,
        resume_from=args.resume_from
    )
    
    # Save final model
    torch.save(model.state_dict(), args.output)
    print(f"\n[OK] Model saved to {args.output}")


def run_quantum_foam(args):
    """Run Quantum Foam simulation."""
    print("="*70)
    print("RUNNING QUANTUM FOAM SIMULATION")
    print("="*70)
    
    from quantum_foam import QuantumFoam
    from engine import MetricField
    
    # Create metric field
    grid_shape = tuple(args.grid_shape)
    g_metric = torch.zeros(*grid_shape, 4, 4, dtype=torch.float64)
    
    for i in range(grid_shape[0]):
        for j in range(grid_shape[1]):
            for k in range(grid_shape[2]):
                for l in range(grid_shape[3]):
                    g_metric[i, j, k, l] = torch.diag(torch.tensor([-1.0, 1.0, 1.0, 1.0]))
                    # Add perturbations
                    g_metric[i, j, k, l] += args.perturbation * torch.randn(4, 4)
                    g_metric[i, j, k, l] = 0.5 * (g_metric[i, j, k, l] + g_metric[i, j, k, l].T)
    
    metric_field = MetricField(g_metric, grid_spacing=args.grid_spacing)
    
    # Create foam simulator
    foam = QuantumFoam(
        grid_shape=grid_shape,
        creation_rate=args.foam_density,
        collapse_threshold=args.collapse_threshold,
        softening_length=args.softening,
        enable_hawking_evaporation=args.enable_hawking
    )
    
    # Run simulation
    print(f"\nRunning simulation for {args.iterations} steps...")
    dt = args.time_step
    
    for step in range(args.iterations):
        current_time = step * dt
        stats = foam.evolve_foam(
            metric_field, 
            current_time, 
            dt,
            enable_quantum_pressure=args.enable_quantum_pressure
        )
        
        if step % 10 == 0:
            print(f"  Step {step}/{args.iterations}: "
                  f"particles={stats['total_particles']}, "
                  f"singularities={stats['singularities']}")
    
    print("\n[OK] Quantum foam simulation complete!")
    print(f"  Final particles: {stats['total_particles']}")
    print(f"  Final singularities: {stats['singularities']}")


def run_chaos_analysis(args):
    """Run Lyapunov chaos analysis."""
    print("="*70)
    print("RUNNING CHAOS ANALYSIS")
    print("="*70)
    
    from chaos_analysis import LyapunovAnalyzer
    from quantum_foam import QuantumFoam
    from engine import MetricField
    
    # Create metric field
    grid_shape = tuple(args.grid_shape)
    g_metric = torch.zeros(*grid_shape, 4, 4, dtype=torch.float64)
    
    for i in range(grid_shape[0]):
        for j in range(grid_shape[1]):
            for k in range(grid_shape[2]):
                for l in range(grid_shape[3]):
                    g_metric[i, j, k, l] = torch.diag(torch.tensor([-1.0, 1.0, 1.0, 1.0]))
                    g_metric[i, j, k, l] += 0.01 * torch.randn(4, 4)
                    g_metric[i, j, k, l] = 0.5 * (g_metric[i, j, k, l] + g_metric[i, j, k, l].T)
    
    metric_field = MetricField(g_metric, grid_spacing=1.0)
    
    # Create foam
    foam = QuantumFoam(
        grid_shape=grid_shape,
        creation_rate=0.5,
        collapse_threshold=1.0,
        softening_length=0.1
    )
    
    # Create analyzer
    analyzer = LyapunovAnalyzer(
        perturbation_size=args.perturbation_size,
        n_iterations=args.iterations,
        dt=args.time_step
    )
    
    # Compute Lyapunov exponent
    result = analyzer.compute_lyapunov_exponent(
        foam, metric_field,
        initial_time=0.0,
        total_time=args.total_time
    )
    
    # Classify chaos
    chaos_type = analyzer.analyze_chaos_type(result['lyapunov_exponent'])
    print(f"\nChaos classification: {chaos_type}")
    
    # Plot
    analyzer.plot_divergence(save_path=args.output)
    
    print(f"\n[OK] Chaos analysis complete!")
    print(f"  Lyapunov exponent: λ = {result['lyapunov_exponent']:.6f}")


def run_observational_signatures(args):
    """Run observational signatures computation."""
    print("="*70)
    print("RUNNING OBSERVATIONAL SIGNATURES")
    print("="*70)
    
    from observational_signatures import VirtualDetector
    
    # Create detector
    detector_pos = torch.tensor([0.0, 0.0, 0.0, 0.0])
    detector = VirtualDetector(
        detector_position=detector_pos,
        detector_size=1.0
    )
    
    # Generate report
    results = detector.generate_observational_report(
        foam_density=args.foam_density,
        save_path=args.output
    )
    
    print(f"\n[OK] Observational signatures computed!")
    print(f"  Report saved to {args.output}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Quantum Gravity HPC - Unified Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train PINN for 1000 epochs
  python main_cli.py --mode pinn --epochs 1000 --batch-size 64
  
  # Run quantum foam with high density
  python main_cli.py --mode foam --foam-density 0.8 --iterations 200
  
  # Analyze chaos
  python main_cli.py --mode chaos --total-time 20.0
  
  # Compute observational signatures
  python main_cli.py --mode detector --foam-density 0.1
        """
    )
    
    # Global arguments
    parser.add_argument('--mode', type=str, required=True,
                       choices=['pinn', 'foam', 'chaos', 'detector'],
                       help='Operation mode')
    parser.add_argument('--grid-shape', type=int, nargs=4, default=[8, 8, 8, 8],
                       help='Grid shape (4D)')
    parser.add_argument('--output', type=str, default='output.txt',
                       help='Output file path')
    
    # PINN arguments
    parser.add_argument('--epochs', type=int, default=100,
                       help='Number of training epochs (PINN)')
    parser.add_argument('--batch-size', type=int, default=32,
                       help='Batch size (PINN)')
    parser.add_argument('--learning-rate', type=float, default=1e-4,
                       help='Learning rate (PINN)')
    parser.add_argument('--hidden-dim', type=int, default=256,
                       help='Hidden dimension (PINN)')
    parser.add_argument('--checkpoint-dir', type=str, default='checkpoints',
                       help='Checkpoint directory (PINN)')
    parser.add_argument('--checkpoint-interval', type=int, default=1000,
                       help='Checkpoint interval (PINN)')
    parser.add_argument('--resume-from', type=str, default=None,
                       help='Resume from checkpoint (PINN)')
    
    # Quantum Foam arguments
    parser.add_argument('--foam-density', type=float, default=0.5,
                       help='Foam creation rate or density')
    parser.add_argument('--iterations', type=int, default=100,
                       help='Number of iterations')
    parser.add_argument('--time-step', type=float, default=0.1,
                       help='Time step (Planck times)')
    parser.add_argument('--grid-spacing', type=float, default=1.0,
                       help='Grid spacing (Planck lengths)')
    parser.add_argument('--collapse-threshold', type=float, default=1.0,
                       help='Collapse threshold (r/r_s)')
    parser.add_argument('--softening', type=float, default=0.1,
                       help='Softening length (Planck lengths)')
    parser.add_argument('--perturbation', type=float, default=0.01,
                       help='Metric perturbation amplitude')
    parser.add_argument('--enable-hawking', action='store_true', default=True,
                       help='Enable Hawking evaporation')
    parser.add_argument('--enable-quantum-pressure', action='store_true', default=True,
                       help='Enable quantum pressure')
    
    # Chaos analysis arguments
    parser.add_argument('--perturbation-size', type=float, default=1e-8,
                       help='Perturbation size for Lyapunov')
    parser.add_argument('--total-time', type=float, default=10.0,
                       help='Total simulation time')
    
    args = parser.parse_args()
    
    # Route to appropriate function
    if args.mode == 'pinn':
        if args.output == 'output.txt':
            args.output = 'ml_metric_predictor.pth'
        run_pinn_training(args)
    elif args.mode == 'foam':
        run_quantum_foam(args)
    elif args.mode == 'chaos':
        if args.output == 'output.txt':
            args.output = 'lyapunov_divergence.png'
        run_chaos_analysis(args)
    elif args.mode == 'detector':
        if args.output == 'output.txt':
            args.output = 'observational_signatures.txt'
        run_observational_signatures(args)
    else:
        print(f"Unknown mode: {args.mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
