from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.schemas import AssignmentResult, RoutePlan
from src.data_io.scenario_loader import PlanningScenario
from src.mpc.dynamics import ControlInput, PointMassState
from src.mpc.robust_mpc import ConstrainedRobustMPC, RobustMPCPrototype, TrackingResult
from src.mpc.route_tracking import track_route_with_weather


@dataclass(frozen=True)
class MpcTrackingEvaluation:
    metrics_by_method: dict[str, dict[str, float]]
    route_rows: list[dict[str, str | float]]


def build_mpc_controller(mpc_config: dict[str, Any]) -> RobustMPCPrototype | ConstrainedRobustMPC:
    controller_name = str(mpc_config.get("controller", "prototype"))
    if controller_name == "qp":
        return ConstrainedRobustMPC(
            dt=float(mpc_config.get("dt", 1.0)),
            horizon=int(mpc_config.get("horizon", 6)),
            max_acc=float(mpc_config.get("max_acc", 3.0)),
            max_speed=float(mpc_config.get("max_speed", 20.0)),
            min_height_m=float(mpc_config.get("min_height_m", 0.0)),
            max_height_m=float(mpc_config.get("max_height_m", 120.0)),
        )
    return RobustMPCPrototype(
        dt=float(mpc_config.get("dt", 1.0)),
        max_acc=float(mpc_config.get("max_acc", 3.0)),
        max_speed=float(mpc_config.get("max_speed", 20.0)),
    )


def control_effort(controls: list[ControlInput]) -> float:
    return sum(control.ax**2 + control.ay**2 + control.az**2 for control in controls)


def _state_speed(state: PointMassState) -> float:
    return math.sqrt(state.vx**2 + state.vy**2 + state.vz**2)


def constraint_violation_count(
    tracking_result: TrackingResult,
    mpc_config: dict[str, Any],
    tolerance: float = 1e-6,
) -> int:
    max_acc = float(mpc_config.get("max_acc", 3.0))
    max_speed = float(mpc_config.get("max_speed", 20.0))
    min_height_m = float(mpc_config.get("min_height_m", 0.0))
    max_height_m = float(mpc_config.get("max_height_m", 120.0))

    violations = 0
    for state in tracking_result.states:
        if state.z < min_height_m - tolerance or state.z > max_height_m + tolerance:
            violations += 1
        if _state_speed(state) > max_speed + tolerance:
            violations += 1
    for control in tracking_result.controls:
        if (
            abs(control.ax) > max_acc + tolerance
            or abs(control.ay) > max_acc + tolerance
            or abs(control.az) > max_acc + tolerance
        ):
            violations += 1
    return violations


def _route_metrics(
    route: RoutePlan,
    tracking_result: TrackingResult,
    mpc_config: dict[str, Any],
) -> dict[str, float]:
    errors = tracking_result.tracking_errors
    total_effort = control_effort(tracking_result.controls)
    control_count = len(tracking_result.controls)
    return {
        "mean_tracking_error": sum(errors) / len(errors) if errors else 0.0,
        "max_tracking_error": max(errors) if errors else 0.0,
        "total_control_effort": total_effort,
        "mean_control_effort": total_effort / control_count if control_count else 0.0,
        "constraint_violation_count": float(
            constraint_violation_count(tracking_result, mpc_config)
        ),
        "state_count": float(len(tracking_result.states)),
        "control_count": float(control_count),
        "waypoint_count": float(len(route.waypoints)),
    }


def evaluate_mpc_tracking_for_assignment(
    method: str,
    result: AssignmentResult,
    scenario: PlanningScenario,
) -> tuple[dict[str, float], list[dict[str, str | float]]]:
    mpc_config = scenario.config.get("mpc", {})
    controller = build_mpc_controller(mpc_config)
    steps_per_segment = int(mpc_config.get("steps_per_segment", 25))
    coordinate_scale = float(mpc_config.get("coordinate_scale", 1.0))

    route_rows: list[dict[str, str | float]] = []
    all_errors: list[float] = []
    total_control_effort = 0.0
    total_control_count = 0
    total_state_count = 0
    total_violations = 0
    tracked_count = 0
    failed_count = 0

    for route in result.assignments:
        base_row: dict[str, str | float] = {
            "method": method,
            "uav_id": route.uav_id,
            "task_id": route.task_id,
            "leg_index": float(route.metadata.get("leg_index", 1)),
            "route_strategy": str(route.metadata.get("route_strategy", "direct")),
        }
        try:
            summary = track_route_with_weather(
                route,
                scenario.weather_map,
                time=scenario.time,
                controller=controller,
                steps_per_segment=steps_per_segment,
                coordinate_scale=coordinate_scale,
            )
        except Exception as error:
            failed_count += 1
            route_rows.append(
                {
                    **base_row,
                    "status": "failed",
                    "error": str(error),
                    "mean_tracking_error": 0.0,
                    "max_tracking_error": 0.0,
                    "total_control_effort": 0.0,
                    "mean_control_effort": 0.0,
                    "constraint_violation_count": 0.0,
                    "state_count": 0.0,
                    "control_count": 0.0,
                    "waypoint_count": float(len(route.waypoints)),
                }
            )
            continue

        tracked_count += 1
        tracking_result = summary.tracking_result
        route_metric = _route_metrics(route, tracking_result, mpc_config)
        all_errors.extend(tracking_result.tracking_errors)
        total_control_effort += route_metric["total_control_effort"]
        total_control_count += int(route_metric["control_count"])
        total_state_count += int(route_metric["state_count"])
        total_violations += int(route_metric["constraint_violation_count"])
        route_rows.append(
            {
                **base_row,
                "status": "ok",
                "error": "",
                **route_metric,
            }
        )

    metrics = {
        "mpc_route_count": float(len(result.assignments)),
        "mpc_tracked_route_count": float(tracked_count),
        "mpc_failed_route_count": float(failed_count),
        "mpc_mean_tracking_error": sum(all_errors) / len(all_errors) if all_errors else 0.0,
        "mpc_max_tracking_error": max(all_errors) if all_errors else 0.0,
        "mpc_total_control_effort": total_control_effort,
        "mpc_mean_control_effort": (
            total_control_effort / total_control_count if total_control_count else 0.0
        ),
        "mpc_constraint_violation_count": float(total_violations),
        "mpc_total_state_count": float(total_state_count),
        "mpc_total_control_count": float(total_control_count),
        "mpc_coordinate_scale": coordinate_scale,
    }
    return metrics, route_rows


def evaluate_mpc_tracking_for_methods(
    scenario: PlanningScenario,
    assignment_results: dict[str, AssignmentResult],
) -> MpcTrackingEvaluation:
    metrics_by_method: dict[str, dict[str, float]] = {}
    route_rows: list[dict[str, str | float]] = []
    for method, result in assignment_results.items():
        metrics, rows = evaluate_mpc_tracking_for_assignment(method, result, scenario)
        metrics_by_method[method] = metrics
        route_rows.extend(rows)
    return MpcTrackingEvaluation(metrics_by_method=metrics_by_method, route_rows=route_rows)


def merge_mpc_metrics(
    metrics_by_method: dict[str, dict[str, float]],
    mpc_metrics_by_method: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    merged = {method: dict(metrics) for method, metrics in metrics_by_method.items()}
    for method, metrics in mpc_metrics_by_method.items():
        merged.setdefault(method, {}).update(metrics)
    return merged


def export_mpc_tracking_csv(
    rows: list[dict[str, str | float]],
    path: str | Path,
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "method",
        "uav_id",
        "task_id",
        "leg_index",
        "route_strategy",
        "status",
        "error",
        "mean_tracking_error",
        "max_tracking_error",
        "total_control_effort",
        "mean_control_effort",
        "constraint_violation_count",
        "state_count",
        "control_count",
        "waypoint_count",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
