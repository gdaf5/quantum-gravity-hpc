#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "geodesic_core.hpp"

namespace py = pybind11;

// Wrapper for compute_christoffel_batch
py::array_t<double> py_compute_christoffel_batch(
    py::array_t<double> g_batch,
    py::array_t<double> dg_batch
) {
    auto g_buf = g_batch.request();
    auto dg_buf = dg_batch.request();
    
    if (g_buf.ndim != 3 || dg_buf.ndim != 4) {
        throw std::runtime_error("Input arrays must be 3D and 4D");
    }
    
    int N = g_buf.shape[0];
    
    // Call C++ function
    auto result = quantum_gravity::compute_christoffel_batch(
        static_cast<double*>(g_buf.ptr),
        static_cast<double*>(dg_buf.ptr),
        N
    );
    
    // Return as numpy array [N, 4, 4, 4]
    return py::array_t<double>(
        {N, 4, 4, 4},
        result.data()
    );
}

// Wrapper for geodesic_acceleration_batch
py::array_t<double> py_geodesic_acceleration_batch(
    py::array_t<double> Gamma_batch,
    py::array_t<double> velocity_batch
) {
    auto Gamma_buf = Gamma_batch.request();
    auto velocity_buf = velocity_batch.request();
    
    if (Gamma_buf.ndim != 4 || velocity_buf.ndim != 2) {
        throw std::runtime_error("Input arrays must be 4D and 2D");
    }
    
    int N = Gamma_buf.shape[0];
    
    // Call C++ function
    auto result = quantum_gravity::geodesic_acceleration_batch(
        static_cast<double*>(Gamma_buf.ptr),
        static_cast<double*>(velocity_buf.ptr),
        N
    );
    
    // Return as numpy array [N, 4]
    return py::array_t<double>(
        {N, 4},
        result.data()
    );
}

PYBIND11_MODULE(geodesic_cpp, m) {
    m.doc() = "C++ accelerated geodesic integration (20-50x speedup)";
    
    m.def("compute_christoffel_batch", &py_compute_christoffel_batch,
          "Compute Christoffel symbols for batch of particles",
          py::arg("g_batch"), py::arg("dg_batch"));
    
    m.def("geodesic_acceleration_batch", &py_geodesic_acceleration_batch,
          "Compute geodesic acceleration for batch of particles",
          py::arg("Gamma_batch"), py::arg("velocity_batch"));
}
