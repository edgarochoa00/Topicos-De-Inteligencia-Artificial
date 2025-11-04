# -*- coding: utf-8 -*-
"""
main.py
-------
Programa principal para optimizar la ubicación de sensores de riego
mediante el algoritmo de Enjambre de Partículas (PSO).
"""

import numpy as np
import csv
import os
from config import ConfiguracionPSO
from cargador_datos import CargadorDatos
from funciones_aptitud import funcion_aptitud
from pso import PSO
from visualizacion import graficar_resultado


def guardar_resultados_csv(sensores, mejor_val, cfg):
    """
    Guarda los resultados del algoritmo PSO en un archivo CSV dentro de la carpeta /resultados.
    Incluye manejo de nombres de atributos variables para compatibilidad.
    """
    os.makedirs("resultados", exist_ok=True)
    ruta_salida = os.path.join("resultados", "resultados_pso.csv")

    # Intentar obtener nombres de atributos aunque varíen
    num_particulas = getattr(cfg, "num_particulas", getattr(cfg, "numero_particulas", getattr(cfg, "n_particulas", "N/D")))
    iteraciones = getattr(cfg, "iteraciones", "N/D")
    numero_sensores = getattr(cfg, "numero_sensores", getattr(cfg, "num_sensores", "N/D"))
    c1 = getattr(cfg, "c1", "N/D")
    c2 = getattr(cfg, "c2", "N/D")
    w = getattr(cfg, "w", getattr(cfg, "inercia", "N/D"))

    with open(ruta_salida, mode="w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["# Resultados del algoritmo PSO - Optimización de Riego"])
        escritor.writerow(["Mejor valor de aptitud", round(mejor_val, 6)])
        escritor.writerow([])
        escritor.writerow(["Parámetros del algoritmo"])
        escritor.writerow(["Número de partículas", num_particulas])
        escritor.writerow(["Iteraciones", iteraciones])
        escritor.writerow(["Número de sensores", numero_sensores])
        escritor.writerow(["Coeficiente cognitivo (c1)", c1])
        escritor.writerow(["Coeficiente social (c2)", c2])
        escritor.writerow(["Factor de inercia (w)", w])
        escritor.writerow([])
        escritor.writerow(["Sensor", "Latitud", "Longitud"])

        for i, (lat, lon) in enumerate(sensores, start=1):
            escritor.writerow([f"Sensor {i}", round(lat, 6), round(lon, 6)])

    print(f"\n Resultados guardados en: {ruta_salida}")


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
    print(f"Sensores óptimos:\n")
    for i, (lat, lon) in enumerate(sensores, start=1):
        print(f"Sensor {i:02d} -> lat={lat:.6f}, lon={lon:.6f}")

    # 7. Guardar resultados en CSV
    guardar_resultados_csv(sensores, mejor_val, cfg)

    # 8. Visualización de resultados
    print("\nGenerando gráfico de resultados...")
    graficar_resultado(sensores, puntos)

    print("\nProceso completado con éxito.")


# Ejecutar solo si este archivo se llama directamente
if __name__ == "__main__":
    main()
