# main.py
"""
Script principal con menú para seleccionar la función objetivo.
"""

from pso import OptimizadorPSO
from de import EvolucionDiferencial
from benchmarks import crear_limites
from utils import graficar_convergencia, graficar_posiciones_finales

import numpy as np
import os

# === Definición de funciones de prueba ===
def funcion_esfera(x):
    return np.sum(x**2)

def funcion_rosenbrock(x):
    return np.sum(100 * (x[1:] - x[:-1]**2)**2 + (1 - x[:-1])**2)

def funcion_rastrigin(x):
    A = 10
    n = len(x)
    return A * n + np.sum(x**2 - A * np.cos(2 * np.pi * x))

def funcion_ackley(x):
    a, b, c = 20, 0.2, 2 * np.pi
    n = len(x)
    suma1 = np.sum(x**2)
    suma2 = np.sum(np.cos(c * x))
    return -a * np.exp(-b * np.sqrt(suma1 / n)) - np.exp(suma2 / n) + a + np.e

def funcion_griewank(x):
    i = np.arange(1, len(x) + 1)
    return 1 + np.sum(x**2) / 4000 - np.prod(np.cos(x / np.sqrt(i)))


# === Menú de selección ===
def seleccionar_funcion():
    print("\nSeleccione la función a optimizar:")
    print("1) Esfera")
    print("2) Rosenbrock")
    print("3) Rastrigin")
    print("4) Ackley")
    print("5) Griewank")

    while True:
        opcion = input("Ingrese el número de la función (1-5): ").strip()
        if opcion in ["1", "2", "3", "4", "5"]:
            break
        print("⚠️  Opción no válida. Intente de nuevo.")

    if opcion == "1":
        return funcion_esfera, "Esfera", (-5.12, 5.12)
    elif opcion == "2":
        return funcion_rosenbrock, "Rosenbrock", (-2.0, 2.0)
    elif opcion == "3":
        return funcion_rastrigin, "Rastrigin", (-5.12, 5.12)
    elif opcion == "4":
        return funcion_ackley, "Ackley", (-5.0, 5.0)
    else:
        return funcion_griewank, "Griewank", (-5.0, 5.0)


def main():
    # === Menú ===
    funcion_objetivo, nombre_funcion, rango = seleccionar_funcion()
    print(f"\n🔹 Ejecutando PSO y DE sobre la función {nombre_funcion}...\n")

    dim = 2
    limites = crear_limites(dim, rango[0], rango[1])
    carpeta_salida = "resultados"
    os.makedirs(carpeta_salida, exist_ok=True)

    # === Ejecutar PSO ===
    pso = OptimizadorPSO(
        funcion_objetivo=funcion_objetivo,
        dim=dim,
        limites=limites,
        n_particulas=40,
        iter_max=200,
        w_inicio=0.9,
        w_fin=0.4,
        c1=1.7,
        c2=1.7,
        semilla=42,
    )
    mejor_pos_pso, mejor_val_pso, historial_pso, posiciones_pso = pso.optimizar(verboso=True)
    print("=== PSO ===")
    print(f"Mejor posición (PSO): {mejor_pos_pso}")
    print(f"Mejor valor (PSO): {mejor_val_pso:.6e}")

    graficar_convergencia(historial_pso, os.path.join(carpeta_salida, f"{nombre_funcion}_PSO_convergencia.png"))
    graficar_posiciones_finales(posiciones_pso, mejor_pos_pso, limites, os.path.join(carpeta_salida, f"{nombre_funcion}_PSO_posiciones.png"))

    # === Ejecutar DE ===
    de = EvolucionDiferencial(
        funcion_objetivo=funcion_objetivo,
        dim=dim,
        limites=limites,
        tam_poblacion=60,
        iter_max=200,
        F=0.8,
        CR=0.9,
        semilla=123,
    )
    mejor_pos_de, mejor_val_de, historial_de, poblacion_de = de.optimizar(verboso=True)
    print("\n=== DE ===")
    print(f"Mejor posición (DE): {mejor_pos_de}")
    print(f"Mejor valor (DE): {mejor_val_de:.6e}")

    graficar_convergencia(historial_de, os.path.join(carpeta_salida, f"{nombre_funcion}_DE_convergencia.png"))
    graficar_posiciones_finales(poblacion_de, mejor_pos_de, limites, os.path.join(carpeta_salida, f"{nombre_funcion}_DE_posiciones.png"))

    print("\n Optimización terminada")
    print(f"Resultados guardados en la carpeta '{carpeta_salida}/'.")


if __name__ == "__main__":
    main()
