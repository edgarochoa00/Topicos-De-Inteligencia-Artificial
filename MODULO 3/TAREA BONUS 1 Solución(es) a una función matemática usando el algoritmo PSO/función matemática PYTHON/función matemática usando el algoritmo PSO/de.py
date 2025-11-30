# de.py

# Evolución Diferencial (DE)
# clases, métodos, variables y docstrings.


from typing import Callable, List, Tuple
import numpy as np


class EvolucionDiferencial:
    """
    Implementación básica de DE con estrategia rand/1/bin.
    """

    def __init__(
        self,
        funcion_objetivo: Callable[[np.ndarray], float],
        dim: int,
        limites: np.ndarray,
        tam_poblacion: int = None,
        iter_max: int = 200,
        F: float = 0.8,
        CR: float = 0.9,
        semilla: int = 0,
    ):
        self.funcion = funcion_objetivo
        self.dim = dim
        self.limites = limites
        self.tam_poblacion = tam_poblacion if tam_poblacion is not None else max(10, 10 * dim)
        self.iter_max = iter_max
        self.F = F
        self.CR = CR
        self.rng = np.random.default_rng(semilla)

        self._inicializar_poblacion()
        self.historial: List[float] = []

    def _inicializar_poblacion(self):
        """Crea la población inicial dentro de los límites."""
        bajos = self.limites[:, 0]
        altos = self.limites[:, 1]
        self.poblacion = self.rng.uniform(bajos, altos, size=(self.tam_poblacion, self.dim))
        self.valores = np.array([self.funcion(x) for x in self.poblacion])
        idx = int(np.argmin(self.valores))
        self.mejor_posicion = self.poblacion[idx].copy()
        self.mejor_valor = float(self.valores[idx])

    def _mutacion(self, idx_actual: int) -> np.ndarray:
        """Mutación rand/1: v = x_r1 + F*(x_r2 - x_r3)"""
        indices = list(range(self.tam_poblacion))
        indices.remove(idx_actual)
        r1, r2, r3 = self.rng.choice(indices, size=3, replace=False)
        v = self.poblacion[r1] + self.F * (self.poblacion[r2] - self.poblacion[r3])
        return v

    def _cruce_binomial(self, objetivo: np.ndarray, mutante: np.ndarray) -> np.ndarray:
        """Cruce binomial entre objetivo y mutante, devuelve trial."""
        trial = objetivo.copy()
        jrand = self.rng.integers(0, self.dim)
        for j in range(self.dim):
            if self.rng.random() < self.CR or j == jrand:
                trial[j] = mutante[j]
        # aplicar límites (clip)
        bajos = self.limites[:, 0]
        altos = self.limites[:, 1]
        trial = np.minimum(np.maximum(trial, bajos), altos)
        return trial

    def optimizar(self, verboso: bool = False) -> Tuple[np.ndarray, float, List[float], np.ndarray]:
        """
        Ejecuta DE (rand/1/bin).

        :return: (mejor_posicion, mejor_valor, historial_mejores, poblacion_final)
        """
        self.historial = []
        for t in range(self.iter_max):
            for i in range(self.tam_poblacion):
                mutante = self._mutacion(i)
                trial = self._cruce_binomial(self.poblacion[i], mutante)
                valor_trial = self.funcion(trial)
                # selección 1-a-1
                if valor_trial <= self.valores[i]:
                    self.poblacion[i] = trial
                    self.valores[i] = valor_trial
                    # actualizar global si aplica
                    if valor_trial < self.mejor_valor:
                        self.mejor_valor = valor_trial
                        self.mejor_posicion = trial.copy()

            self.historial.append(self.mejor_valor)
            if verboso and (t % max(1, self.iter_max // 10) == 0):
                print(f"[DE] Iteración {t+1}/{self.iter_max} - mejor f = {self.mejor_valor:.6e}")

        return self.mejor_posicion, self.mejor_valor, self.historial, self.poblacion.copy()

    def obtener_historial(self) -> List[float]:
        return self.historial
