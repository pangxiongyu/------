from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_io.scenario_loader import build_scenario
from src.eval.export import export_assignments_csv, export_metrics_csv
from src.eval.metrics import compare_metric_tables
from src.eval.scenario_eval import evaluate_scenario
from src.viz.plot_routes import plot_routes
from src.viz.plot_weather_map import plot_weather_layer


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one configured UAV planning scenario.")
    parser.add_argument(
        "--config",
        default=str(ROOT / "configs" / "default.yaml"),
        help="Path to scenario YAML config.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional directory for metrics.csv and assignments.csv.",
    )
    args = parser.parse_args()

    scenario = build_scenario(args.config)
    evaluation = evaluate_scenario(scenario)
    metrics_by_method = evaluation.metrics_by_method
    baseline_result = evaluation.assignment_results["one_shot"]
    sequential_result = evaluation.assignment_results["sequential"]
    weather_aware_result = evaluation.assignment_results["weather_grid"]
    marl_greedy_result = evaluation.assignment_results["marl_greedy"]

    print("Scenario")
    print(
        {
            "time": scenario.time,
            "height_m": scenario.height_m,
            "uav_count": len(scenario.uavs),
            "task_count": len(scenario.tasks),
        }
    )
    print()
    print("One-shot baseline assignments")
    for route in baseline_result.assignments:
        print(
            {
                "uav_id": route.uav_id,
                "task_id": route.task_id,
                "score": round(float(route.metadata["assignment_score"]), 3),
                "cost": round(route.total_cost, 3),
                "weather_cost": round(route.weather_cost, 3),
                "risk_level": route.metadata["risk_level"],
            }
        )
    print()
    print("Sequential baseline assignments")
    for route in sequential_result.assignments:
        print(
            {
                "uav_id": route.uav_id,
                "task_id": route.task_id,
                "leg": route.metadata["leg_index"],
                "score": round(float(route.metadata["adjusted_score"]), 3),
                "cost": round(route.total_cost, 3),
                "weather_cost": round(route.weather_cost, 3),
                "risk_level": route.metadata["risk_level"],
            }
        )
    print()
    print("Metric comparison")
    print(compare_metric_tables(metrics_by_method))

    if args.output_dir:
        output_dir = Path(args.output_dir)
        export_metrics_csv(metrics_by_method, output_dir / "metrics.csv")
        export_assignments_csv(evaluation.assignment_results, output_dir / "assignments.csv")
        plot_weather_layer(
            scenario.weather_map,
            output_dir / "weather_layer.png",
            time=scenario.time,
            height_m=scenario.height_m,
        )
        plot_routes(baseline_result.assignments, output_dir / "routes_one_shot.png")
        plot_routes(sequential_result.assignments, output_dir / "routes_sequential.png")
        plot_routes(weather_aware_result.assignments, output_dir / "routes_weather_grid.png")
        plot_routes(marl_greedy_result.assignments, output_dir / "routes_marl_greedy.png")
        print()
        print("Exported")
        print(
            {
                "metrics": str(output_dir / "metrics.csv"),
                "assignments": str(output_dir / "assignments.csv"),
                "weather_layer": str(output_dir / "weather_layer.png"),
                "routes_one_shot": str(output_dir / "routes_one_shot.png"),
                "routes_sequential": str(output_dir / "routes_sequential.png"),
                "routes_weather_grid": str(output_dir / "routes_weather_grid.png"),
                "routes_marl_greedy": str(output_dir / "routes_marl_greedy.png"),
            }
        )


if __name__ == "__main__":
    main()
