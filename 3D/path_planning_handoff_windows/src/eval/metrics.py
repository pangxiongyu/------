from __future__ import annotations

from src.core.geo_utils import max_route_segment_distance_km
from src.core.schemas import AssignmentResult


def assignment_metrics(result: AssignmentResult, task_count: int) -> dict[str, float]:
    completed = len(result.assignments)
    total_distance = sum(route.total_distance_km for route in result.assignments)
    max_segment_distances = [
        max_route_segment_distance_km(route.waypoints)
        for route in result.assignments
    ]
    average_weather = (
        sum(route.weather_cost for route in result.assignments) / completed
        if completed
        else 0.0
    )
    high_risk_count = sum(
        1
        for route in result.assignments
        if route.metadata.get("risk_level") == "high"
    )
    energy_pressure_sum = sum(
        float(route.metadata.get("energy_pressure", 0.0))
        for route in result.assignments
    )
    return {
        "task_completion_rate": completed / task_count if task_count else 0.0,
        "completed_task_count": float(completed),
        "rejected_task_count": float(len(result.rejected_tasks)),
        "total_path_cost": result.total_cost,
        "total_assignment_score": result.total_score,
        "total_distance_km": total_distance,
        "average_max_segment_distance_km": (
            sum(max_segment_distances) / completed if completed else 0.0
        ),
        "max_segment_distance_km": max(max_segment_distances) if max_segment_distances else 0.0,
        "average_weather_cost": average_weather,
        "high_risk_assignment_count": float(high_risk_count),
        "energy_pressure_sum": energy_pressure_sum,
    }


def compare_metric_tables(named_metrics: dict[str, dict[str, float]]) -> str:
    metric_names = sorted({name for metrics in named_metrics.values() for name in metrics})
    headers = ["metric", *named_metrics]
    rows = [" | ".join(headers), " | ".join(["---"] * len(headers))]
    for metric_name in metric_names:
        values = [metric_name]
        for method in named_metrics:
            value = named_metrics[method].get(metric_name, 0.0)
            values.append(f"{value:.4f}")
        rows.append(" | ".join(values))
    return "\n".join(rows)
