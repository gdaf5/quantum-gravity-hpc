#pragma once

#include <vector>
#include <array>
#include <cmath>

namespace quantum_gravity {

// Compute Christoffel symbols for batch of particles
// g_batch: [N, 4, 4] metric tensors (flattened)
// dg_batch: [N, 4, 4, 4] metric derivatives (flattened)
// Returns: [N, 4, 4, 4] Christoffel symbols (flattened)
std::vector<double> compute_christoffel_batch(
    const double* g_batch,
    const double* dg_batch,
    int N
);

// Compute geodesic acceleration for batch
// Gamma_batch: [N, 4, 4, 4] Christoffel symbols
// velocity_batch: [N, 4] 4-velocities
// Returns: [N, 4] accelerations
std::vector<double> geodesic_acceleration_batch(
    const double* Gamma_batch,
    const double* velocity_batch,
    int N
);

// Helper: Matrix inversion for 4x4 matrix
void invert_4x4(const double* mat, double* inv);

} // namespace quantum_gravity
