from setuptools import setup, Extension
import pybind11
import sys
import os

# Compiler flags
extra_compile_args = []
extra_link_args = []

if sys.platform == 'win32':
    # Windows (MSVC)
    extra_compile_args = [
        '/O2',           # Optimization
        '/openmp',       # OpenMP
        '/std:c++17',    # C++17
        '/EHsc',         # Exception handling
    ]
    extra_link_args = ['/openmp']
else:
    # Linux/Mac (GCC/Clang)
    extra_compile_args = [
        '-O3',           # Optimization
        '-march=native', # CPU-specific optimizations
        '-fopenmp',      # OpenMP
        '-std=c++17',    # C++17
        '-ffast-math',   # Fast math
    ]
    extra_link_args = ['-fopenmp']

ext_modules = [
    Extension(
        'geodesic_cpp',
        sources=[
            'cpp/bindings.cpp',
            'cpp/geodesic_core.cpp',
        ],
        include_dirs=[
            pybind11.get_include(),
            'cpp',
        ],
        language='c++',
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
]

setup(
    name='geodesic_cpp',
    version='1.0.0',
    author='Quantum Gravity Research',
    description='C++ accelerated geodesic integration',
    ext_modules=ext_modules,
    install_requires=['pybind11>=2.6.0'],
    zip_safe=False,
)
