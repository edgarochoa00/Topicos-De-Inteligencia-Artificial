# mdvrp/results_table.py
"""
Tabla de resultados en terminal + export a Excel con resumen por CD y global.
"""

import pandas as pd
from collections import defaultdict


class ResultsTableGenerator:

    @staticmethod
    def print_and_export(results, df, output_excel="resumen_global.xlsx"):
        print("\n" + "="*100)
        print("TABLA DE RESULTADOS - OPTIMIZACION MDVRP (Prediseñada vs SA vs Elegida)")
        print("="*100)

        # Agrupar por depósito
        by_depot = defaultdict(list)
        for r in results.routes:
            by_depot[r.depot_name].append(r)

        rows = []
        for depot_num, (depot_name, routes) in enumerate(by_depot.items(), start=1):
            print(f"\n{'='*100}")
            print(f"CENTRO DE DISTRIBUCION #{depot_num}: {depot_name}")
            print(f"{'='*100}\nRutas desde este deposito: {len(routes)}")
            print("-"*100)
            print(f"{'RUTA':<30}{'BASE(tipo)':<12}{'BASE$':>10}{'SA$':>10}{'ELEGIDA':>10}{'AHORRO% SA':>12}")
            print("-"*100)

            depot_base = depot_opt = 0.0
            depot_base_dist = depot_opt_dist = 0.0

            for route in routes:
                depot_base += route.base_fuel_cost
                depot_base_dist += route.base_distance
                depot_opt += route.chosen_fuel_cost
                depot_opt_dist += route.chosen_distance

                print(f"{route.route_id:<30}{route.base_kind:<12}"
                      f"{route.base_fuel_cost:>10.2f}{route.sa_fuel_cost:>10.2f}{route.chosen_kind:>10}"
                      f"{route.sa_improvement_fuel_pct:>12.2f}")

                rows.append({
                    "Centro de Distribución": depot_name,
                    "Ruta": route.route_id,
                    "Tiendas": route.num_stores,
                    "Base Tipo": route.base_kind,
                    "Base Combustible": route.base_fuel_cost,
                    "Base Distancia": route.base_distance,
                    "SA Combustible": route.sa_fuel_cost,
                    "SA Distancia": route.sa_distance,
                    "Elegida": route.chosen_kind,
                    "Elegida Combustible": route.chosen_fuel_cost,
                    "Elegida Distancia": route.chosen_distance,
                    "Ahorro Combustible (%) vs Base": route.sa_improvement_fuel_pct,
                    "Ahorro Distancia (%) vs Base": route.sa_improvement_dist_pct
                })

            depot_sav = depot_base - depot_opt
            depot_sav_pct = (100.0 * depot_sav / depot_base) if depot_base > 0 else 0.0
            depot_dist_sav = depot_base_dist - depot_opt_dist
            depot_dist_sav_pct = (100.0 * depot_dist_sav / depot_base_dist) if depot_base_dist > 0 else 0.0

            print("-"*100)
            print(f"➡️  TOTAL {depot_name:<25} | BASE $:{depot_base:>10.2f} | OPT $:{depot_opt:>10.2f} | "
                  f"AHORRO: {depot_sav_pct:>6.2f}% | REDUCCION DIST: {depot_dist_sav_pct:>6.2f}%")

        # Resumen global
        df_routes = pd.DataFrame(rows)
        total_base = df_routes["Base Combustible"].sum()
        total_opt = df_routes["Elegida Combustible"].sum()
        total_sav = total_base - total_opt
        total_sav_pct = (100.0 * total_sav / total_base) if total_base > 0 else 0.0
        total_base_dist = df_routes["Base Distancia"].sum()
        total_opt_dist = df_routes["Elegida Distancia"].sum()
        total_dist_sav = total_base_dist - total_opt_dist
        total_dist_sav_pct = (100.0 * total_dist_sav / total_base_dist) if total_base_dist > 0 else 0.0

        print("\n" + "="*100)
        print("📈  RESUMEN GLOBAL DEL SISTEMA DE OPTIMIZACIÓN")
        print("="*100)
        print(f"BASE $: {total_base:.2f} | OPT $: {total_opt:.2f} | AHORRO $: {total_sav:.2f} ({total_sav_pct:.2f}%)")
        print(f"BASE km: {total_base_dist:.2f} | OPT km: {total_opt_dist:.2f} | REDUCCION km: {total_dist_sav:.2f} ({total_dist_sav_pct:.2f}%)")

        # Exportar a Excel (incluye hoja rutas y hoja resumen)
        with pd.ExcelWriter(output_excel, engine="xlsxwriter") as writer:
            df_routes.to_excel(writer, sheet_name="Rutas Detalle", index=False)
            pd.DataFrame([{
                "Costo Base Total": total_base,
                "Costo Optimizado Total": total_opt,
                "Ahorro $": total_sav,
                "Ahorro %": total_sav_pct,
                "Distancia Base Total": total_base_dist,
                "Distancia Optimizada Total": total_opt_dist,
                "Reducción Distancia km": total_dist_sav,
                "Reducción Distancia %": total_dist_sav_pct
            }]).to_excel(writer, sheet_name="Resumen Global (Culiacán)", index=False)

        print(f"\nResumen exportado a {output_excel}")
