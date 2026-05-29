from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_io.scenario_loader import build_scenario
from src.eval.export import export_assignments_csv, export_metrics_csv
from src.eval.mappo_checkpoint import evaluate_mappo_checkpoint_for_scenario
from src.eval.metrics import compare_metric_tables
from src.eval.mpc_eval import (
    evaluate_mpc_tracking_for_methods,
    export_mpc_tracking_csv,
    merge_mpc_metrics,
)
from src.eval.scenario_eval import evaluate_scenario
from src.eval.training_export import export_policy_eval_csv


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare baselines, MARL greedy, and a saved MAPPO checkpoint on one scenario."
    )
    parser.add_argument("--config", default=str(ROOT / "configs" / "default.yaml"))
    parser.add_argument(
        "--checkpoint",
        default=str(ROOT / "outputs" / "mappo_train" / "mappo_checkpoint.pt"),
    )
    parser.add_argument("--episodes", type=int, default=None)
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "outputs" / "mappo_benchmark"),
    )
    parser.add_argument(
        "--skip-mpc",
        action="store_true",
        help="Skip Robust MPC route tracking metrics in the benchmark output.",
    )
    args = parser.parse_args()

    scenario = build_scenario(args.config)
    mappo_config = scenario.config.get("mappo", {})
    episodes = args.episodes if args.episodes is not None else int(mappo_config.get("eval_episodes", 3))
    baseline_eval = evaluate_scenario(scenario)
    try:
        checkpoint_eval = evaluate_mappo_checkpoint_for_scenario(
            scenario,
            checkpoint_path=args.checkpoint,
            episodes=episodes,
        )
    except ValueError as error:
        raise SystemExit(
            "MAPPO checkpoint action space does not match this config. "
            "Train a checkpoint with the same marl.route_strategies and height-action settings first. "
            f"Details: {error}"
        ) from error

    metrics_by_method = {
        **baseline_eval.metrics_by_method,
        "mappo_checkpoint": checkpoint_eval.comparable_metrics,
    }
    assignment_results = {
        **baseline_eval.assignment_results,
        "mappo_checkpoint": checkpoint_eval.assignment_result,
    }
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    mpc_export_path: Path | None = None
    if not args.skip_mpc:
        mpc_eval = evaluate_mpc_tracking_for_methods(scenario, assignment_results)
        metrics_by_method = merge_mpc_metrics(metrics_by_method, mpc_eval.metrics_by_method)
        mpc_export_path = output_dir / "mpc_tracking.csv"
        export_mpc_tracking_csv(mpc_eval.route_rows, mpc_export_path)
    table = compare_metric_tables(metrics_by_method)

    export_metrics_csv(metrics_by_method, output_dir / "metrics_with_mappo.csv")
    export_assignments_csv(assignment_results, output_dir / "assignments_reference.csv")
    export_policy_eval_csv(checkpoint_eval.raw_metrics, output_dir / "mappo_policy_eval.csv")
    (output_dir / "comparison.md").write_text(table + "\n", encoding="utf-8")

    print("Scenario")
    print(
        {
            "time": scenario.time,
            "height_m": scenario.height_m,
            "uav_count": len(scenario.uavs),
            "task_count": len(scenario.tasks),
            "checkpoint": args.checkpoint,
            "episodes": episodes,
        }
    )
    print()
    print(table)
    print()
    print(
        "exported:",
        {
            "metrics": str(output_dir / "metrics_with_mappo.csv"),
            "assignments": str(output_dir / "assignments_reference.csv"),
            "policy_eval": str(output_dir / "mappo_policy_eval.csv"),
            "comparison": str(output_dir / "comparison.md"),
            "mpc_tracking": str(mpc_export_path) if mpc_export_path else "",
        },
    )


if __name__ == "__main__":
    main()
