from __future__ import annotations

import csv
from pathlib import Path

from src.core.schemas import AssignmentResult
from src.data_io.weather_loader import WeatherMap


def export_metrics_csv(metrics_by_method: dict[str, dict[str, float]], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metric_names = sorted({name for metrics in metrics_by_method.values() for name in metrics})
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["metric", *metrics_by_method])
        for metric_name in metric_names:
            writer.writerow(
                [
                    metric_name,
                    *[metrics_by_method[method].get(metric_name, 0.0) for method in metrics_by_method],
                ]
            )


def export_assignments_csv(
    named_results: dict[str, AssignmentResult],
    path: str | Path,
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        fieldnames = [
            "method",
            "uav_id",
            "task_id",
            "leg_index",
            "total_distance_km",
            "total_cost",
            "weather_cost",
            "profile_cost",
            "assignment_score",
            "adjusted_score",
            "risk_level",
            "energy_pressure",
            "route_strategy",
            "waypoint_count",
            "max_segment_distance_km",
            "trackability_penalty",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for method, result in named_results.items():
            for route in result.assignments:
                writer.writerow(
                    {
                        "method": method,
                        "uav_id": route.uav_id,
                        "task_id": route.task_id,
                        "leg_index": route.metadata.get("leg_index", 1),
                        "total_distance_km": route.total_distance_km,
                        "total_cost": route.total_cost,
                        "weather_cost": route.weather_cost,
                        "profile_cost": route.profile_cost,
                        "assignment_score": route.metadata.get("assignment_score", 0.0),
                        "adjusted_score": route.metadata.get("adjusted_score", ""),
                        "risk_level": route.metadata.get("risk_level", ""),
                        "energy_pressure": route.metadata.get("energy_pressure", 0.0),
                        "route_strategy": route.metadata.get("route_strategy", "direct"),
                        "waypoint_count": route.metadata.get(
                            "waypoint_count",
                            len(route.waypoints),
                        ),
                        "max_segment_distance_km": route.metadata.get(
                            "max_segment_distance_km",
                            "",
                        ),
                        "trackability_penalty": route.metadata.get(
                            "trackability_penalty",
                            0.0,
                        ),
                    }
                )


def export_route_waypoints_csv(
    named_results: dict[str, AssignmentResult],
    path: str | Path,
    weather_map: WeatherMap | None = None,
    time: str | None = None,
) -> None:
    """Export full route waypoints for Qt/Web 3D visualization."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "method",
        "uav_id",
        "task_id",
        "leg_index",
        "route_strategy",
        "point_index",
        "latitude",
        "longitude",
        "height_m",
        "weather_cost",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for method, result in named_results.items():
            for route in result.assignments:
                route_strategy = route.metadata.get("route_strategy", "direct")
                leg_index = route.metadata.get("leg_index", 1)
                for point_index, (latitude, longitude, height_m) in enumerate(route.waypoints):
                    weather_cost = ""
                    if weather_map is not None:
                        try:
                            weather_cost = weather_map.query_nearest(
                                latitude,
                                longitude,
                                height_m,
                                time=time,
                            ).cost
                        except ValueError:
                            weather_cost = ""
                    writer.writerow(
                        {
                            "method": method,
                            "uav_id": route.uav_id,
                            "task_id": route.task_id,
                            "leg_index": leg_index,
                            "route_strategy": route_strategy,
                            "point_index": point_index,
                            "latitude": latitude,
                            "longitude": longitude,
                            "height_m": height_m,
                            "weather_cost": weather_cost,
                        }
                    )


def export_batch_metrics_csv(
    rows: list[dict[str, str | float]],
    path: str | Path,
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["experiment", "method", "metric", "value"]
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def flatten_batch_metrics(
    experiment_name: str,
    metrics_by_method: dict[str, dict[str, float]],
) -> list[dict[str, str | float]]:
    rows: list[dict[str, str | float]] = []
    for method, metrics in metrics_by_method.items():
        for metric, value in metrics.items():
            rows.append(
                {
                    "experiment": experiment_name,
                    "method": method,
                    "metric": metric,
                    "value": value,
                }
            )
    return rows
