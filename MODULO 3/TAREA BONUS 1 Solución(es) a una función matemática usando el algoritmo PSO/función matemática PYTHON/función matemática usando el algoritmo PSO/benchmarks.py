# benchmarks.py

###Funciones objetivo y utilidades para benchmarks.


import numpy as np


def funcion_rastrigin(x: np.ndarray) -> float:
    
#   Función Rastrigin multi-dimensional.
#   f(x) = 10*n + sum(x_i^2 - 10*cos(2*pi*x_i))
#   Óptimo global en x = 0 con f(0)=0.
    
    A = 10.0
    n = x.size
    return A * n + float(np.sum(x**2 - A * np.cos(2 * np.pi * x)))


def crear_limites(dim: int, minimo: float = -5.12, maximo: float = 5.12) -> np.ndarray:
    
#   Devuelve array límites shape (dim,2) con (min, max) por dimensión.
    
    limites = np.tile(np.array([minimo, maximo]), (dim, 1))
    return limites
