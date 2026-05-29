from __future__ import annotations

from dataclasses import dataclass, replace

from src.baseline.shortest_path import direct_route
from src.baseline.rule_assignment import greedy_assignment
from src.baseline.sequential_assignment import sequential_greedy_assignment
from src.baseline.weather_aware_assignment import weather_aware_sequential_assignment
from src.core.schemas import AssignmentResult, RoutePlan, TaskState, UavState, Waypoint
from src.data_io.scenario_loader import PlanningScenario
from src.eval.metrics import assignment_metrics
from src.marl.action_space import (
    DEFAULT_ROUTE_STRATEGY,
    WEATHER_3D_ROUTE_STRATEGY,
    WEATHER_GRID_ROUTE_STRATEGY,
)
from src.marl.policy import greedy_policy_actions
from src.marl.scenario_env import build_marl_env_from_scenario
from src.planning.weather_3d_path import Weather3DPathPlanner
from src.planning.weather_grid_path import WeatherGridPathPlanner


@dataclass
class ScenarioEvaluation:
    metrics_by_method: dict[str, dict[str, float]]
    assignment_results: dict[str, AssignmentResult]


@dataclass
class MarlGreedyEvaluation:
    metrics: dict[str, float]
    assignment_result: AssignmentResult


def marl_route_waypoints(
    scenario: PlanningScenario,
    start_uav: UavState,
    task: TaskState,
    route_strategy: str,
    weather_grid_weight: float,
) -> list[Waypoint]:
    if route_strategy == WEATHER_GRID_ROUTE_STRATEGY:
        planner = WeatherGridPathPlanner(
            scenario.weather_map,
            time=scenario.time,
            height_m=task.target_height_m,
            weather_weight=weather_grid_weight,
        )
        return planner.plan(
            start_lat=start_uav.current_lat,
            start_lon=start_uav.current_lon,
            goal_lat=task.target_lat,
            goal_lon=task.target_lon,
        ).waypoints
    if route_strategy == WEATHER_3D_ROUTE_STRATEGY:
        planner = Weather3DPathPlanner(
            scenario.weather_map,
            time=scenario.time,
            weather_weight=weather_grid_weight,
        )
        return planner.plan(
            start_lat=start_uav.current_lat,
            start_lon=start_uav.current_lon,
            start_height_m=start_uav.current_height_m,
            goal_lat=task.target_lat,
            goal_lon=task.target_lon,
            goal_height_m=task.target_height_m,
        ).waypoints
    return direct_route(start_uav, task)


def run_marl_greedy_evaluation(scenario: PlanningScenario) -> MarlGreedyEvaluation:
    marl_config = scenario.config.get("marl", {})
    height_layers = scenario.weather_map.height_layers if marl_config.get("use_height_actions") else None
    route_strategies = marl_config.get("route_strategies")
    weather_grid_weight = float(scenario.config.get("baseline", {}).get("weather_grid_weight", 20.0))
    env = build_marl_env_from_scenario(scenario)
    env.reset()
    done = False
    total_reward = 0.0
    completed = 0
    conflict_count = 0
    weather_sum = 0.0
    path_cost_sum = 0.0
    distance_sum = 0.0
    total_score = 0.0
    strategy_counts = {
        DEFAULT_ROUTE_STRATEGY: 0,
        WEATHER_GRID_ROUTE_STRATEGY: 0,
        WEATHER_3D_ROUTE_STRATEGY: 0,
    }
    assignments: list[RoutePlan] = []
    task_counts = {uav.uav_id: 0 for uav in scenario.uavs}

    while not done:
        before_uavs = {uav_id: replace(uav) for uav_id, uav in env.uavs.items()}
        before_tasks = {task_id: replace(task) for task_id, task in env.tasks.items()}
        actions = greedy_policy_actions(
            list(env.uavs.values()),
            list(env.tasks.values()),
            scenario.weather_map,
            time=scenario.time,
            height_layers=height_layers,
            route_strategies=route_strategies,
            weather_grid_weight=weather_grid_weight,
        )
        _, rewards, done, info = env.step(actions)
        total_reward += sum(rewards.values())
        for event in info["events"]:
            if event.get("event") == "completed":
                completed += 1
                route_strategy = str(event.get("route_strategy", DEFAULT_ROUTE_STRATEGY))
                if route_strategy in strategy_counts:
                    strategy_counts[route_strategy] += 1
                event_score = float(event.get("assignment_score", 0.0))
                total_score += event_score
                weather_sum += float(event.get("weather_cost", 0.0))
                path_cost_sum += float(event.get("path_cost", 0.0))
                distance_sum += float(event.get("distance_km", 0.0))
                task_id = str(event["task_id"])
                uav_id = str(event["uav_id"])
                start_uav = before_uavs[uav_id]
                original_task = before_tasks[task_id]
                selected_task = replace(
                    original_task,
                    target_height_m=float(event.get("selected_height_m", original_task.target_height_m)),
                )
                task_counts[uav_id] += 1
                assignments.append(
                    RoutePlan(
                        uav_id=uav_id,
                        task_id=task_id,
                        waypoints=marl_route_waypoints(
                            scenario,
                            start_uav,
                            selected_task,
                            route_strategy,
                            weather_grid_weight,
                        ),
                        total_distance_km=float(event.get("distance_km", 0.0)),
                        total_cost=float(event.get("path_cost", 0.0)),
                        weather_cost=float(event.get("weather_cost", 0.0)),
                        profile_cost=100.0 - start_uav.profile.dynamic_health_score,
                        metadata={
                            "assignment_score": event_score,
                            "adjusted_score": float(rewards.get(uav_id, 0.0)),
                            "risk_level": start_uav.profile.dynamic_risk_level,
                            "energy_pressure": float(event.get("energy_pressure", 0.0)),
                            "leg_index": task_counts[uav_id],
                            "task_priority": selected_task.priority,
                            "route_strategy": route_strategy,
                            "selected_height_m": selected_task.target_height_m,
                            "grid_waypoint_count": float(event.get("grid_waypoint_count", 0.0)),
                            "grid_visited_count": float(event.get("grid_visited_count", 0.0)),
                            "uses_3d_path": float(event.get("uses_3d_path", 0.0)),
                            "waypoint_count": float(event.get("waypoint_count", 0.0)),
                            "max_segment_distance_km": float(
                                event.get("max_segment_distance_km", 0.0)
                            ),
                            "trackability_penalty": float(
                                event.get("trackability_penalty", 0.0)
                            ),
                        },
                    )
                )
            elif event.get("event") in {"conflict", "invalid_task", "payload_overload"}:
                conflict_count += 1

    task_count = len(scenario.tasks)
    rejected_tasks = sorted(
        task_id for task_id, task in env.tasks.items() if task.status == "pending"
    )
    assignment_result = AssignmentResult(
        assignments=assignments,
        rejected_tasks=rejected_tasks,
        total_score=total_score,
        total_cost=path_cost_sum,
        metadata={
            "task_counts": task_counts,
            "route_strategy_counts": strategy_counts,
            "total_reward": total_reward,
        },
    )
    metrics = {
        "task_completion_rate": completed / task_count if task_count else 0.0,
        "completed_task_count": float(completed),
        "rejected_task_count": float(len(rejected_tasks)),
        "total_reward": total_reward,
        "total_path_cost": path_cost_sum,
        "total_assignment_score": total_score,
        "total_distance_km": distance_sum,
        "average_max_segment_distance_km": (
            sum(route.metadata.get("max_segment_distance_km", 0.0) for route in assignments)
            / completed
            if completed
            else 0.0
        ),
        "max_segment_distance_km": (
            max(route.metadata.get("max_segment_distance_km", 0.0) for route in assignments)
            if assignments
            else 0.0
        ),
        "trackability_penalty": sum(
            float(route.metadata.get("trackability_penalty", 0.0))
            for route in assignments
        ),
        "average_weather_cost": weather_sum / completed if completed else 0.0,
        "uav_conflict_count": float(conflict_count),
        "uses_weather_grid_paths": float(strategy_counts[WEATHER_GRID_ROUTE_STRATEGY] > 0),
        "direct_action_count": float(strategy_counts[DEFAULT_ROUTE_STRATEGY]),
        "weather_grid_action_count": float(strategy_counts[WEATHER_GRID_ROUTE_STRATEGY]),
        "weather_3d_action_count": float(strategy_counts[WEATHER_3D_ROUTE_STRATEGY]),
        "uses_weather_3d_paths": float(strategy_counts[WEATHER_3D_ROUTE_STRATEGY] > 0),
    }
    return MarlGreedyEvaluation(metrics=metrics, assignment_result=assignment_result)


def run_marl_greedy_metrics(scenario: PlanningScenario) -> dict[str, float]:
    return run_marl_greedy_evaluation(scenario).metrics


def evaluate_scenario(scenario: PlanningScenario) -> ScenarioEvaluation:
    baseline_config = scenario.config.get("baseline", {})
    baseline_result = greedy_assignment(
        scenario.uavs,
        scenario.tasks,
        scenario.weather_map,
        time=scenario.time,
        allow_high_risk=bool(baseline_config.get("allow_high_risk", False)),
    )
    sequential_result = sequential_greedy_assignment(
        scenario.uavs,
        scenario.tasks,
        scenario.weather_map,
        time=scenario.time,
        allow_high_risk=bool(baseline_config.get("allow_high_risk", False)),
        max_tasks_per_uav=baseline_config.get("max_tasks_per_uav"),
    )
    weather_aware_result = weather_aware_sequential_assignment(
        scenario.uavs,
        scenario.tasks,
        scenario.weather_map,
        time=scenario.time,
        height_m=scenario.height_m,
        allow_high_risk=bool(baseline_config.get("allow_high_risk", False)),
        max_tasks_per_uav=baseline_config.get("max_tasks_per_uav"),
        weather_weight=float(baseline_config.get("weather_grid_weight", 20.0)),
    )
    marl_greedy_evaluation = run_marl_greedy_evaluation(scenario)
    assignment_results = {
        "one_shot": baseline_result,
        "sequential": sequential_result,
        "weather_grid": weather_aware_result,
        "marl_greedy": marl_greedy_evaluation.assignment_result,
    }
    metrics_by_method = {
        "one_shot": assignment_metrics(baseline_result, task_count=len(scenario.tasks)),
        "sequential": assignment_metrics(sequential_result, task_count=len(scenario.tasks)),
        "weather_grid": assignment_metrics(weather_aware_result, task_count=len(scenario.tasks)),
        "marl_greedy": marl_greedy_evaluation.metrics,
    }
    return ScenarioEvaluation(
        metrics_by_method=metrics_by_method,
        assignment_results=assignment_results,
    )
