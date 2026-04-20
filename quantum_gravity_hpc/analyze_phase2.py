"""
Quick D2 calculation for Phase 2
"""
import h5py
import numpy as np

print("="*70)
print("PHASE 2 RESULTS - QUICK ANALYSIS")
print("="*70)

# Load data
with h5py.File('phase2_breakthrough.h5', 'r') as f:
    particles = f['particles'][:]
    M = f.attrs['M']
    r_s = f.attrs['r_s']
    
print(f"\nSimulation:")
print(f"  M = {M} m_P")
print(f"  r_s = {r_s} l_P")
print(f"  Steps: {len(particles)}")
print(f"  Particles: {particles.shape[1]}")

# Calculate D2 (correlation dimension)
print("\nCalculating fractal dimension D2...")

# Use final state
final_state = particles[-1]
positions = final_state[:, 1:4]

# Compute pairwise distances
N = len(positions)
distances = []
for i in range(min(N, 100)):  # Sample for speed
    for j in range(i+1, min(N, 100)):
        r = np.sqrt(np.sum((positions[i] - positions[j])**2))
        if r > 0:
            distances.append(r)

distances = np.array(distances)

# Correlation integral C(r) ~ r^D2
scales = np.logspace(np.log10(distances.min()), np.log10(distances.max()), 20)
correlations = []

for scale in scales:
    count = np.sum(distances < scale)
    correlations.append(count / len(distances))

correlations = np.array(correlations)

# Fit log(C) vs log(r)
valid = (correlations > 0) & (scales > 0)
if np.sum(valid) > 5:
    log_r = np.log(scales[valid])
    log_C = np.log(correlations[valid])
    
    # Linear fit
    coeffs = np.polyfit(log_r, log_C, 1)
    D2 = coeffs[0]
    
    print(f"\nFractal Dimension D2 = {D2:.3f}")
    
    if D2 > 4.0:
        print("\n*** BREAKTHROUGH! D2 > 4.0 ***")
        print("Strong quantum gravity effects detected!")
    elif D2 > 3.5:
        print("\n*** SIGNIFICANT! D2 > 3.5 ***")
        print("Quantum corrections visible!")
    else:
        print(f"\nD2 = {D2:.3f} (still classical regime)")
else:
    print("\nNot enough data for D2 calculation")
    D2 = None

# Energy analysis
print("\nEnergy analysis...")
velocities = final_state[:, 5:8]
v_mag = np.sqrt(np.sum(velocities**2, axis=1))
print(f"  Mean velocity: {v_mag.mean():.3f} c")
print(f"  Max velocity: {v_mag.max():.3f} c")

# Position analysis
r = np.sqrt(np.sum(positions**2, axis=1))
print(f"\nPosition analysis:")
print(f"  Mean radius: {r.mean():.1f} l_P ({r.mean()/r_s:.2f} r_s)")
print(f"  Min radius: {r.min():.1f} l_P ({r.min()/r_s:.2f} r_s)")
print(f"  Max radius: {r.max():.1f} l_P ({r.max()/r_s:.2f} r_s)")

# Save result
result = {
    'D2': float(D2) if D2 is not None else None,
    'mean_velocity': float(v_mag.mean()),
    'mean_radius': float(r.mean()),
    'regime': 'EXTREME - Near horizon'
}

import json
with open('phase2_results.json', 'w') as f:
    json.dump(result, f, indent=2)

print("\n" + "="*70)
print("RESULTS SAVED: phase2_results.json")
print("="*70)
