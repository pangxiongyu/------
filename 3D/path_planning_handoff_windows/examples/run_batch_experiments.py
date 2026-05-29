from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_io.scenario_loader import build_scenario_from_config, load_config
from src.eval.export import (
    export_assignments_csv,
    export_batch_metrics_csv,
    export_metrics_csv,
    flatten_batch_metrics,
)
from src.eval.metrics import compare_metric_tables
from src.eval.report import export_batch_summary
from src.eval.scenario_eval import evaluate_scenario


def deep_merge(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def load_suite(path: str | Path) -> dict[str, Any]:
    suite_path = Path(path)
    with suite_path.open("r", encoding="utf-8") as file:
        suite = yaml.safe_load(file) or {}
    suite["_suite_path"] = str(suite_path)
    suite["_root"] = str(suite_path.resolve().parents[1])
    return suite


def main() -> None:
    parser = argparse.ArgumentParser(description="Run configured batch UAV planning experiments.")
    parser.add_argument(
        "--suite",
        default=str(ROOT / "configs" / "experiments.yaml"),
        help="Path to batch experiment YAML.",
    )
    args = parser.parse_args()

    suite = load_suite(args.suite)
    root = Path(suite["_root"])
    base_config_path = root / suite.get("base_config", "configs/default.yaml")
    base_config = load_config(base_config_path)
    output_dir = root / suite.get("output_dir", "outputs/batch_experiments")
    output_dir.mkdir(parents=True, exist_ok=True)

    batch_rows: list[dict[str, str | float]] = []
    experiments = suite.get("experiments", [])
    if not experiments:
        raise SystemExit("No experiments configured.")

    for experiment in experiments:
        name = str(experiment["name"])
        overrides = experiment.get("overrides", {})
        config = deep_merge(base_config, overrides)
        scenario = build_scenario_from_config(config, root=root)
        evaluation = evaluate_scenario(scenario)
        experiment_dir = output_dir / name
        export_metrics_csv(evaluation.metrics_by_method, experiment_dir / "metrics.csv")
        export_assignments_csv(evaluation.assignment_results, experiment_dir / "assignments.csv")
        batch_rows.extend(flatten_batch_metrics(name, evaluation.metrics_by_method))

        print(f"\nExperiment: {name}")
        print(
            {
                "time": scenario.time,
                "height_m": scenario.height_m,
                "uav_count": len(scenario.uavs),
                "task_count": len(scenario.tasks),
            }
        )
        print(compare_metric_tables(evaluation.metrics_by_method))

    long_metrics_path = output_dir / "batch_metrics_long.csv"
    export_batch_metrics_csv(batch_rows, long_metrics_path)
    export_batch_summary(long_metrics_path, output_dir)
    print("\nBatch exported")
    print(
        {
            "output_dir": str(output_dir),
            "batch_metrics": str(long_metrics_path),
            "batch_summary": str(output_dir / "batch_summary.csv"),
        }
    )


if __name__ == "__main__":
    main()
