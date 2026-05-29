from __future__ import annotations

from demo_setup import build_demo_problem

from src.baseline.sequential_assignment import sequential_greedy_assignment
from src.eval.metrics import assignment_metrics


def main() -> None:
    weather_map, uavs, tasks, time = build_demo_problem()
    result = sequential_greedy_assignment(uavs, tasks, weather_map, time=time)
    metrics = assignment_metrics(result, task_count=len(tasks))

    print("Sequential baseline assignments")
    for route in result.assignments:
        print(
            {
                "uav_id": route.uav_id,
                "task_id": route.task_id,
                "leg": route.metadata["leg_index"],
                "distance_km": round(route.total_distance_km, 3),
                "total_cost": round(route.total_cost, 3),
                "weather_cost": round(route.weather_cost, 3),
                "risk_level": route.metadata.get("risk_level"),
                "adjusted_score": round(float(route.metadata["adjusted_score"]), 3),
            }
        )
    print("Metrics")
    for key, value in metrics.items():
        print(f"{key}: {value:.4f}")


if __name__ == "__main__":
    main()

