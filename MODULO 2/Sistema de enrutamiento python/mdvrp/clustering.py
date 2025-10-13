# mdvrp/clustering.py
"""
Asignación y clustering de tiendas a Centros de Distribución.
"""

import numpy as np


class StoreAssigner:
    """
    Asigna cada tienda al Centro de Distribución más cercano.
    """

    @staticmethod
    def assign_stores_to_depots(df_depots, df_stores, distance_matrix):
        depot_indices = df_depots.index.tolist()
        store_indices = df_stores.index.tolist()

        assignments = {dep: [] for dep in depot_indices}
        for store in store_indices:
            distances = [distance_matrix[store, dep] for dep in depot_indices]
            nearest_depot = depot_indices[int(np.argmin(distances))]
            assignments[nearest_depot].append(store)

        return assignments


class CapacityClusterer:
    """
    Agrupa las tiendas de cada CD en rutas según la capacidad del vehículo.
    """

    @staticmethod
    def cluster_by_capacity(df_stores, assignments, vehicle_capacity):
        clusters = {}
        for depot, stores in assignments.items():
            depot_clusters = []
            current_cluster = []
            current_demand = 0

            for store in stores:
                demand = df_stores.loc[store, "Capacidad_Venta"]
                if current_demand + demand <= vehicle_capacity:
                    current_cluster.append(store)
                    current_demand += demand
                else:
                    depot_clusters.append(current_cluster)
                    current_cluster = [store]
                    current_demand = demand

            if current_cluster:
                depot_clusters.append(current_cluster)

            clusters[depot] = depot_clusters

        return clusters
