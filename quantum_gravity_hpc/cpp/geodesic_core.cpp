#include "geodesic_core.hpp"
#include <cstring>
#include <algorithm>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace quantum_gravity {

// Helper: 4x4 matrix inversion using cofactor method
void invert_4x4(const double* mat, double* inv) {
    double det;
    double m[16];
    std::memcpy(m, mat, 16 * sizeof(double));
    
    inv[0] = m[5]*m[10]*m[15] - m[5]*m[11]*m[14] - m[9]*m[6]*m[15] + 
             m[9]*m[7]*m[14] + m[13]*m[6]*m[11] - m[13]*m[7]*m[10];
    inv[4] = -m[4]*m[10]*m[15] + m[4]*m[11]*m[14] + m[8]*m[6]*m[15] - 
             m[8]*m[7]*m[14] - m[12]*m[6]*m[11] + m[12]*m[7]*m[10];
    inv[8] = m[4]*m[9]*m[15] - m[4]*m[11]*m[13] - m[8]*m[5]*m[15] + 
             m[8]*m[7]*m[13] + m[12]*m[5]*m[11] - m[12]*m[7]*m[9];
    inv[12] = -m[4]*m[9]*m[14] + m[4]*m[10]*m[13] + m[8]*m[5]*m[14] - 
              m[8]*m[6]*m[13] - m[12]*m[5]*m[10] + m[12]*m[6]*m[9];
    inv[1] = -m[1]*m[10]*m[15] + m[1]*m[11]*m[14] + m[9]*m[2]*m[15] - 
             m[9]*m[3]*m[14] - m[13]*m[2]*m[11] + m[13]*m[3]*m[10];
    inv[5] = m[0]*m[10]*m[15] - m[0]*m[11]*m[14] - m[8]*m[2]*m[15] + 
             m[8]*m[3]*m[14] + m[12]*m[2]*m[11] - m[12]*m[3]*m[10];
    inv[9] = -m[0]*m[9]*m[15] + m[0]*m[11]*m[13] + m[8]*m[1]*m[15] - 
             m[8]*m[3]*m[13] - m[12]*m[1]*m[11] + m[12]*m[3]*m[9];
    inv[13] = m[0]*m[9]*m[14] - m[0]*m[10]*m[13] - m[8]*m[1]*m[14] + 
              m[8]*m[2]*m[13] + m[12]*m[1]*m[10] - m[12]*m[2]*m[9];
    inv[2] = m[1]*m[6]*m[15] - m[1]*m[7]*m[14] - m[5]*m[2]*m[15] + 
             m[5]*m[3]*m[14] + m[13]*m[2]*m[7] - m[13]*m[3]*m[6];
    inv[6] = -m[0]*m[6]*m[15] + m[0]*m[7]*m[14] + m[4]*m[2]*m[15] - 
             m[4]*m[3]*m[14] - m[12]*m[2]*m[7] + m[12]*m[3]*m[6];
    inv[10] = m[0]*m[5]*m[15] - m[0]*m[7]*m[13] - m[4]*m[1]*m[15] + 
              m[4]*m[3]*m[13] + m[12]*m[1]*m[7] - m[12]*m[3]*m[5];
    inv[14] = -m[0]*m[5]*m[14] + m[0]*m[6]*m[13] + m[4]*m[1]*m[14] - 
              m[4]*m[2]*m[13] - m[12]*m[1]*m[6] + m[12]*m[2]*m[5];
    inv[3] = -m[1]*m[6]*m[11] + m[1]*m[7]*m[10] + m[5]*m[2]*m[11] - 
             m[5]*m[3]*m[10] - m[9]*m[2]*m[7] + m[9]*m[3]*m[6];
    inv[7] = m[0]*m[6]*m[11] - m[0]*m[7]*m[10] - m[4]*m[2]*m[11] + 
             m[4]*m[3]*m[10] + m[8]*m[2]*m[7] - m[8]*m[3]*m[6];
    inv[11] = -m[0]*m[5]*m[11] + m[0]*m[7]*m[9] + m[4]*m[1]*m[11] - 
              m[4]*m[3]*m[9] - m[8]*m[1]*m[7] + m[8]*m[3]*m[5];
    inv[15] = m[0]*m[5]*m[10] - m[0]*m[6]*m[9] - m[4]*m[1]*m[10] + 
              m[4]*m[2]*m[9] + m[8]*m[1]*m[6] - m[8]*m[2]*m[5];
    
    det = m[0]*inv[0] + m[1]*inv[4] + m[2]*inv[8] + m[3]*inv[12];
    
    if (std::abs(det) < 1e-15) {
        // Singular matrix, return identity
        std::fill(inv, inv + 16, 0.0);
        inv[0] = inv[5] = inv[10] = inv[15] = 1.0;
        return;
    }
    
    det = 1.0 / det;
    for (int i = 0; i < 16; i++) {
        inv[i] *= det;
    }
}

std::vector<double> compute_christoffel_batch(
    const double* g_batch,
    const double* dg_batch,
    int N
) {
    std::vector<double> Gamma_batch(N * 4 * 4 * 4, 0.0);
    
    #ifdef _OPENMP
    #pragma omp parallel for
    #endif
    for (int n = 0; n < N; ++n) {
        // Get pointers for this particle
        const double* g = g_batch + n * 16;
        const double* dg = dg_batch + n * 64;
        double* Gamma = Gamma_batch.data() + n * 64;
        
        // Compute inverse metric
        double g_inv[16];
        invert_4x4(g, g_inv);
        
        // Compute Christoffel symbols
        // Γ^σ_{μν} = ½ g^{σρ} (∂_μ g_{ρν} + ∂_ν g_{ρμ} - ∂_ρ g_{μν})
        for (int sigma = 0; sigma < 4; ++sigma) {
            for (int mu = 0; mu < 4; ++mu) {
                for (int nu = 0; nu < 4; ++nu) {
                    double sum = 0.0;
                    for (int rho = 0; rho < 4; ++rho) {
                        // dg[mu, rho, nu] = dg[mu*16 + rho*4 + nu]
                        double term1 = dg[mu * 16 + rho * 4 + nu];
                        double term2 = dg[nu * 16 + rho * 4 + mu];
                        double term3 = dg[rho * 16 + mu * 4 + nu];
                        
                        sum += g_inv[sigma * 4 + rho] * (term1 + term2 - term3);
                    }
                    Gamma[sigma * 16 + mu * 4 + nu] = 0.5 * sum;
                }
            }
        }
    }
    
    return Gamma_batch;
}

std::vector<double> geodesic_acceleration_batch(
    const double* Gamma_batch,
    const double* velocity_batch,
    int N
) {
    std::vector<double> accel_batch(N * 4, 0.0);
    
    #ifdef _OPENMP
    #pragma omp parallel for
    #endif
    for (int n = 0; n < N; ++n) {
        const double* Gamma = Gamma_batch + n * 64;
        const double* velocity = velocity_batch + n * 4;
        double* accel = accel_batch.data() + n * 4;
        
        // a^σ = -Γ^σ_{μν} u^μ u^ν
        for (int sigma = 0; sigma < 4; ++sigma) {
            double sum = 0.0;
            for (int mu = 0; mu < 4; ++mu) {
                for (int nu = 0; nu < 4; ++nu) {
                    sum += Gamma[sigma * 16 + mu * 4 + nu] * 
                           velocity[mu] * velocity[nu];
                }
            }
            accel[sigma] = -sum;
        }
    }
    
    return accel_batch;
}

} // namespace quantum_gravity
