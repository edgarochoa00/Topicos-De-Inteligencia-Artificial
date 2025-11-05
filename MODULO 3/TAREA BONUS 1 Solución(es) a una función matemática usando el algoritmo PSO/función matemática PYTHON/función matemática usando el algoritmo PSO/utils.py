import numpy as np
import matplotlib.pyplot as plt

def graficar_convergencia(historial, ruta_guardado):
#    Grafica la curva de convergencia (mejor valor vs iteración).
    plt.figure(figsize=(8, 5))
    plt.semilogy(range(1, len(historial) + 1), historial)
    plt.xlabel("Iteración")
    plt.ylabel("Mejor valor f(x) (escala log)")
    plt.title("Convergencia del algoritmo")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(ruta_guardado, dpi=150)
    plt.close()

def graficar_posiciones_finales(posiciones, mejor, limites, ruta_guardado):
#   Grafica posiciones finales sobre contornos (solo válido para 2D).
    if posiciones.shape[1] != 2:
        raise ValueError("Solo se puede graficar en 2D.")

    xs = np.linspace(limites[0, 0], limites[0, 1], 200)
    ys = np.linspace(limites[1, 0], limites[1, 1], 200)
    X, Y = np.meshgrid(xs, ys)
    Z = 10 * 2 + (X**2 - 10*np.cos(2*np.pi*X)) + (Y**2 - 10*np.cos(2*np.pi*Y))

    plt.figure(figsize=(7, 6))
    plt.contour(X, Y, Z, levels=30, alpha=0.7)
    plt.scatter(posiciones[:, 0], posiciones[:, 1], s=25, label="Partículas finales")
    plt.plot(mejor[0], mejor[1], 'r*', markersize=12, label="Mejor global")
    plt.legend()
    plt.xlabel("x₁")
    plt.ylabel("x₂")
    plt.title("Posiciones finales del enjambre/población")
    plt.tight_layout()
    plt.savefig(ruta_guardado, dpi=150)
    plt.close()
