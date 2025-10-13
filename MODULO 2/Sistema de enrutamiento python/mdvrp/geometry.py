import math
import numpy as np
import pandas as pd
from typing import List


class GeometryCalculator:
    """Calculadora de métricas geométricas y de ruta"""

    @staticmethod
    def calculate_angle_from_depot(df: pd.DataFrame, depot_idx: int, node_idx: int) -> float:
        """
        Calcula el ángulo polar de un nodo respecto a un depósito
        Útil para ordenamiento angular en clustering.
        """
        delta_y = df.at[node_idx, "lat"] - df.at[depot_idx, "lat"]
        delta_x = df.at[node_idx, "lon"] - df.at[depot_idx, "lon"]
        return math.atan2(delta_y, delta_x)

    @staticmethod
    def route_fuel_cost(fuel_matrix: np.ndarray, route: List[int]) -> float:
        """
        Calcula el costo total de combustible de una ruta.
        Args:
            fuel_matrix: Matriz de costos de combustible
            route: Lista de índices (incluye depósito al inicio y final)
        Returns:
            Costo total de combustible
        """
        return sum(fuel_matrix[route[i], route[i + 1]] for i in range(len(route) - 1))

    @staticmethod
    def route_distance(distance_matrix: np.ndarray, route: List[int]) -> float:
        """
        Calcula la distancia total recorrida por una ruta.
        Args:
            distance_matrix: Matriz de distancias
            route: Secuencia de nodos (incluye depósito)
        Returns:
            Distancia total en kilómetros
        """
        return sum(distance_matrix[route[i], route[i + 1]] for i in range(len(route) - 1))

    @staticmethod
    def route_time(distance_km: float, num_stores: int, speed_kmh: float, service_time_hours: float) -> float:
        """
        Calcula el tiempo total estimado de la ruta.
        Args:
            distance_km: Distancia total de la ruta
            num_stores: Número de tiendas en la ruta
            speed_kmh: Velocidad promedio (km/h)
            service_time_hours: Tiempo de servicio por tienda (horas)
        Returns:
            Tiempo total en horas
        """
        travel_time = distance_km / speed_kmh
        service_time_total = num_stores * service_time_hours
        return travel_time + service_time_total
