# mdvrp/route_builder.py
"""
Construcción de rutas:
- Prediseñadas (si existen columnas)
- Vecino más cercano (NN) como fallback y para ordenar dentro de grupo
"""

import numpy as np


class RouteBuilder:

    @staticmethod
    def nearest_neighbor_route(depot_idx, stores_idx, distance_matrix):
        if not stores_idx:
            return [depot_idx, depot_idx]

        unvisited = list(stores_idx)
        route = [depot_idx]
        current = depot_idx
        while unvisited:
            nxt = min(unvisited, key=lambda j: distance_matrix[current, j])
            unvisited.remove(nxt)
            route.append(nxt)
            current = nxt
        route.append(depot_idx)
        return route

    @staticmethod
    def route_from_predesigned(depot_idx, stores_idx, df, col_order, distance_matrix):
        """
        Si col_order está presente y tiene valores, ordena por ese campo.
        Si no, usa NN dentro del mismo grupo.
        """
        if not stores_idx:
            return [depot_idx, depot_idx]
        if col_order and col_order in df.columns and df.loc[stores_idx, col_order].notna().any():
            group = df.loc[stores_idx, [col_order, "idx"]].sort_values(by=col_order)
            inner = group["idx"].tolist()
            return [depot_idx] + inner + [depot_idx]
        # Fallback: NN dentro del grupo prediseñado
        return RouteBuilder.nearest_neighbor_route(depot_idx, stores_idx, distance_matrix)
