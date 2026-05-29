from __future__ import annotations

from dataclasses import replace

from src.baseline.rule_assignment import evaluate_candidate
from src.baseline.shortest_path import direct_route
from src.core.schemas import AssignmentResult, CandidateEvaluation, RoutePlan, TaskState, UavState
from src.data_io.weather_loader import WeatherMap


def _task_priority_bonus(task: TaskState, priority_weight: float) -> float:
    return priority_weight * max(0.0, task.priority - 1.0)


def sequential_greedy_assignment(
    uavs: list[UavState],
    tasks: list[TaskState],
    weather_map: WeatherMap,
    time: str | None = None,
    allow_high_risk: bool = False,
    max_tasks_per_uav: int | None = None,
    priority_weight: float = 10.0,
) -> AssignmentResult:
    """Assign all possible tasks while updating UAV positions after each leg.

    The earlier one-shot baseline removes a UAV after assigning one task. This
    baseline keeps UAVs available, so it can build a route sequence per UAV.
    It is still deliberately interpretable and greedy, which makes it a strong
    baseline before MARL training.
    """
    working_uavs = {uav.uav_id: replace(uav) for uav in uavs}
    pending_tasks = {task.task_id: replace(task) for task in tasks}
    task_counts = {uav.uav_id: 0 for uav in uavs}
    assignments: list[RoutePlan] = []
    candidate_log: list[CandidateEvaluation] = []
    total_score = 0.0
    total_cost = 0.0

    while pending_tasks:
        best_uav: UavState | None = None
        best_task: TaskState | None = None
        best_candidate: CandidateEvaluation | None = None
        best_adjusted_score: float | None = None

        for uav in working_uavs.values():
            if max_tasks_per_uav is not None and task_counts[uav.uav_id] >= max_tasks_per_uav:
                continue
            if not allow_high_risk and uav.profile.dynamic_risk_level == "high":
                continue

            for task in pending_tasks.values():
                if task.payload_g > uav.payload_capacity_g:
                    continue
                candidate = evaluate_candidate(uav, task, weather_map, time=time)
                adjusted_score = candidate.score + _task_priority_bonus(task, priority_weight)
                candidate_log.append(candidate)
                if best_adjusted_score is None or adjusted_score > best_adjusted_score:
                    best_uav = uav
                    best_task = task
                    best_candidate = candidate
                    best_adjusted_score = adjusted_score

        if best_uav is None or best_task is None or best_candidate is None:
            break

        weather = weather_map.query_nearest(
            latitude=best_task.target_lat,
            longitude=best_task.target_lon,
            height_m=best_task.target_height_m,
            time=time,
        )
        waypoints = direct_route(best_uav, best_task)
        leg_index = task_counts[best_uav.uav_id] + 1
        route = RoutePlan(
            uav_id=best_uav.uav_id,
            task_id=best_task.task_id,
            waypoints=waypoints,
            total_distance_km=best_candidate.distance_km,
            total_cost=best_candidate.path_cost,
            weather_cost=weather.cost,
            profile_cost=100.0 - best_uav.profile.dynamic_health_score,
            metadata={
                "assignment_score": best_candidate.score,
                "adjusted_score": best_adjusted_score,
                "risk_level": best_uav.profile.dynamic_risk_level,
                "energy_pressure": best_candidate.energy_pressure,
                "leg_index": leg_index,
                "task_priority": best_task.priority,
            },
        )
        assignments.append(route)
        total_score += best_adjusted_score
        total_cost += best_candidate.path_cost

        best_uav.current_lat = best_task.target_lat
        best_uav.current_lon = best_task.target_lon
        best_uav.current_height_m = best_task.target_height_m
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

