# -*- coding: utf-8 -*-
"""
main.py
-------
Programa principal para optimizar la ubicación de sensores de riego
mediante el algoritmo de Enjambre de Partículas (PSO).
"""

import numpy as np
from config import ConfiguracionPSO
from cargador_datos import CargadorDatos
from funciones_aptitud import funcion_aptitud
from pso import PSO
from visualizacion import graficar_resultado


def main():
    """
    Función principal del proyecto.
    Carga los datos, configura los parámetros, ejecuta el PSO y muestra resultados.
    """

    print("=== OPTIMIZACIÓN DE RIEGO CON ENJAMBRE DE PARTÍCULAS ===")

    # 1. Cargar datos desde CSV
    ruta_csv = "datos_cultivos.csv"
    cargador = CargadorDatos(ruta_csv)
    puntos = cargador.cargar_csv()
    print(f"Datos cargados correctamente: {len(puntos)} registros encontrados.")

    # 2. Crear configuración del algoritmo PSO
    cfg = ConfiguracionPSO()

    # 3. Obtener límites geográficos del área de estudio
    limites = cargador.obtener_limites(margen=0.01)
    print(f"Límites de búsqueda (lat/lon): {limites}")

    # 4. Definir la función de aptitud
    f_aptitud = lambda x: funcion_aptitud(x, puntos, cfg)

    # 5. Crear y ejecutar el optimizador PSO
    print("\nEjecutando optimización PSO, por favor espere...")
    pso = PSO(f_aptitud, cfg, limites)
    mejor_pos, mejor_val = pso.ejecutar()

    # 6. Procesar resultados
    sensores = mejor_pos.reshape(-1, 2)
    print("\n=== RESULTADOS DE OPTIMIZACIÓN ===")
    print(f"Mejor valor de aptitud: {mejor_val:.6f}")
    print(f"Sensores óptimos ({cfg.numero_sensores} total):\n")
    for i, (lat, lon) in enumerate(sensores, start=1):
        print(f"Sensor {i:02d} -> lat={lat:.6f}, lon={lon:.6f}")

    # 7. Visualización de resultados
    print("\nGenerando gráfico de resultados...")
    graficar_resultado(sensores, puntos)

    print("\nProceso completado con éxito.")



# Ejecutar solo si este archivo se llama directamente
if __name__ == "__main__":
    main()
