from __future__ import annotations

from dataclasses import replace

from src.baseline.rule_assignment import evaluate_candidate
from src.core.cost_model import normalize, risk_penalty
from src.core.schemas import TaskState, UavState
from src.data_io.weather_loader import WeatherMap
from src.marl.action_space import (
    DEFAULT_ROUTE_STRATEGY,
    WEATHER_3D_ROUTE_STRATEGY,
    WEATHER_GRID_ROUTE_STRATEGY,
    encode_task_action,
)
from src.planning.weather_3d_path import Weather3DPathPlanner
from src.planning.weather_grid_path import WeatherGridPathPlanner


def greedy_policy_actions(
    uavs: list[UavState],
    tasks: list[TaskState],
    weather_map: WeatherMap,
    time: str | None = None,
    height_layers: list[float] | None = None,
    route_strategies: list[str] | None = None,
    weather_grid_weight: float = 20.0,
) -> dict[str, str]:
    pending = [task for task in tasks if task.status == "pending"]
    actions: dict[str, str] = {}
    used_tasks: set[str] = set()
    for uav in uavs:
        candidates = [
            task
            for task in pending
            if task.task_id not in used_tasks and task.payload_g <= uav.payload_capacity_g
        ]
        if not candidates:
            actions[uav.uav_id] = "wait"
            continue
        best_task: TaskState | None = None
        best_height: float | None = None
        best_strategy: str | None = None
        best_score: float | None = None
        for task in candidates:
            candidate_heights = height_layers or [task.target_height_m]
            for height_m in candidate_heights:
                scored_task = replace(task, target_height_m=height_m)
                candidate_strategies = route_strategies or [DEFAULT_ROUTE_STRATEGY]
                for strategy in candidate_strategies:
                    score = _score_strategy(
                        uav=uav,
                        task=scored_task,
                        weather_map=weather_map,
                        time=time,
                        strategy=strategy,
                        weather_grid_weight=weather_grid_weight,
                    )
                    if best_score is None or score > best_score:
                        best_score = score
                        best_task = task
                        best_height = height_m if height_layers else None
                        best_strategy = strategy if route_strategies else None
        if best_task is None:
            actions[uav.uav_id] = "wait"
            continue
        actions[uav.uav_id] = encode_task_action(best_task.task_id, best_height, best_strategy)
        used_tasks.add(best_task.task_id)
    return actions


def _score_strategy(
    uav: UavState,
    task: TaskState,
    weather_map: WeatherMap,
    time: str | None,
    strategy: str,
    weather_grid_weight: float,
) -> float:
    candidate = evaluate_candidate(uav, task, weather_map, time=time)
    if strategy == DEFAULT_ROUTE_STRATEGY:
        return candidate.score
    if strategy == WEATHER_3D_ROUTE_STRATEGY and time is not None:
        path = Weather3DPathPlanner(
            weather_map,
            time=time,
            weather_weight=weather_grid_weight,
        ).plan(
            start_lat=uav.current_lat,
            start_lon=uav.current_lon,
            start_height_m=uav.current_height_m,
            goal_lat=task.target_lat,
            goal_lon=task.target_lon,
            goal_height_m=task.target_height_m,
        )
        average_weather = path.weather_cost_sum / max(1, len(path.waypoints))
        normalized_distance = normalize(path.distance_km, 0.0, 1500.0)
        return (
            uav.profile.dynamic_health_score
            - 20.0 * average_weather
            - 10.0 * normalized_distance
            - risk_penalty(uav.profile.dynamic_risk_level)
            + 10.0 * max(0.0, task.priority - 1.0)
        )
    if strategy != WEATHER_GRID_ROUTE_STRATEGY or time is None:
        return candidate.score - 100.0

    path = WeatherGridPathPlanner(
        weather_map,
        time=time,
        height_m=task.target_height_m,
        weather_weight=weather_grid_weight,
    ).plan(
        start_lat=uav.current_lat,
        start_lon=uav.current_lon,
        goal_lat=task.target_lat,
        goal_lon=task.target_lon,
    )
    average_weather = path.weather_cost_sum / max(1, len(path.waypoints))
    normalized_distance = normalize(path.distance_km, 0.0, 1500.0)
    return (
        uav.profile.dynamic_health_score
        - 20.0 * average_weather
        - 10.0 * normalized_distance
        - risk_penalty(uav.profile.dynamic_risk_level)
        + 10.0 * max(0.0, task.priority - 1.0)
    )
