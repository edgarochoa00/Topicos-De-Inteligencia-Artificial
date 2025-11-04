# -*- coding: utf-8 -*-
"""
config.py
---------
Configuración general del algoritmo PSO.
"""

class ConfiguracionPSO:
    """Contiene los parámetros globales del algoritmo PSO."""

    def __init__(self):
        self.tamano_enjambre = 40
        self.iteraciones_max = 150
        self.w_inercia = 0.72
        self.c_cognitivo = 1.49
        self.c_social = 1.49
        self.velocidad_max = 0.015
        self.numero_sensores = 12
        self.radio_influencia_m = 350.0
        self.distancia_minima_m = 120.0
        self.costo_por_sensor = 1.0
        self.peso_cobertura = 1.0
        self.peso_costo = 0.12
        self.semilla = 42
