from __future__ import annotations

from dataclasses import replace

from src.baseline.rule_assignment import evaluate_candidate
from src.core.cost_model import energy_pressure
from src.core.schemas import AssignmentResult, CandidateEvaluation, RoutePlan, TaskState, UavState
from src.data_io.weather_loader import WeatherMap
from src.planning.weather_grid_path import WeatherGridPathPlanner


def weather_aware_sequential_assignment(
    uavs: list[UavState],
    tasks: list[TaskState],
    weather_map: WeatherMap,
    time: str,
    height_m: float,
    allow_high_risk: bool = False,
    max_tasks_per_uav: int | None = None,
    weather_weight: float = 20.0,
) -> AssignmentResult:
    planner = WeatherGridPathPlanner(
        weather_map,
        time=time,
        height_m=height_m,
        weather_weight=weather_weight,
    )
    working_uavs = {uav.uav_id: replace(uav) for uav in uavs}
    pending_tasks = {task.task_id: replace(task, target_height_m=height_m) for task in tasks}
    task_counts = {uav.uav_id: 0 for uav in uavs}
    assignments: list[RoutePlan] = []
    candidate_log: list[CandidateEvaluation] = []
    total_score = 0.0
    total_cost = 0.0

    while pending_tasks:
        best_uav: UavState | None = None
        best_task: TaskState | None = None
        best_candidate: CandidateEvaluation | None = None
        best_path = None
        best_score: float | None = None

        for uav in working_uavs.values():
            if max_tasks_per_uav is not None and task_counts[uav.uav_id] >= max_tasks_per_uav:
                continue
            if not allow_high_risk and uav.profile.dynamic_risk_level == "high":
                continue

            for task in pending_tasks.values():
                if task.payload_g > uav.payload_capacity_g:
                    continue
                candidate = evaluate_candidate(uav, task, weather_map, time=time)
                path = planner.plan(
                    start_lat=uav.current_lat,
                    start_lon=uav.current_lon,
                    goal_lat=task.target_lat,
                    goal_lon=task.target_lon,
                )
                adjusted_score = (
                    candidate.score
                    + 10.0 * max(0.0, task.priority - 1.0)
                    - 0.05 * path.weather_cost_sum
                    - 0.01 * path.distance_km
                )
                candidate_log.append(candidate)
                if best_score is None or adjusted_score > best_score:
                    best_uav = uav
                    best_task = task
                    best_candidate = candidate
                    best_path = path
                    best_score = adjusted_score

        if best_uav is None or best_task is None or best_candidate is None or best_path is None:
            break

        leg_index = task_counts[best_uav.uav_id] + 1
        route = RoutePlan(
            uav_id=best_uav.uav_id,
            task_id=best_task.task_id,
            waypoints=best_path.waypoints,
            total_distance_km=best_path.distance_km,
            total_cost=best_path.total_cost,
            weather_cost=best_path.weather_cost_sum / max(1, len(best_path.waypoints)),
            profile_cost=100.0 - best_uav.profile.dynamic_health_score,
            metadata={
                "assignment_score": best_candidate.score,
                "adjusted_score": best_score,
                "risk_level": best_uav.profile.dynamic_risk_level,
                "energy_pressure": energy_pressure(best_uav.profile),
                "leg_index": leg_index,
                "task_priority": best_task.priority,
                "route_strategy": "weather_grid",
                "grid_waypoint_count": len(best_path.waypoints),
                "grid_visited_count": best_path.visited_count,
            },
        )
        assignments.append(route)
        total_score += best_score
        total_cost += best_path.total_cost

        best_uav.current_lat = best_task.target_lat
        best_uav.current_lon = best_task.target_lon
        best_uav.current_height_m = height_m
        best_uav.assigned_task_id = best_task.task_id
        task_counts[best_uav.uav_id] = leg_index
        pending_tasks.pop(best_task.task_id)

    return AssignmentResult(
        assignments=assignments,
        rejected_tasks=sorted(pending_tasks),
        total_score=total_score,
        total_cost=total_cost,
        metadata={
            "candidate_count": len(candidate_log),
            "candidates": candidate_log,
            "task_counts": task_counts,
        },
    )
