# mdvrp/config.py
"""
Configuración y modelos de resultados del sistema MDVRP (Culiacán).
Incluye parámetros de SA, columnas opcionales para rutas pre-diseñadas
y estructuras para reportar comparación Prediseñada vs SA vs Elegida.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class OptimizationConfig:
    # Archivos
    data_file: str = "distribucion.xlsx"
    distance_matrix_file: str = "matriz_distancias.xlsx"
    fuel_matrix_file: str = "matriz_costos_combustible.xlsx"
    output_visualizations: str = "visualizaciones_mdvrp.png"

    # Columnas (opcionales) para rutas pre-diseñadas
    col_route_name: str = "Ruta_Predisenada"
    col_route_order: str = "Orden_Ruta"

    # Parámetros operativos / vehículo
    average_speed_kmh: float = 35.0
    service_time_minutes: float = 10.0
    capacity_multiplier_p50: float = 3.0
    capacity_multiplier_p80: float = 2.2

    # SA (Simulated Annealing)
    seed: int = 123
    initial_temp: float = 0.5       # factor relativo al costo inicial
    cooling_rate: float = 0.995
    min_temp: float = 1e-6
    iterations_base: int = 2000
    iterations_per_store: int = 150
    track_iterations: bool = True
    tracking_interval: int = 50

    # Metaheurística robustecida
    multistart_perturbations: int = 5  # intentos adicionales perturbando la ruta inicial
    accept_tie_on_distance: bool = True  # desempate por menor distancia cuando costos iguales


@dataclass
class RouteComparison:
    """Comparativa por ruta: prediseñada vs SA, y la elegida."""
    depot_name: str
    route_id: str
    stores: List[str]
    num_stores: int

    # Prediseñada (si aplica; si no, se usa NN como 'base')
    base_kind: str  # 'Predisenada' o 'NN'
    base_distance: float
    base_fuel_cost: float

    # Optimizada con SA
    sa_distance: float
    sa_fuel_cost: float
    sa_improvement_fuel_pct: float
    sa_improvement_dist_pct: float

    # Elegida (la mejor de ambas)
    chosen_kind: str  # 'Predisenada' o 'SA'
    chosen_distance: float
    chosen_fuel_cost: float

    # Secuencias (índices)
    base_sequence_idx: List[int]
    sa_sequence_idx: List[int]
    chosen_sequence_idx: List[int]


@dataclass
class OptimizationResults:
    """Resultados globales del sistema MDVRP."""
    routes: List[RouteComparison] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
