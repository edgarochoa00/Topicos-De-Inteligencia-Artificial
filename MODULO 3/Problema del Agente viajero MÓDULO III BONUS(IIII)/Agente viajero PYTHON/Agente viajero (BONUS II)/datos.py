# datos.py
# ------------------------------------------------------------
# Definición del grafo según el esquema compartido,
# construcción de la matriz de distancias completa mediante
# el algoritmo de Floyd–Warshall (caminos mínimos),
# y un diseño de coordenadas aproximadas para graficar.
# ------------------------------------------------------------

from typing import Dict, List, Tuple
import numpy as np


def obtener_ciudades() -> List[str]:
    """
    Devuelve la lista de ciudades en un orden fijo para indexación.
    """
    return [
        "Londres",
        "Dublín",
        "Madrid",
        "Atenas",
        "París",
        "Varsovia",
        "Moscú",
    ]


def obtener_aristas() -> List[Tuple[str, str, float]]:
    """
    Devuelve la lista de aristas no dirigidas (ciudad_a, ciudad_b, distancia_km)
    extraídas del esquema provisto. Solo se incluyen conexiones visibles.
    """
    E = []
    agregar = E.append

    # Conexiones del esquema (distancias en km):
    agregar(("Londres", "Dublín", 463.0))
    agregar(("Londres", "París", 344.0))
    agregar(("Londres", "Varsovia", 344.0))
    agregar(("Dublín", "Madrid", 1053.0))
    agregar(("Madrid", "París", 1053.0))
    agregar(("París", "Atenas", 1053.0))
    agregar(("Atenas", "Moscú", 1053.0))
    agregar(("Varsovia", "Moscú", 1152.0))

    return E


def obtener_diseno() -> Dict[str, Tuple[float, float]]:
    """
    Devuelve un diccionario {ciudad: (x, y)} con coordenadas aproximadas
    para graficar la ruta en un plano 2D similar al esquema (no geográficas).
    """
    return {
        "Londres":  (0.0, 1.0),
        "Dublín":   (-1.1, 0.9),
        "Madrid":   (-1.0, -0.2),
        "París":    (-0.1, 0.5),
        "Varsovia": (1.0, 0.8),
        "Moscú":    (1.6, 0.2),
        "Atenas":   (0.5, -0.5),
    }


def construir_matriz_todos_con_todos() -> Tuple[np.ndarray, Dict[str, int]]:
    """
    Construye una matriz de distancias completa (simétrica) usando Floyd–Warshall
    sobre el grafo esparso del esquema. Así, si dos ciudades no tienen arista
    directa, su distancia se calcula por el camino mínimo.

    Retorna:
        D: np.ndarray (n, n) con distancias mínimas en km.
        indice: dict {nombre_ciudad: indice_entero}
    """
    ciudades = obtener_ciudades()
    indice = {c: i for i, c in enumerate(ciudades)}
    n = len(ciudades)
    INF = 1e18

    # Inicialización de la matriz de distancias
    D = np.full((n, n), INF, dtype=float)
    for i in range(n):
        D[i, i] = 0.0

    # Cargar aristas no dirigidas
    for a, b, w in obtener_aristas():
        i, j = indice[a], indice[b]
        if w < D[i, j]:
            D[i, j] = w
            D[j, i] = w

    # Floyd–Warshall para completar todos los pares
    for k in range(n):
        for i in range(n):
            via_k = D[i, k] + D[k, :]
            mask = via_k < D[i, :]
            D[i, mask] = via_k[mask]

    return D, indice


if __name__ == "__main__":
    D, idx = construir_matriz_todos_con_todos()
    ciudades = obtener_ciudades()
    print("Índices de ciudades:", idx)
    print("Matriz de distancias (km):")
    with np.printoptions(precision=1, suppress=True):
        print(D)
