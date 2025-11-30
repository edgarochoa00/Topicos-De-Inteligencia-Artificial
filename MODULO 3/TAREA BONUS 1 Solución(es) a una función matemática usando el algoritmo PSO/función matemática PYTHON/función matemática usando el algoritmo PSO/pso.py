# pso.py
"""
Optimización por Enjambre de Partículas (PSO)
"""

from typing import Callable, List, Tuple
import numpy as np


class Particula:
    #
#    Representa una partícula del enjambre (PSO).
#
#    Atributos:
#        posicion: np.ndarray (dim,)
#        velocidad: np.ndarray (dim,)
#        mejor_posicion: np.ndarray (dim,) - mejor posición personal
#        mejor_valor: float - valor objetivo en mejor_posicion
    #

    def __init__(self, dim: int, limites: np.ndarray, rng: np.random.Generator):
        """
        Inicializa posición y velocidad de la partícula.

        :param dim: número de dimensiones
        :param limites: np.array shape (dim,2) con (min, max) por dimensión
        :param rng: generador aleatorio numpy
        """
        self.dim = dim
        self.limites = limites
        self.rng = rng

        # posición inicial uniforme en los límites
        self.posicion = rng.uniform(limites[:, 0], limites[:, 1])
        rango = limites[:, 1] - limites[:, 0]
        # velocidad inicial pequeña relativa al rango
        self.velocidad = rng.uniform(-rango, rango) * 0.1

        self.mejor_posicion = self.posicion.copy()
        self.mejor_valor = float("inf")

    def aplicar_limites(self):
        """Aplica clipping de posición y devuelve máscara de colisión (dim,)"""
        bajo = self.limites[:, 0]
        alto = self.limites[:, 1]
        colision = (self.posicion < bajo) | (self.posicion > alto)
        self.posicion = np.minimum(np.maximum(self.posicion, bajo), alto)
        return colision


class OptimizadorPSO:
    """
    Implementación de PSO (global-best).

    Ejemplo de uso:
        optim = OptimizadorPSO(funcion_objetivo, dim=2, limites=lim)
        mejor_pos, mejor_val, historial, posiciones_finales = optim.optimizar()
    """

    def __init__(
        self,
        funcion_objetivo: Callable[[np.ndarray], float],
        dim: int,
        limites: np.ndarray,
        n_particulas: int = 40,
        iter_max: int = 200,
        w_inicio: float = 0.9,
        w_fin: float = 0.4,
        c1: float = 1.7,
        c2: float = 1.7,
        semilla: int = 0,
    ):
        self.funcion = funcion_objetivo
        self.dim = dim
        self.limites = limites
        self.n_particulas = n_particulas
        self.iter_max = iter_max
        self.w_inicio = w_inicio
        self.w_fin = w_fin
        self.c1 = c1
        self.c2 = c2
        self.rng = np.random.default_rng(semilla)

        self._inicializar_particulas()
        self.historial: List[float] = []

    def _inicializar_particulas(self):
        """Crea partículas y establece pbest/gbest iniciales."""
        self.enjambre = [Particula(self.dim, self.limites, self.rng) for _ in range(self.n_particulas)]
        for p in self.enjambre:
            val = self.funcion(p.posicion)
            p.mejor_valor = val
            p.mejor_posicion = p.posicion.copy()

        idx_mejor = int(np.argmin([p.mejor_valor for p in self.enjambre]))
        self.mejor_global_posicion = self.enjambre[idx_mejor].mejor_posicion.copy()
        self.mejor_global_valor = self.enjambre[idx_mejor].mejor_valor

    def _actualizar_velocidad_posicion(self, particula: Particula, w: float):
        """Actualiza velocidad y posición de una partícula con PSO estándar."""
        r1 = self.rng.random(self.dim)
        r2 = self.rng.random(self.dim)
        parte_cognitiva = self.c1 * r1 * (particula.mejor_posicion - particula.posicion)
        parte_social = self.c2 * r2 * (self.mejor_global_posicion - particula.posicion)

        particula.velocidad = w * particula.velocidad + parte_cognitiva + parte_social
        particula.posicion = particula.posicion + particula.velocidad

        # si colisiona con límites, aplicar clipping y amortiguar velocidad (rebote)
        col = particula.aplicar_limites()
        if np.any(col):
            particula.velocidad[col] *= -0.5

    def optimizar(self, verboso: bool = False) -> Tuple[np.ndarray, float, List[float], np.ndarray]:
        """
        Ejecuta el algoritmo PSO.

        :param verboso: imprime progreso si True
        :return: (mejor_posicion, mejor_valor, historial_mejores, posiciones_finales_enjambre)
        """
        self.historial = []
        for t in range(self.iter_max):
            # inercia con decaimiento lineal
            w = self.w_inicio + (self.w_fin - self.w_inicio) * (t / max(1, self.iter_max - 1))
            for p in self.enjambre:
                self._actualizar_velocidad_posicion(p, w)
                valor = self.funcion(p.posicion)
                # actualizar pbest
                if valor < p.mejor_valor:
                    p.mejor_valor = valor
                    p.mejor_posicion = p.posicion.copy()

            # actualizar gbest
            idx_mejor = int(np.argmin([p.mejor_valor for p in self.enjambre]))
            if self.enjambre[idx_mejor].mejor_valor < self.mejor_global_valor:
                self.mejor_global_valor = self.enjambre[idx_mejor].mejor_valor
                self.mejor_global_posicion = self.enjambre[idx_mejor].mejor_posicion.copy()

            self.historial.append(self.mejor_global_valor)

            if verboso and (t % max(1, self.iter_max // 10) == 0):
                print(f"[PSO] Iteración {t+1}/{self.iter_max} - mejor f = {self.mejor_global_valor:.6e}")

        posiciones_finales = np.vstack([p.posicion for p in self.enjambre])
        return self.mejor_global_posicion, self.mejor_global_valor, self.historial, posiciones_finales

    def obtener_historial(self) -> List[float]:
        """Devuelve el historial de mejor valor por iteración."""
        return self.historial
