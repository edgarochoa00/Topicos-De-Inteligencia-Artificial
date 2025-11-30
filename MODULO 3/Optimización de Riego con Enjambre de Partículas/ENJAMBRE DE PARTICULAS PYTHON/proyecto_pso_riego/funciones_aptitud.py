# -*- coding: utf-8 -*-
"""
funciones_aptitud.py
--------------------
Define la función de aptitud (evaluación) y utilidades para el problema.
"""

import numpy as np
import math

def distancia_haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def ponderacion_cultivo(cultivo):
    cultivo = cultivo.lower()
    if "chile" in cultivo: return 1.15
    elif "tomate" in cultivo: return 1.10
    elif "maíz" in cultivo or "maiz" in cultivo: return 1.00
    return 1.0

def funcion_aptitud(x, puntos, cfg):
    sensores = np.array(x).reshape(-1, 2)
    influencias = []

    for _, p in puntos.iterrows():
        lat_p, lon_p, cultivo = p["latitud"], p["longitud"], p["cultivo"]
        dist_min = min(distancia_haversine(lat_p, lon_p, s[0], s[1]) for s in sensores)
        influencia = math.exp(-dist_min / cfg.radio_influencia_m) * ponderacion_cultivo(cultivo)
        influencias.append(influencia)

    cobertura = np.mean(influencias)
    penalizacion = 0.0

    for i in range(len(sensores)):
        for j in range(i + 1, len(sensores)):
            d = distancia_haversine(sensores[i][0], sensores[i][1], sensores[j][0], sensores[j][1])
            if d < cfg.distancia_minima_m:
                penalizacion += (cfg.distancia_minima_m - d) / cfg.distancia_minima_m

    costo = len(sensores) * cfg.costo_por_sensor
    return cfg.peso_cobertura * cobertura - cfg.peso_costo * costo - 2.0 * penalizacion
