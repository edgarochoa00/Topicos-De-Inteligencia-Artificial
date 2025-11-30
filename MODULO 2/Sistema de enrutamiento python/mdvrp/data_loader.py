# mdvrp/data_loader.py
"""
Carga y validación de datos. Lee:
- distribucion.xlsx (ubicaciones y, opcionalmente, rutas prediseñadas)
- matriz_distancias.xlsx (N x N)
- matriz_costos_combustible.xlsx (N x N)
Permite rutas prediseñadas si existen columnas Ruta_Predisenada / Orden_Ruta.
"""

import pandas as pd
import numpy as np


class DataLoader:
    def __init__(self, config):
        self.config = config

    def load_data(self):
        print("[1/6] Cargando datos...")

        # === 1) DISTRIBUCIÓN ===
        df = pd.read_excel(self.config.data_file).copy()

        # Normalizar Tipo
        if "Tipo" not in df.columns:
            raise ValueError("⚠️ No se encuentra la columna 'Tipo' en distribucion.xlsx")
        df["Tipo"] = df["Tipo"].astype(str).str.strip().str.lower()

        # Coordenadas y demanda
        def col_or_fail(name): 
            if name not in df.columns:
                raise ValueError(f"⚠️ Falta la columna '{name}' en distribucion.xlsx")
            return name

        lat_col = col_or_fail("Latitud_WGS84")
        lon_col = col_or_fail("Longitud_WGS84")
        name_col = col_or_fail("Nombre")
        demand_col = col_or_fail("Capacidad_Venta")

        # Índices alineados a matrices
        df["idx"] = np.arange(len(df))
        df["lat"] = df[lat_col] / 1e6
        df["lon"] = df[lon_col] / 1e6
        is_store = ~df["Tipo"].str.contains("distribuci")  # todo lo que no sea CD es tienda
        df["demanda"] = np.where(is_store, df[demand_col].fillna(0).astype(float), 0.0)

        df_depots = df[~is_store].copy()
        df_stores = df[is_store].copy()

        # Rutas prediseñadas (opcionales)
        has_predesigned = (self.config.col_route_name in df.columns)
        if has_predesigned:
            df[self.config.col_route_name] = df[self.config.col_route_name].astype(str)
            if self.config.col_route_order in df.columns:
                df[self.config.col_route_order] = pd.to_numeric(df[self.config.col_route_order], errors="coerce")

        # === 2) MATRICES ===
        # Saltar encabezado tipo "Nodo_1 ... Nodo_N"
        dist_df = pd.read_excel(self.config.distance_matrix_file, header=None, skiprows=1)
        fuel_df = pd.read_excel(self.config.fuel_matrix_file, header=None, skiprows=1)

        # Forzar numérico y limpiar bordes
        dist_df = dist_df.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all").dropna(how="all")
        fuel_df = fuel_df.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all").dropna(how="all")

        n1, n2 = dist_df.shape
        if n1 != n2:
            raise ValueError(f"⚠️ La matriz de distancias no es cuadrada ({n1}x{n2}).")
        if dist_df.shape != fuel_df.shape:
            raise ValueError("⚠️ Distancias y costos de combustible tienen tamaños diferentes.")

        distance_matrix = dist_df.values.astype(float)
        fuel_matrix = fuel_df.values.astype(float)

        # Diagonales a 0
        np.fill_diagonal(distance_matrix, 0.0)
        np.fill_diagonal(fuel_matrix, 0.0)

        print(f"  ✓ Depósitos: {len(df_depots)}")
        print(f"  ✓ Tiendas: {len(df_stores)}")
        print(f"  ✓ Matriz {n1}x{n2}")

        return df, df_depots, df_stores, distance_matrix, fuel_matrix, has_predesigned
