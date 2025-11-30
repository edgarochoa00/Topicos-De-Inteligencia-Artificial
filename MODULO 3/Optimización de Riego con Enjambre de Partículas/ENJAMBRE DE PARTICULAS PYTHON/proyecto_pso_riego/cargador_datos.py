# -*- coding: utf-8 -*-
"""
cargador_datos.py
-----------------
Versión 9.0 - Corrige lectura y escala numérica de coordenadas.
Asegura rangos realistas (25–26 lat, -109–-107 lon) para Guasave, Sinaloa.
"""

import pandas as pd
import csv
import re

class CargadorDatos:
    """Clase para cargar, limpiar y validar los datos del CSV."""

    def __init__(self, ruta_csv: str):
        self.ruta_csv = ruta_csv
        self.df = None

    def _detectar_delimitador(self):
        """Detecta automáticamente el delimitador del archivo CSV."""
        with open(self.ruta_csv, "r", encoding="utf-8", errors="ignore") as f:
            muestra = f.read(2048)
            sniffer = csv.Sniffer()
            try:
                return sniffer.sniff(muestra).delimiter
            except csv.Error:
                return ","

    def _extraer_numero(self, texto):
        """Extrae el primer número decimal válido dentro de un texto."""
        if pd.isna(texto):
            return None
        texto = str(texto).replace(",", ".")
        match = re.search(r"-?\d+\.\d+", texto)
        if match:
            return float(match.group())
        match = re.search(r"-?\d+", texto)
        if match:
            return float(match.group())
        return None

    def cargar_csv(self) -> pd.DataFrame:
        """Carga el CSV y corrige las coordenadas con regex."""
        delimitador = self._detectar_delimitador()
        print(f"[INFO] Delimitador detectado: '{delimitador}'")

        # Leer el CSV sin forzar tipos
        df = pd.read_csv(self.ruta_csv, delimiter=delimitador, encoding="utf-8", dtype=str, on_bad_lines="skip")

        print("\n[INFO] Columnas detectadas:")
        print(list(df.columns))

        # Normalizar nombres de columnas
        df.columns = [c.strip().lower().replace(" ", "_").replace("(", "").replace(")", "").replace("°", "") for c in df.columns]

        # Equivalencias comunes
        equivalencias = {
            "humedad_%": "humedad",
            "humedad": "humedad",
            "cultivo": "cultivo",
            "elevación_m": "elevacion",
            "elevacion_m": "elevacion",
            "salinidad_dsm": "salinidad",
            "salinidad": "salinidad",
            "temperatura_c": "temperatura",
            "temperatura": "temperatura",
            "latitud": "latitud",
            "longitud": "longitud"
        }
        df.rename(columns=lambda c: equivalencias.get(c, c), inplace=True)

        # Limpiar columnas numéricas básicas
        for col in ["humedad", "elevacion", "salinidad", "temperatura"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Extraer números de latitud y longitud
        if "latitud" in df.columns and "longitud" in df.columns:
            df["latitud"] = df["latitud"].apply(self._extraer_numero)
            df["longitud"] = df["longitud"].apply(self._extraer_numero)

        # Filtrar coordenadas realistas (Guasave ≈ lat 24–27, lon -110 a -105)
        df = df.dropna(subset=["latitud", "longitud"])
        df = df[(df["latitud"].between(24, 27)) & (df["longitud"].between(-110, -105))]

        print("\n[INFO] Primeras filas corregidas:")
        print(df.head(5))

        registros_validos = len(df)
        print(f"\n Datos cargados correctamente: {registros_validos} registros válidos.")

        if registros_validos > 0:
            print(f"\n[INFO] Rango de latitud: {df['latitud'].min()} – {df['latitud'].max()}")
            print(f"[INFO] Rango de longitud: {df['longitud'].min()} – {df['longitud'].max()}")

        self.df = df.reset_index(drop=True)
        return self.df

    def obtener_limites(self, margen: float = 0.01):
        """Devuelve los límites geográficos del conjunto de datos."""
        if self.df is None or self.df.empty:
            raise ValueError("No hay datos cargados. Ejecuta 'cargar_csv()' primero.")

        lat_min = self.df["latitud"].min() - margen
        lat_max = self.df["latitud"].max() + margen
        lon_min = self.df["longitud"].min() - margen
        lon_max = self.df["longitud"].max() + margen

        return (float(lat_min), float(lat_max), float(lon_min), float(lon_max))
