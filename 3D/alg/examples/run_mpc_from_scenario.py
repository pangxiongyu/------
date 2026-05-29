from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_io.scenario_loader import build_scenario
from src.eval.mpc_eval import build_mpc_controller, constraint_violation_count, control_effort
from src.eval.scenario_eval import evaluate_scenario
from src.mpc.route_tracking import track_route_with_weather


def main() -> None:
    parser = argparse.ArgumentParser(description="Track one assigned route from a configured scenario.")
    parser.add_argument(
        "--config",
        default=str(ROOT / "configs" / "default.yaml"),
        help="Path to scenario YAML config.",
    )
    parser.add_argument(
        "--method",
        default="marl_greedy",
        help="Assignment method to track, e.g. marl_greedy, weather_grid, sequential, one_shot.",
    )
    args = parser.parse_args()

    scenario = build_scenario(args.config)
    evaluation = evaluate_scenario(scenario)
    if args.method not in evaluation.assignment_results:
        available = ", ".join(evaluation.assignment_results)
        raise SystemExit(f"Unknown method={args.method}. Available methods: {available}")
    result = evaluation.assignment_results[args.method]
    if not result.assignments:
        raise SystemExit("No route assignment available for MPC tracking.")

    route = next(
        (candidate for candidate in result.assignments if candidate.total_distance_km > 1.0),
        result.assignments[0],
    )
    mpc_config = scenario.config.get("mpc", {})
    controller_name = str(mpc_config.get("controller", "prototype"))
    controller = build_mpc_controller(mpc_config)
    summary = track_route_with_weather(
        route,
        scenario.weather_map,
        time=scenario.time,
        controller=controller,
        steps_per_segment=int(mpc_config.get("steps_per_segment", 25)),
        coordinate_scale=float(mpc_config.get("coordinate_scale", 1.0)),
    )

    print(
        "tracked_route:",
        {
            "method": args.method,
            "uav_id": route.uav_id,
            "task_id": route.task_id,
            "route_strategy": route.metadata.get("route_strategy", ""),
        },
    )
    print("controller:", controller_name)
    print("local_waypoints:", summary.local_waypoints)
    print("wind_vectors:", summary.winds)
    print("state_count:", len(summary.tracking_result.states))
    print("control_count:", len(summary.tracking_result.controls))
    print("mean_tracking_error:", round(summary.tracking_result.mean_tracking_error, 4))
    print("max_tracking_error:", round(max(summary.tracking_result.tracking_errors or [0.0]), 4))
    print("total_control_effort:", round(control_effort(summary.tracking_result.controls), 4))
    print(
        "constraint_violation_count:",
        constraint_violation_count(summary.tracking_result, mpc_config),
    )
    print("final_state:", summary.tracking_result.states[-1])


if __name__ == "__main__":
    main()
