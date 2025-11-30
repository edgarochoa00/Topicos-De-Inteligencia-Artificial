# main.py
"""
Ejecución principal MDVRP (Culiacán):
- Usa rutas prediseñadas si existen columnas Ruta_Predisenada / Orden_Ruta
- Compara Prediseñada vs SA y elige la mejor
- Imprime informe completo y exporta Excel + visualizaciones
"""

from mdvrp.config import OptimizationConfig
from mdvrp.data_loader import DataLoader
from mdvrp.solver import MDVRPSolver
from mdvrp.results_table import ResultsTableGenerator
from mdvrp.visualizer import Visualizer


def main():
    cfg = OptimizationConfig()
    loader = DataLoader(cfg)
    df, df_depots, df_stores, D, C, has_predesigned = loader.load_data()

    solver = MDVRPSolver(cfg, df, df_depots, df_stores, D, C, has_predesigned)
    results = solver.solve()

    # Tabla + Excel
    ResultsTableGenerator.print_and_export(results, df, output_excel="resumen_global.xlsx")

    # Visualizaciones
    Visualizer.generate_visualizations(results, cfg.output_visualizations)

    # Cierre tipo auditoría
    print("\n" + "="*70)
    print("OPTIMIZACION COMPLETADA EXITOSAMENTE")
    print("="*70)
    print(f"\n RESULTADOS FINALES:")
    print(f"  * Total de rutas generadas: {results.summary['total_routes']}")
    print(f"  * Costo combustible base: ${results.summary['total_base_fuel']:.2f}")
    print(f"  * Costo combustible optimizado: ${results.summary['total_opt_fuel']:.2f}")
    print(f"  * Ahorro en combustible: ${results.summary['fuel_savings']:.2f} "
          f"({results.summary['fuel_savings_pct']:.2f}%)")
    print(f"  * Distancia base: {results.summary['total_base_distance']:.2f} km")
    print(f"  * Distancia optimizada: {results.summary['total_opt_distance']:.2f} km")
    print(f"  * Reduccion de distancia: {results.summary['distance_savings']:.2f} km "
          f"({results.summary['distance_savings_pct']:.2f}%)")
    print(f"\n ARCHIVOS GENERADOS:")
    print(f"  * Visualizaciones: {cfg.output_visualizations}")
    print(f"  * Excel resumen: resumen_global.xlsx")
    print("\n Sistema listo para análisis de resultados")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
