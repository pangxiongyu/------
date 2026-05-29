from __future__ import annotations

from src.baseline.shortest_path import direct_route
from src.core.cost_model import assignment_score, energy_pressure, path_cost, risk_penalty
from src.core.geo_utils import route_distance_km
from src.core.schemas import (
    AssignmentResult,
    CandidateEvaluation,
    RoutePlan,
    TaskState,
    UavState,
)
from src.data_io.weather_loader import WeatherMap


def evaluate_candidate(
    uav: UavState,
    task: TaskState,
    weather_map: WeatherMap,
    time: str | None = None,
) -> CandidateEvaluation:
    weather = weather_map.query_nearest(
        latitude=task.target_lat,
        longitude=task.target_lon,
        height_m=task.target_height_m,
        time=time,
    )
    waypoints = direct_route(uav, task)
    distance_km = route_distance_km(waypoints)
    altitude_change_m = task.target_height_m - uav.current_height_m
    score = assignment_score(uav, task, weather)
    total_path_cost = path_cost(
        distance_km=distance_km,
        weather_cost=weather.cost,
        altitude_change_m=altitude_change_m,
        profile=uav.profile,
    )
    return CandidateEvaluation(
        uav_id=uav.uav_id,
        task_id=task.task_id,
        score=score,
        path_cost=total_path_cost,
        distance_km=distance_km,
        weather_cost=weather.cost,
        risk_penalty=risk_penalty(uav.profile.dynamic_risk_level),
        energy_pressure=energy_pressure(uav.profile),
    )


def greedy_assignment(
    uavs: list[UavState],
    tasks: list[TaskState],
    weather_map: WeatherMap,
    time: str | None = None,
    allow_high_risk: bool = False,
) -> AssignmentResult:
    available_uavs = {uav.uav_id: uav for uav in uavs}
    assignments: list[RoutePlan] = []
    rejected_tasks: list[str] = []
    candidate_log: list[CandidateEvaluation] = []
    total_score = 0.0
    total_cost = 0.0

    for task in sorted(tasks, key=lambda item: item.priority, reverse=True):
        candidates: list[CandidateEvaluation] = []
        for uav in available_uavs.values():
            if task.payload_g > uav.payload_capacity_g:
                continue
            if not allow_high_risk and uav.profile.dynamic_risk_level == "high":
                continue
            candidates.append(evaluate_candidate(uav, task, weather_map, time=time))

        candidate_log.extend(candidates)
        if not candidates:
            rejected_tasks.append(task.task_id)
            continue

        best = max(candidates, key=lambda item: item.score)
        uav = available_uavs.pop(best.uav_id)
        weather = weather_map.query_nearest(
            latitude=task.target_lat,
            longitude=task.target_lon,
            height_m=task.target_height_m,
            time=time,
        )
        waypoints = direct_route(uav, task)
        route = RoutePlan(
            uav_id=uav.uav_id,
            task_id=task.task_id,
            waypoints=waypoints,
            total_distance_km=best.distance_km,
            total_cost=best.path_cost,
            weather_cost=weather.cost,
            profile_cost=100.0 - uav.profile.dynamic_health_score,
            metadata={
                "assignment_score": best.score,
                "risk_level": uav.profile.dynamic_risk_level,
                "energy_pressure": best.energy_pressure,
            },
        )
        assignments.append(route)
        total_score += best.score
        total_cost += best.path_cost

    return AssignmentResult(
        assignments=assignments,
        rejected_tasks=rejected_tasks,
        total_score=total_score,
        total_cost=total_cost,
        metadata={
            "candidate_count": len(candidate_log),
            "candidates": candidate_log,
        },
    )

