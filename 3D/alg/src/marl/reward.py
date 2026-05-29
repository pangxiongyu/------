from __future__ import annotations

from src.baseline.rule_assignment import evaluate_candidate
from src.core.cost_model import normalize
from src.core.schemas import TaskState, UavState
from src.data_io.weather_loader import WeatherMap


def task_reward(
    uav: UavState,
    task: TaskState,
    weather_map: WeatherMap,
    time: str | None = None,
    task_complete_reward: float = 100.0,
    distance_weight: float = 10.0,
    weather_weight: float = 20.0,
    energy_weight: float = 5.0,
    risk_weight: float = 1.0,
    path_cost_weight: float = 0.0,
    trackability_weight: float = 0.0,
    max_distance_km: float = 1500.0,
    max_path_cost: float = 12000.0,
    max_trackable_segment_km: float = 1000.0,
    path_distance_km: float | None = None,
    weather_cost: float | None = None,
    path_cost: float | None = None,
    max_segment_distance_km: float | None = None,
    path_info: dict[str, float] | None = None,
) -> tuple[float, dict[str, float]]:
    evaluation = evaluate_candidate(uav, task, weather_map, time=time)
    effective_distance_km = evaluation.distance_km if path_distance_km is None else path_distance_km
    effective_weather_cost = evaluation.weather_cost if weather_cost is None else weather_cost
    effective_path_cost = evaluation.path_cost if path_cost is None else path_cost
    effective_max_segment_distance_km = (
        effective_distance_km
        if max_segment_distance_km is None
        else max_segment_distance_km
    )
    normalized_distance = normalize(effective_distance_km, 0.0, max_distance_km)
    normalized_path_cost = normalize(effective_path_cost, 0.0, max_path_cost)
    normalized_trackability_penalty = normalize(
        effective_max_segment_distance_km,
        0.0,
        max_trackable_segment_km,
    )
    reward = (
        task_complete_reward * task.priority
        - distance_weight * normalized_distance
        - weather_weight * effective_weather_cost
        - energy_weight * evaluation.energy_pressure
        - risk_weight * evaluation.risk_penalty
        - path_cost_weight * normalized_path_cost
        - trackability_weight * normalized_trackability_penalty
    )
    info = {
        "distance_km": effective_distance_km,
        "normalized_distance": normalized_distance,
        "normalized_path_cost": normalized_path_cost,
        "max_segment_distance_km": effective_max_segment_distance_km,
        "normalized_trackability_penalty": normalized_trackability_penalty,
        "trackability_penalty": trackability_weight * normalized_trackability_penalty,
        "weather_cost": effective_weather_cost,
        "energy_pressure": evaluation.energy_pressure,
        "risk_penalty": evaluation.risk_penalty,
        "path_cost": effective_path_cost,
        "assignment_score": evaluation.score,
    }
    if path_info:
        info.update(path_info)
    return reward, info
