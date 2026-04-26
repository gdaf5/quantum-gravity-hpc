from test_lyapunov_scientific import run_scientific_analysis

result = run_scientific_analysis(foam_density=0.3, verbose=True)
print(f"\n\nFinal lambda = {result['lyapunov_exponent']:.6f}")
