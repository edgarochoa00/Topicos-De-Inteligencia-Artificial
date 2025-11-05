# algoritmo_genetico_tsp.py
# ------------------------------------------------------------
# Implementación de un Algoritmo Genético para el TSP:
# - Representación: una ruta es una permutación de índices de ciudades.
# - Aptitud: inversa de la distancia total de la ruta cerrada.
# - Selección: torneo.
# - Cruce: OX (Order Crossover).
# - Mutación: intercambio (swap) o inversión de segmento.
# - Reemplazo: generacional con elitismo.
# ------------------------------------------------------------

from typing import List, Tuple
import numpy as np
import random


Ruta = List[int]


def distancia_ruta(ruta: Ruta, D: np.ndarray) -> float:
    """
    Calcula la distancia total (km) de una ruta cerrada (regresa al origen).

    Parámetros:
        ruta: lista de índices de ciudades (orden de visita).
        D: matriz de distancias (km) entre ciudades.

    Retorna:
        Distancia total en km.
    """
    total = 0.0
    n = len(ruta)
    for i in range(n):
        a = ruta[i]
        b = ruta[(i + 1) % n]
        total += D[a, b]
    return total


def aptitud(ruta: Ruta, D: np.ndarray) -> float:
    """
    Calcula la aptitud como el inverso de la distancia total.
    Se agrega un pequeño término para evitar división por cero.

    Parámetros:
        ruta: ruta a evaluar.
        D: matriz de distancias.

    Retorna:
        Valor de aptitud (mayor es mejor).
    """
    return 1.0 / (1e-12 + distancia_ruta(ruta, D))


def seleccion_torneo(poblacion: List[Ruta],
                     D: np.ndarray,
                     k: int = 3,
                     rng: random.Random = random) -> Ruta:
    """
    Selección por torneo: elige k individuos al azar y devuelve
    una copia del mejor (menor distancia).
    """
    candidatos = rng.sample(poblacion, k=min(k, len(poblacion)))
    candidatos.sort(key=lambda r: distancia_ruta(r, D))
    return candidatos[0][:]


def cruce_ox(padre1: Ruta, padre2: Ruta, rng: random.Random = random) -> Ruta:
    """
    Cruce OX (Order Crossover):
    - Copia un segmento contiguo del padre1.
    - Completa los huecos manteniendo el orden relativo del padre2.
    """
    n = len(padre1)
    a, b = sorted(rng.sample(range(n), 2))
    hijo = [-1] * n

    # Copiar segmento del padre1
    hijo[a:b+1] = padre1[a:b+1]

    # Completar con el orden del padre2
    restos = [x for x in padre2 if x not in hijo]
    j = 0
    for i in range(n):
        if hijo[i] == -1:
            hijo[i] = restos[j]
            j += 1
    return hijo


def mutacion_intercambio(ruta: Ruta, rng: random.Random = random) -> None:
    """
    Mutación por intercambio de dos posiciones.
    Modifica la ruta en el lugar.
    """
    i, j = rng.sample(range(len(ruta)), 2)
    ruta[i], ruta[j] = ruta[j], ruta[i]


def mutacion_inversion(ruta: Ruta, rng: random.Random = random) -> None:
    """
    Mutación por inversión de un segmento [a, b].
    Modifica la ruta en el lugar.
    """
    a, b = sorted(rng.sample(range(len(ruta)), 2))
    ruta[a:b+1] = reversed(ruta[a:b+1])


def crear_poblacion_inicial(tamano: int,
                            n_ciudades: int,
                            rng: random.Random = random) -> List[Ruta]:
    """
    Crea una población inicial de rutas aleatorias (permutaciones).
    """
    base = list(range(n_ciudades))
    poblacion = []
    for _ in range(tamano):
        r = base[:]
        rng.shuffle(r)
        poblacion.append(r)
    return poblacion


def evolucionar_tsp_ag(
    D: np.ndarray,
    tamano_poblacion: int = 150,
    generaciones: int = 500,
    torneo_k: int = 3,
    prob_cruce: float = 0.9,
    prob_mutacion: float = 0.25,
    tipo_mutacion: str = "inversion",  # "inversion" o "intercambio"
    elitismo: int = 2,
    semilla: int = 42,
) -> Tuple[Ruta, float, List[float]]:
    """
    Ejecuta el Algoritmo Genético para TSP.

    Parámetros:
        D: matriz de distancias (km) entre ciudades.
        tamano_poblacion: número de individuos en la población.
        generaciones: número de iteraciones evolutivas.
        torneo_k: tamaño del torneo para selección.
        prob_cruce: probabilidad de aplicar cruce OX.
        prob_mutacion: probabilidad de aplicar mutación.
        tipo_mutacion: "inversion" o "intercambio".
        elitismo: número de mejores individuos que se copian directamente.
        semilla: semilla para reproducibilidad.

    Retorna:
        mejor_ruta: lista de índices de ciudades (orden óptimo encontrado).
        mejor_distancia: distancia total (km) de la mejor_ruta.
        historial_mejor: lista con la mejor distancia por generación.
    """
    rng = random.Random(semilla)
    n = D.shape[0]

    poblacion = crear_poblacion_inicial(tamano_poblacion, n, rng)
    poblacion.sort(key=lambda r: distancia_ruta(r, D))
    mejor_ruta = poblacion[0][:]
    mejor_distancia = distancia_ruta(mejor_ruta, D)
    historial_mejor = [mejor_distancia]

    for _ in range(generaciones):
        # Elitismo
        nueva_poblacion: List[Ruta] = [r[:] for r in poblacion[:elitismo]]

        # Reproducción
        while len(nueva_poblacion) < tamano_poblacion:
            padre1 = seleccion_torneo(poblacion, D, k=torneo_k, rng=rng)
            padre2 = seleccion_torneo(poblacion, D, k=torneo_k, rng=rng)

            # Cruce
            if rng.random() < prob_cruce:
                hijo = cruce_ox(padre1, padre2, rng=rng)
            else:
                hijo = padre1[:]

            # Mutación
            if rng.random() < prob_mutacion:
                if tipo_mutacion == "intercambio":
                    mutacion_intercambio(hijo, rng=rng)
                else:
                    mutacion_inversion(hijo, rng=rng)

            nueva_poblacion.append(hijo)

        # Reemplazo
        poblacion = nueva_poblacion
        poblacion.sort(key=lambda r: distancia_ruta(r, D))

        # Actualizar mejor global
        dist_actual = distancia_ruta(poblacion[0], D)
        if dist_actual < mejor_distancia:
            mejor_distancia = dist_actual
            mejor_ruta = poblacion[0][:]

        historial_mejor.append(mejor_distancia)

    return mejor_ruta, mejor_distancia, historial_mejor
