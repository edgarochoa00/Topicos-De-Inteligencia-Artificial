# graficos.py
# ------------------------------------------------------------
# Funciones de visualización:
# - Curva de convergencia (mejor distancia vs generación).
# - Ruta óptima sobre un plano con coordenadas aproximadas.
# ------------------------------------------------------------

from typing import Dict, Tuple, List
import numpy as np
import matplotlib.pyplot as plt


def graficar_convergencia(historial: List[float], ruta_salida: str) -> None:
    """
    Genera y guarda la gráfica de convergencia del algoritmo genético.

    Parámetros:
        historial: lista con la mejor distancia por generación.
        ruta_salida: nombre de archivo de imagen (PNG).
    """
    plt.figure(figsize=(7, 4.2))
    plt.plot(range(len(historial)), historial, linewidth=2)
    plt.xlabel("Generación")
    plt.ylabel("Mejor distancia (km)")
    plt.title("Convergencia del Algoritmo Genético (TSP)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=150)
    plt.close()


def graficar_ruta(
    orden: List[int],
    ciudades: List[str],
    diseno: Dict[str, Tuple[float, float]],
    ruta_salida: str
) -> None:
    """
    Dibuja la ruta óptima encontrada sobre un plano 2D usando
    coordenadas aproximadas del esquema.

    Parámetros:
        orden: lista de índices de ciudades en el orden de visita.
        ciudades: lista de nombres de ciudades.
        diseno: diccionario {ciudad: (x, y)} con coordenadas aproximadas.
        ruta_salida: nombre de archivo de imagen (PNG).
    """
    xs, ys = [], []
    for i in orden + [orden[0]]:  # cerrar el ciclo
        x, y = diseno[ciudades[i]]
        xs.append(x)
        ys.append(y)

    plt.figure(figsize=(6.4, 5.6))
    plt.plot(xs, ys, "-o", linewidth=2, markersize=6)
    for i, ciudad in enumerate(ciudades):
        x, y = diseno[ciudad]
        plt.text(x + 0.03, y + 0.02, ciudad, fontsize=9)
    plt.title("Ruta óptima encontrada (esquema)")
    plt.axis("equal")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=150)
    plt.close()
