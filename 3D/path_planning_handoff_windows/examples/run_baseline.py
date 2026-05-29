from __future__ import annotations

from demo_setup import build_demo_problem

from src.baseline.rule_assignment import greedy_assignment
from src.eval.metrics import assignment_metrics


def main() -> None:
    weather_map, uavs, tasks, time = build_demo_problem()
    result = greedy_assignment(uavs, tasks, weather_map, time=time)
    metrics = assignment_metrics(result, task_count=len(tasks))

    print("Baseline assignments")
    for route in result.assignments:
        print(
            {
                "uav_id": route.uav_id,
                "task_id": route.task_id,
                "distance_km": round(route.total_distance_km, 3),
                "total_cost": round(route.total_cost, 3),
                "weather_cost": round(route.weather_cost, 3),
                "risk_level": route.metadata.get("risk_level"),
                "assignment_score": round(float(route.metadata["assignment_score"]), 3),
            }
        )
    print("Metrics")
    for key, value in metrics.items():
        print(f"{key}: {value:.4f}")


if __name__ == "__main__":
    main()

