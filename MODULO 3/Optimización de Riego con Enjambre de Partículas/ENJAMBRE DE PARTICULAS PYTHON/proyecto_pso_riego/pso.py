# -*- coding: utf-8 -*-
"""
pso.py
------
Implementación del algoritmo de optimización por enjambre de partículas (PSO).
"""

import numpy as np

class PSO:
    """Implementa el algoritmo PSO clásico (topología global)."""

    def __init__(self, funcion_aptitud, cfg, limites):
        self.funcion_aptitud = funcion_aptitud
        self.cfg = cfg
        self.limites = limites
        self.rng = np.random.default_rng(cfg.semilla)
        self.dim = cfg.numero_sensores * 2
        self._inicializar()

    def _inicializar(self):
        """Inicializa las partículas dentro de los límites dados."""
        lat_min, lat_max, lon_min, lon_max = self.limites
        self.pos = np.empty((self.cfg.tamano_enjambre, self.dim))
        self.vel = self.rng.uniform(-self.cfg.velocidad_max, self.cfg.velocidad_max,
                                    size=(self.cfg.tamano_enjambre, self.dim))

        for i in range(self.cfg.tamano_enjambre):
            coords = []
            for _ in range(self.cfg.numero_sensores):
                lat = self.rng.uniform(lat_min, lat_max)
                lon = self.rng.uniform(lon_min, lon_max)
                coords.extend([lat, lon])
            self.pos[i, :] = np.array(coords)

        self.pbest_pos = self.pos.copy()
        self.pbest_val = np.array([self.funcion_aptitud(self.pos[i, :]) for i in range(self.cfg.tamano_enjambre)])
        idx = np.argmax(self.pbest_val)
        self.gbest_pos = self.pbest_pos[idx].copy()
        self.gbest_val = self.pbest_val[idx]

    def ejecutar(self):
        """Ejecuta el PSO durante el número máximo de iteraciones."""
        for _ in range(self.cfg.iteraciones_max):
            r1 = self.rng.random(size=self.pos.shape)
            r2 = self.rng.random(size=self.pos.shape)
            cognitivo = self.cfg.c_cognitivo * r1 * (self.pbest_pos - self.pos)
            social = self.cfg.c_social * r2 * (self.gbest_pos - self.pos)
            self.vel = self.cfg.w_inercia * self.vel + cognitivo + social
            self.vel = np.clip(self.vel, -self.cfg.velocidad_max, self.cfg.velocidad_max)
            self.pos += self.vel

            lat_min, lat_max, lon_min, lon_max = self.limites
            self.pos[:, 0::2] = np.clip(self.pos[:, 0::2], lat_min, lat_max)
            self.pos[:, 1::2] = np.clip(self.pos[:, 1::2], lon_min, lon_max)

            for i in range(self.cfg.tamano_enjambre):
                valor = self.funcion_aptitud(self.pos[i, :])
                if valor > self.pbest_val[i]:
                    self.pbest_val[i] = valor
                    self.pbest_pos[i, :] = self.pos[i, :].copy()

                if valor > self.gbest_val:
                    self.gbest_val = valor
                    self.gbest_pos = self.pos[i, :].copy()

        return self.gbest_pos.copy(), float(self.gbest_val)
