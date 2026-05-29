from __future__ import annotations

from src.data_io.scenario_loader import build_scenario
from src.eval.mpc_eval import evaluate_mpc_tracking_for_assignment
from src.eval.scenario_eval import evaluate_scenario


def test_mpc_tracking_metrics_are_added_for_assignment_result() -> None:
    scenario = build_scenario("configs/default.yaml")
    scenario.config["mpc"] = {
        "controller": "prototype",
        "dt": 1.0,
        "max_acc": 3.0,
        "max_speed": 20.0,
        "min_height_m": 0.0,
        "max_height_m": 120.0,
        "steps_per_segment": 2,
        "coordinate_scale": 0.001,
    }
    evaluation = evaluate_scenario(scenario)
    assignment_result = evaluation.assignment_results["sequential"]

    metrics, rows = evaluate_mpc_tracking_for_assignment(
        "sequential",
        assignment_result,
        scenario,
    )

    assert metrics["mpc_route_count"] == len(assignment_result.assignments)
    assert metrics["mpc_tracked_route_count"] == len(assignment_result.assignments)
    assert metrics["mpc_failed_route_count"] == 0.0
    assert metrics["mpc_total_control_count"] > 0.0
    assert metrics["mpc_mean_tracking_error"] >= 0.0
    assert len(rows) == len(assignment_result.assignments)
    assert rows[0]["status"] == "ok"
