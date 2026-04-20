use pyo3::prelude::*;
use numpy::{PyArray2, PyArray4, PyReadonlyArray2, PyReadonlyArray4};
use ndarray::{Array2, Array4, ArrayView2, ArrayView4, s};
use rayon::prelude::*;

/// Invert 4x4 matrix using LU decomposition
fn invert_4x4(mat: &[[f64; 4]; 4]) -> [[f64; 4]; 4] {
    // Simple cofactor method for 4x4
    let mut inv = [[0.0; 4]; 4];
    let m = mat;
    
    inv[0][0] = m[1][1]*m[2][2]*m[3][3] - m[1][1]*m[2][3]*m[3][2] - m[2][1]*m[1][2]*m[3][3] + 
                m[2][1]*m[1][3]*m[3][2] + m[3][1]*m[1][2]*m[2][3] - m[3][1]*m[1][3]*m[2][2];
    inv[1][0] = -m[1][0]*m[2][2]*m[3][3] + m[1][0]*m[2][3]*m[3][2] + m[2][0]*m[1][2]*m[3][3] - 
                m[2][0]*m[1][3]*m[3][2] - m[3][0]*m[1][2]*m[2][3] + m[3][0]*m[1][3]*m[2][2];
    inv[2][0] = m[1][0]*m[2][1]*m[3][3] - m[1][0]*m[2][3]*m[3][1] - m[2][0]*m[1][1]*m[3][3] + 
                m[2][0]*m[1][3]*m[3][1] + m[3][0]*m[1][1]*m[2][3] - m[3][0]*m[1][3]*m[2][1];
    inv[3][0] = -m[1][0]*m[2][1]*m[3][2] + m[1][0]*m[2][2]*m[3][1] + m[2][0]*m[1][1]*m[3][2] - 
                m[2][0]*m[1][2]*m[3][1] - m[3][0]*m[1][1]*m[2][2] + m[3][0]*m[1][2]*m[2][1];
    
    inv[0][1] = -m[0][1]*m[2][2]*m[3][3] + m[0][1]*m[2][3]*m[3][2] + m[2][1]*m[0][2]*m[3][3] - 
                m[2][1]*m[0][3]*m[3][2] - m[3][1]*m[0][2]*m[2][3] + m[3][1]*m[0][3]*m[2][2];
    inv[1][1] = m[0][0]*m[2][2]*m[3][3] - m[0][0]*m[2][3]*m[3][2] - m[2][0]*m[0][2]*m[3][3] + 
                m[2][0]*m[0][3]*m[3][2] + m[3][0]*m[0][2]*m[2][3] - m[3][0]*m[0][3]*m[2][2];
    inv[2][1] = -m[0][0]*m[2][1]*m[3][3] + m[0][0]*m[2][3]*m[3][1] + m[2][0]*m[0][1]*m[3][3] - 
                m[2][0]*m[0][3]*m[3][1] - m[3][0]*m[0][1]*m[2][3] + m[3][0]*m[0][3]*m[2][1];
    inv[3][1] = m[0][0]*m[2][1]*m[3][2] - m[0][0]*m[2][2]*m[3][1] - m[2][0]*m[0][1]*m[3][2] + 
                m[2][0]*m[0][2]*m[3][1] + m[3][0]*m[0][1]*m[2][2] - m[3][0]*m[0][2]*m[2][1];
    
    inv[0][2] = m[0][1]*m[1][2]*m[3][3] - m[0][1]*m[1][3]*m[3][2] - m[1][1]*m[0][2]*m[3][3] + 
                m[1][1]*m[0][3]*m[3][2] + m[3][1]*m[0][2]*m[1][3] - m[3][1]*m[0][3]*m[1][2];
    inv[1][2] = -m[0][0]*m[1][2]*m[3][3] + m[0][0]*m[1][3]*m[3][2] + m[1][0]*m[0][2]*m[3][3] - 
                m[1][0]*m[0][3]*m[3][2] - m[3][0]*m[0][2]*m[1][3] + m[3][0]*m[0][3]*m[1][2];
    inv[2][2] = m[0][0]*m[1][1]*m[3][3] - m[0][0]*m[1][3]*m[3][1] - m[1][0]*m[0][1]*m[3][3] + 
                m[1][0]*m[0][3]*m[3][1] + m[3][0]*m[0][1]*m[1][3] - m[3][0]*m[0][3]*m[1][1];
    inv[3][2] = -m[0][0]*m[1][1]*m[3][2] + m[0][0]*m[1][2]*m[3][1] + m[1][0]*m[0][1]*m[3][2] - 
                m[1][0]*m[0][2]*m[3][1] - m[3][0]*m[0][1]*m[1][2] + m[3][0]*m[0][2]*m[1][1];
    
    inv[0][3] = -m[0][1]*m[1][2]*m[2][3] + m[0][1]*m[1][3]*m[2][2] + m[1][1]*m[0][2]*m[2][3] - 
                m[1][1]*m[0][3]*m[2][2] - m[2][1]*m[0][2]*m[1][3] + m[2][1]*m[0][3]*m[1][2];
    inv[1][3] = m[0][0]*m[1][2]*m[2][3] - m[0][0]*m[1][3]*m[2][2] - m[1][0]*m[0][2]*m[2][3] + 
                m[1][0]*m[0][3]*m[2][2] + m[2][0]*m[0][2]*m[1][3] - m[2][0]*m[0][3]*m[1][2];
    inv[2][3] = -m[0][0]*m[1][1]*m[2][3] + m[0][0]*m[1][3]*m[2][1] + m[1][0]*m[0][1]*m[2][3] - 
                m[1][0]*m[0][3]*m[2][1] - m[2][0]*m[0][1]*m[1][3] + m[2][0]*m[0][3]*m[1][1];
    inv[3][3] = m[0][0]*m[1][1]*m[2][2] - m[0][0]*m[1][2]*m[2][1] - m[1][0]*m[0][1]*m[2][2] + 
                m[1][0]*m[0][2]*m[2][1] + m[2][0]*m[0][1]*m[1][2] - m[2][0]*m[0][2]*m[1][1];
    
    let det = m[0][0]*inv[0][0] + m[0][1]*inv[1][0] + m[0][2]*inv[2][0] + m[0][3]*inv[3][0];
    
    if det.abs() < 1e-15 {
        // Return identity for singular matrix
        return [[1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0]];
    }
    
    let inv_det = 1.0 / det;
    for i in 0..4 {
        for j in 0..4 {
            inv[i][j] *= inv_det;
        }
    }
    
    inv
}

/// Compute Christoffel symbols for batch of particles
#[pyfunction]
fn compute_christoffel_batch<'py>(
    py: Python<'py>,
    g_batch: PyReadonlyArray2<'py, f64>,
    dg_batch: PyReadonlyArray4<'py, f64>,
) -> PyResult<&'py PyArray4<f64>> {
    let g = g_batch.as_array();
    let dg = dg_batch.as_array();
    let n = g.shape()[0];
    
    // Parallel computation using rayon
    let results: Vec<_> = (0..n)
        .into_par_iter()
        .map(|i| {
            // Extract metric for particle i
            let mut g_mat = [[0.0; 4]; 4];
            for mu in 0..4 {
                for nu in 0..4 {
                    g_mat[mu][nu] = g[[i, mu * 4 + nu]];
                }
            }
            
            let g_inv = invert_4x4(&g_mat);
            
            // Compute Christoffel symbols
            let mut gamma = [[[0.0; 4]; 4]; 4];
            for sigma in 0..4 {
                for mu in 0..4 {
                    for nu in 0..4 {
                        let mut sum = 0.0;
                        for rho in 0..4 {
                            let term1 = dg[[i, mu, rho, nu]];
                            let term2 = dg[[i, nu, rho, mu]];
                            let term3 = dg[[i, rho, mu, nu]];
                            sum += g_inv[sigma][rho] * (term1 + term2 - term3);
                        }
                        gamma[sigma][mu][nu] = 0.5 * sum;
                    }
                }
            }
            
            gamma
        })
        .collect();
    
    // Convert to numpy array
    let mut output = Array4::<f64>::zeros((n, 4, 4, 4));
    for (i, gamma) in results.iter().enumerate() {
        for sigma in 0..4 {
            for mu in 0..4 {
                for nu in 0..4 {
                    output[[i, sigma, mu, nu]] = gamma[sigma][mu][nu];
                }
            }
        }
    }
    
    Ok(PyArray4::from_owned_array(py, output))
}

/// Compute geodesic acceleration for batch
#[pyfunction]
fn geodesic_acceleration_batch<'py>(
    py: Python<'py>,
    gamma_batch: PyReadonlyArray4<'py, f64>,
    velocity_batch: PyReadonlyArray2<'py, f64>,
) -> PyResult<&'py PyArray2<f64>> {
    let gamma = gamma_batch.as_array();
    let velocity = velocity_batch.as_array();
    let n = gamma.shape()[0];
    
    // Parallel computation
    let results: Vec<_> = (0..n)
        .into_par_iter()
        .map(|i| {
            let mut accel = [0.0; 4];
            for sigma in 0..4 {
                let mut sum = 0.0;
                for mu in 0..4 {
                    for nu in 0..4 {
                        sum += gamma[[i, sigma, mu, nu]] * velocity[[i, mu]] * velocity[[i, nu]];
                    }
                }
                accel[sigma] = -sum;
            }
            accel
        })
        .collect();
    
    // Convert to numpy array
    let mut output = Array2::<f64>::zeros((n, 4));
    for (i, accel) in results.iter().enumerate() {
        for j in 0..4 {
            output[[i, j]] = accel[j];
        }
    }
    
    Ok(PyArray2::from_owned_array(py, output))
}

#[pymodule]
fn geodesic_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compute_christoffel_batch, m)?)?;
    m.add_function(wrap_pyfunction!(geodesic_acceleration_batch, m)?)?;
    Ok(())
}
