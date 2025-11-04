# -*- coding: utf-8 -*-
"""
visualizacion.py
----------------
Funciones para mostrar los resultados gráficamente.
"""

import matplotlib.pyplot as plt

def graficar_resultado(sensores, puntos):
    plt.figure(figsize=(8, 7))
    plt.scatter(puntos["longitud"], puntos["latitud"], s=20, alpha=0.6, label="Puntos de cultivo")
    plt.scatter(sensores[:, 1], sensores[:, 0], s=80, color="red", marker="^", label="Sensores óptimos", edgecolors="black")
    plt.xlabel("Longitud")
    plt.ylabel("Latitud")
    plt.title("Optimización de ubicación de sensores (PSO)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
