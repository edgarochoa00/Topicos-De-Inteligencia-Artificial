# mdvrp/optimizer.py
"""
Recocido Simulado para optimizar rutas, con multistart y desempate por distancia.
"""

import math
import random
import numpy as np
from .local_search import LocalSearchOperators


class SimulatedAnnealingOptimizer:
    def __init__(self, distance_matrix, fuel_matrix, config):
        self.D = distance_matrix
        self.C = fuel_matrix
        self.cfg = config
        random.seed(config.seed)
        np.random.seed(config.seed)

    def route_cost(self, route):
        dist = 0.0
        fuel = 0.0
        for i in range(len(route) - 1):
            a, b = route[i], route[i + 1]
            dist += self.D[a, b]
            fuel += self.C[a, b]
        return dist, fuel

    def _accept(self, delta, T):
        if delta < 0:
            return True
        if T <= 0:
            return False
        return (random.random() < math.exp(-delta / T))

    def optimize(self, initial_route):
        """
        SA fuel-first: minimiza combustible, empata con distancia si cfg.accept_tie_on_distance.
        Aplica multistart con pequeñas perturbaciones de la solución inicial.
        """
        best_overall = None  # (route, dist, fuel)

        starts = [initial_route[:]]
        # Perturbaciones controladas
        inner = initial_route[1:-1]
        for _ in range(self.cfg.multistart_perturbations):
            op = LocalSearchOperators.get_random_operator()
            pert = [initial_route[0]] + op(inner) + [initial_route[-1]]
            starts.append(pert)

        for seed_route in starts:
            route = seed_route[:]
            dist, fuel = self.route_cost(route)
            best_route, best_dist, best_fuel = route[:], dist, fuel

            # Temperatura inicial relativa al costo
            T = max(1.0, self.cfg.initial_temp * max(1.0, fuel))
            iterations = max(self.cfg.iterations_base, self.cfg.iterations_per_store * max(1, len(inner)))

            for it in range(iterations):
                # Generar vecino (mutar parte interna)
                inner_now = route[1:-1]
                op = LocalSearchOperators.get_random_operator()
                new_inner = op(inner_now)
                candidate = [route[0]] + new_inner + [route[-1]]

                new_dist, new_fuel = self.route_cost(candidate)

                # fuel-first delta (con desempate por distancia si aplica)
                if self.cfg.accept_tie_on_distance and abs(new_fuel - fuel) < 1e-12:
                    delta = new_dist - dist
                else:
                    delta = new_fuel - fuel

                if self._accept(delta, T):
                    route, dist, fuel = candidate, new_dist, new_fuel
                    # Actualizar best local por fuel y distancia
                    better = False
                    if fuel < best_fuel - 1e-12:
                        better = True
                    elif abs(fuel - best_fuel) < 1e-12 and dist < best_dist - 1e-12:
                        better = True
                    if better:
                        best_route, best_dist, best_fuel = route[:], dist, fuel

                # enfriamiento
                T *= self.cfg.cooling_rate
                if T < self.cfg.min_temp:
                    T = max(1.0, self.cfg.initial_temp * max(1.0, best_fuel))

            # Actualizar mejor global
            if best_overall is None:
                best_overall = (best_route, best_dist, best_fuel)
            else:
                _, bD, bF = best_overall
                if best_fuel < bF - 1e-12 or (abs(best_fuel - bF) < 1e-12 and best_dist < bD - 1e-12):
                    best_overall = (best_route, best_dist, best_fuel)

        return best_overall
