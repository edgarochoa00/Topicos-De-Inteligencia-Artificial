# mdvrp/visualizer.py
"""
Generador de visualizaciones del sistema MDVRP (Culiacán).
Muestra comparativos Base vs SA vs Elegida y distribución de ahorros.
"""

import matplotlib.pyplot as plt
import numpy as np


class Visualizer:
    @staticmethod
    def generate_visualizations(results, output_path="visualizaciones_mdvrp.png"):
        routes = results.routes
        if not routes:
            print("⚠️ No hay rutas para visualizar.")
            return

        # --- Series para combustible ---
        base_fuel = np.array([r.base_fuel_cost for r in routes], dtype=float)
        sa_fuel = np.array([r.sa_fuel_cost for r in routes], dtype=float)
        chosen_fuel = np.array([r.chosen_fuel_cost for r in routes], dtype=float)

        # --- Series para distancia ---
        base_dist = np.array([r.base_distance for r in routes], dtype=float)
        sa_dist = np.array([r.sa_distance for r in routes], dtype=float)
        chosen_dist = np.array([r.chosen_distance for r in routes], dtype=float)

        # --- Ahorros vs Base ---
        fuel_savings_abs = base_fuel - chosen_fuel
        fuel_savings_pct = np.where(base_fuel > 0, 100.0 * fuel_savings_abs / base_fuel, 0.0)
        dist_savings_abs = base_dist - chosen_dist
        dist_savings_pct = np.where(base_dist > 0, 100.0 * dist_savings_abs / base_dist, 0.0)

        # --- Figura ---
        fig = plt.figure(figsize=(16, 10))
        fig.suptitle("MDVRP Culiacán – Comparativo Base vs SA vs Elegida", fontsize=16, fontweight="bold")

        # 1) Barras apiladas o lado a lado: combustible base/SA/elegida
        ax1 = fig.add_subplot(2, 2, 1)
        x = np.arange(len(routes))
        width = 0.28
        ax1.bar(x - width, base_fuel, width, label="Base $ Comb.", alpha=0.8)
        ax1.bar(x,         sa_fuel,   width, label="SA $ Comb.", alpha=0.8)
        ax1.bar(x + width, chosen_fuel, width, label="Elegida $ Comb.", alpha=0.8)
        ax1.set_title("Combustible por Ruta")
        ax1.set_xlabel("Ruta")
        ax1.set_ylabel("$ (costo combustible)")
        ax1.set_xticks(x)
        ax1.set_xticklabels([r.route_id for r in routes], rotation=90)
        ax1.legend()
        ax1.grid(axis="y", alpha=0.3)

        # 2) Histograma de ahorros de combustible (%)
        ax2 = fig.add_subplot(2, 2, 2)
        ax2.hist(fuel_savings_pct, bins=12, alpha=0.85)
        ax2.axvline(fuel_savings_pct.mean(), linestyle="--", linewidth=2, label=f"Media: {fuel_savings_pct.mean():.2f}%")
        ax2.set_title("Distribución de Ahorros de Combustible (%)")
        ax2.set_xlabel("Ahorro % vs Base (combustible)")
        ax2.set_ylabel("Número de rutas")
        ax2.legend()
        ax2.grid(axis="y", alpha=0.3)

        # 3) Scatter Base vs Elegida (combustible)
        ax3 = fig.add_subplot(2, 2, 3)
        ax3.plot(base_fuel, chosen_fuel, "o", alpha=0.8)
        min_v = float(min(base_fuel.min(), chosen_fuel.min()))
        max_v = float(max(base_fuel.max(), chosen_fuel.max()))
        ax3.plot([min_v, max_v], [min_v, max_v], "--", linewidth=1.5)  # línea y=x
        ax3.set_title("Combustible: Base vs Elegida")
        ax3.set_xlabel("Base $ Combustible")
        ax3.set_ylabel("Elegida $ Combustible")
        ax3.grid(True, alpha=0.3)

        # 4) Barras ahorro de distancia (%) por ruta
        ax4 = fig.add_subplot(2, 2, 4)
        ax4.bar(np.arange(len(routes)), dist_savings_pct, alpha=0.85)
        ax4.set_title("Reducción de Distancia por Ruta (%)")
        ax4.set_xlabel("Ruta")
        ax4.set_ylabel("Reducción % vs Base (km)")
        ax4.set_xticks(np.arange(len(routes)))
        ax4.set_xticklabels([r.route_id for r in routes], rotation=90)
        ax4.grid(axis="y", alpha=0.3)

        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        print(f"\nGenerando visualizaciones en {output_path}...\n  ✓ Visualizaciones generadas exitosamente")
