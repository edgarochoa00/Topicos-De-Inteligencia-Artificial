import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pathlib import Path
from .config import OptimizationResults, RouteMetrics


class ResultsExporter:
    """Exporta resultados a Excel y visualizaciones"""

    @staticmethod
    def export_to_excel(results: OptimizationResults, df: pd.DataFrame,
                       distance_matrix: np.ndarray, fuel_matrix: np.ndarray,
                       output_path: Path):
        print(f"\nExportando resultados a {output_path}...")

        summary_data = {
            "Métrica": ["Costo Total Combustible", "Distancia Total (km)", "Número de Rutas"],
            "Base (NN)": [
                results.total_base_fuel_cost,
                results.total_base_distance,
                len(results.routes)
            ],
            "Optimizado (SA)": [
                results.total_opt_fuel_cost,
                results.total_opt_distance,
                len(results.routes)
            ]
        }
        df_summary = pd.DataFrame(summary_data)

        df_routes = pd.DataFrame([{
            "Ruta ID": r.route_id,
            "Depósito": r.depot_name,
            "Tiendas": r.num_stores,
            "Combustible Base": r.base_fuel_cost,
            "Combustible Optimizado": r.opt_fuel_cost,
            "Ahorro (%)": r.fuel_savings_pct
        } for r in results.routes])

        with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
            df_summary.to_excel(writer, sheet_name="Resumen", index=False)
            df_routes.to_excel(writer, sheet_name="Rutas", index=False)
        print("  ✓ Exportación completada")

    @staticmethod
    def create_visualizations(results: OptimizationResults, df: pd.DataFrame, output_path: Path):
        print(f"\nGenerando visualizaciones en {output_path}...")
        fig = plt.figure(figsize=(14, 8))
        gs = GridSpec(1, 2, figure=fig, wspace=0.3)

        ax1 = fig.add_subplot(gs[0, 0])
        ax1.bar(["Base", "Optimizado"], [results.total_base_fuel_cost, results.total_opt_fuel_cost],
                color=["#ff9999", "#66b3ff"])
        ax1.set_title("Comparación de costos de combustible")
        ax1.set_ylabel("Costo total")

        ax2 = fig.add_subplot(gs[0, 1])
        ax2.hist([r.fuel_savings_pct for r in results.routes], bins=10, color="lightgreen", edgecolor="black")
        ax2.set_title("Distribución de Ahorros (%)")

        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()
        print("  ✓ Visualización generada")
