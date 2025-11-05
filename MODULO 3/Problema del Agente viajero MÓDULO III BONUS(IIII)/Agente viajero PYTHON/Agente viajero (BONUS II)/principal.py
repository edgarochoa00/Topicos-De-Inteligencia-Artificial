# principal.py
# ------------------------------------------------------------
# Ejecución de punta a punta:
# - Construye la matriz de distancias (todos-con-todos) desde el grafo.
# - Ejecuta el Algoritmo Genético para el TSP.
# - Imprime resultados clave y guarda las visualizaciones.
# ------------------------------------------------------------

import os
import numpy as np

from datos import construir_matriz_todos_con_todos, obtener_ciudades, obtener_diseno
from algoritmo_genetico_tsp import evolucionar_tsp_ag, distancia_ruta
from graficos import graficar_convergencia, graficar_ruta


def main():
    # 1) Datos
    D, indice = construir_matriz_todos_con_todos()
    ciudades = obtener_ciudades()
    diseno = obtener_diseno()

    # 2) Parámetros del Algoritmo Genético (ajustables)
    parametros = dict(
        tamano_poblacion=200,
        generaciones=600,
        torneo_k=4,
        prob_cruce=0.95,
        prob_mutacion=0.25,
        tipo_mutacion="inversion",  # "inversion" o "intercambio"
        elitismo=2,
        semilla=7,
    )

    # 3) Ejecutar AG
    mejor_ruta, mejor_distancia, historial = evolucionar_tsp_ag(D, **parametros)

    # 4) Resultados
    nombres_ruta = [ciudades[i] for i in mejor_ruta]
    nombres_ruta_cerrada = nombres_ruta + [nombres_ruta[0]]

    print("\n=== Problema del Agente de Viajes (TSP) — Algoritmo Genético ===\n")
    print("Mejor ruta (orden de visita):")
    print(" -> ".join(nombres_ruta_cerrada))
    print(f"\nDistancia total (km): {mejor_distancia:.1f}")

    # Validaciones simples
    assert len(set(mejor_ruta)) == len(ciudades), \
        "La ruta no visita cada ciudad exactamente una vez."
    assert np.isfinite(mejor_distancia), \
        "Se encontró distancia no finita: revise el grafo o la matriz."

    # 5) Salidas gráficas
    os.makedirs("resultados", exist_ok=True)
    graficar_convergencia(historial, "resultados/convergencia_tsp_ag.png")
    graficar_ruta(mejor_ruta, ciudades, diseno, "resultados/ruta_tsp_ag.png")

    print("\nGráficas guardadas en 'resultados/':")
    print(" - convergencia_tsp_ag.png")
    print(" - ruta_tsp_ag.png")
    print("\nEjecución completa.")


if __name__ == "__main__":
    main()
