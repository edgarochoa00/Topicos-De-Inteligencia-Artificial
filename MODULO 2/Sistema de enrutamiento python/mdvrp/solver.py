# mdvrp/solver.py
"""
Orquestador MDVRP:
- Carga datos (ya hecho en main)
- Capacidad vehículo
- Si hay rutas prediseñadas: las respeta por CD y grupo; si no, usa asignación+clustering
- Para cada grupo/ruta: evalúa Prediseñada (o NN) vs SA y ELIGE la mejor por combustible
- Imprime informe estilo auditoría + retorna OptimizationResults
"""

import numpy as np
from collections import defaultdict

from .config import OptimizationResults, OptimizationConfig, RouteComparison
from .clustering import StoreAssigner, CapacityClusterer
from .route_builder import RouteBuilder
from .optimizer import SimulatedAnnealingOptimizer


class MDVRPSolver:
    def __init__(self, config: OptimizationConfig, df, df_depots, df_stores, D, C, has_predesigned: bool):
        self.cfg = config
        self.df = df
        self.df_depots = df_depots
        self.df_stores = df_stores
        self.D = D
        self.C = C
        self.has_predesigned = has_predesigned

    def _vehicle_capacity(self):
        print("\n[2/6] Calculando capacidad de vehículos...")
        p50 = float(np.percentile(self.df_stores["demanda"], 50))
        p80 = float(np.percentile(self.df_stores["demanda"], 80))
        cap = max(self.cfg.capacity_multiplier_p50 * p50,
                  self.cfg.capacity_multiplier_p80 * p80)
        cap = round(cap, 0)
        print(f"  ✓ Demanda mediana (p50): {p50:.2f}")
        print(f"  ✓ Demanda p80: {p80:.2f}")
        print(f"  ✓ Capacidad vehículo: {cap:.2f}")
        return cap

    def _assignment_or_groups(self):
        print("\n[3/6] Asignando tiendas a depósitos...")

        if self.has_predesigned and self.cfg.col_route_name in self.df.columns:
            # Agrupar por CD y Ruta_Predisenada
            # Detectamos depósitos por Tipo
            depots_idx = self.df_depots["idx"].tolist()
            groups = defaultdict(list)  # (depot_idx, route_name) -> [store_idx]

            # map de nombre depósito -> idx (elige el más cercano por distancia por seguridad)
            # asume que cada tienda se asigna al CD de menor distancia si no hay mapping explícito
            for _, row in self.df[self.df["demanda"] > 0].iterrows():
                store_idx = int(row["idx"])
                # deposit nearest:
                nearest_depot = min(depots_idx, key=lambda di: self.D[store_idx, di])
                route_name = str(row[self.cfg.col_route_name])
                groups[(nearest_depot, route_name)].append(store_idx)

            # imprimir conteo por CD
            by_depot_count = defaultdict(int)
            for (depot_idx, _), stores in groups.items():
                by_depot_count[depot_idx] += len(stores)

            for depot_idx, count in by_depot_count.items():
                print(f"  ✓ {self.df.loc[depot_idx, 'Nombre']}: {count} tiendas")

            return groups, True  # True indica que ya vienen agrupadas

        # Fallback: asignación por costo (combustible/distancia) y clustering por capacidad
        depots_idx = self.df_depots["idx"].tolist()
        stores_idx = self.df_stores["idx"].tolist()

        # Asignar por depósito más cercano (en distancia)
        assignment = {d: [] for d in depots_idx}
        for s in stores_idx:
            d_best = min(depots_idx, key=lambda d: self.C[d, s])
            assignment[d_best].append(s)

        for d in depots_idx:
            print(f"  ✓ {self.df.loc[d, 'Nombre']}: {len(assignment[d])} tiendas")

        return assignment, False  # False = no prediseñadas (iremos a clustering)

    def _clusters_from_groups_or_capacity(self, assignment_or_groups, pre_grouped, vehicle_capacity):
        print("\n[4/6] Creando clusters por capacidad...")
        clusters = defaultdict(list)  # depot_idx -> list of store-list

        if pre_grouped:
            # Cada grupo prediseñado ya es una "ruta base" (validamos capacidad: si excede, se parte)
            for (depot_idx, route_name), stores in assignment_or_groups.items():
                current = []
                demand = 0.0
                for s in stores:
                    d = float(self.df.loc[s, "demanda"])
                    if demand + d <= vehicle_capacity:
                        current.append(s); demand += d
                    else:
                        clusters[depot_idx].append(current)
                        current = [s]; demand = d
                if current:
                    clusters[depot_idx].append(current)
        else:
            # Clustering simple secuencial por capacidad
            for depot_idx, stores in assignment_or_groups.items():
                current = []
                demand = 0.0
                for s in stores:
                    d = float(self.df.loc[s, "demanda"])
                    if demand + d <= vehicle_capacity:
                        current.append(s); demand += d
                    else:
                        clusters[depot_idx].append(current)
                        current = [s]; demand = d
                if current:
                    clusters[depot_idx].append(current)

        # imprimir totales
        for depot_idx, routes in clusters.items():
            print(f"  ✓ {self.df.loc[depot_idx, 'Nombre']}: {len(routes)} rutas")
        return clusters

    def solve(self):
        print("\n======================================================================")
        print("INICIANDO OPTIMIZACIÓN MDVRP")
        print("======================================================================")

        vehicle_capacity = self._vehicle_capacity()

        # Asignación / agrupación
        assignment_or_groups, pre_grouped = self._assignment_or_groups()

        # Clusters por capacidad
        clusters = self._clusters_from_groups_or_capacity(assignment_or_groups, pre_grouped, vehicle_capacity)

        # Optimizador
        print("\n[5/6] Optimizando rutas con Recocido Simulado...")
        sa = SimulatedAnnealingOptimizer(self.D, self.C, self.cfg)

        results = OptimizationResults()
        total_base_fuel = total_opt_fuel = 0.0
        total_base_dist = total_opt_dist = 0.0
        route_counter = 0

        for depot_idx, routes in clusters.items():
            depot_name = self.df.loc[depot_idx, "Nombre"]
            for r_i, stores_idx in enumerate(routes, start=1):
                route_counter += 1

                # Construir ruta base (Prediseñada si hay orden, si no NN)
                if pre_grouped:
                    base_route = RouteBuilder.route_from_predesigned(
                        depot_idx, stores_idx, self.df, self.cfg.col_route_order, self.D
                    )
                    base_kind = "Predisenada"
                else:
                    base_route = RouteBuilder.nearest_neighbor_route(depot_idx, stores_idx, self.D)
                    base_kind = "NN"

                base_dist, base_fuel = sa.route_cost(base_route)

                # Optimizar con SA (multistart)
                sa_route, sa_dist, sa_fuel = sa.optimize(base_route)

                # Elegir mejor (combustible; si empate y activado, distancia)
                chosen_kind = base_kind
                chosen_route = base_route
                chosen_dist, chosen_fuel = base_dist, base_fuel

                better = False
                if sa_fuel < base_fuel - 1e-12:
                    better = True
                elif self.cfg.accept_tie_on_distance and abs(sa_fuel - base_fuel) < 1e-12 and sa_dist < base_dist - 1e-12:
                    better = True
                if better:
                    chosen_kind = "SA"
                    chosen_route = sa_route
                    chosen_dist, chosen_fuel = sa_dist, sa_fuel

                fuel_savings_pct = 100.0 * (base_fuel - sa_fuel) / base_fuel if base_fuel > 0 else 0.0
                dist_savings_pct = 100.0 * (base_dist - sa_dist) / base_dist if base_dist > 0 else 0.0

                print(f"  [{route_counter}] {depot_name}-R{r_i}: Combustible {fuel_savings_pct:.1f}%, Distancia {dist_savings_pct:.1f}%")

                total_base_fuel += base_fuel
                total_opt_fuel += chosen_fuel
                total_base_dist += base_dist
                total_opt_dist += chosen_dist

                results.routes.append(RouteComparison(
                    depot_name=depot_name,
                    route_id=f"{depot_name}-R{r_i}",
                    stores=[self.df.loc[s, "Nombre"] for s in stores_idx],
                    num_stores=len(stores_idx),
                    base_kind=base_kind,
                    base_distance=base_dist,
                    base_fuel_cost=base_fuel,
                    sa_distance=sa_dist,
                    sa_fuel_cost=sa_fuel,
                    sa_improvement_fuel_pct=fuel_savings_pct,
                    sa_improvement_dist_pct=dist_savings_pct,
                    chosen_kind=chosen_kind,
                    chosen_distance=chosen_dist,
                    chosen_fuel_cost=chosen_fuel,
                    base_sequence_idx=base_route,
                    sa_sequence_idx=sa_route,
                    chosen_sequence_idx=chosen_route
                ))

        # Resumen
        print("\n[6/6] Compilando resultados...")
        total_fuel_savings = total_base_fuel - total_opt_fuel
        total_distance_savings = total_base_dist - total_opt_dist
        total_fuel_savings_pct = (100.0 * total_fuel_savings / total_base_fuel) if total_base_fuel > 0 else 0.0
        total_distance_savings_pct = (100.0 * total_distance_savings / total_base_dist) if total_base_dist > 0 else 0.0

        print(f"  ✓ Total rutas: {route_counter}")
        print(f"  ✓ Ahorro combustible: {total_fuel_savings:.2f} ({total_fuel_savings_pct:.1f}%)")
        print(f"  ✓ Ahorro distancia: {total_distance_savings:.2f} km ({total_distance_savings_pct:.1f}%)")

        results.summary = {
            "total_routes": route_counter,
            "total_base_fuel": total_base_fuel,
            "total_opt_fuel": total_opt_fuel,
            "fuel_savings": total_fuel_savings,
            "fuel_savings_pct": total_fuel_savings_pct,
            "total_base_distance": total_base_dist,
            "total_opt_distance": total_opt_dist,
            "distance_savings": total_distance_savings,
            "distance_savings_pct": total_distance_savings_pct
        }

        return results
