from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path

from src.core.schemas import AssignmentResult, RoutePlan
from src.data_io.scenario_loader import PlanningScenario, build_scenario
from src.eval.scenario_eval import marl_route_waypoints
from src.marl.action_space import (
    DEFAULT_ROUTE_STRATEGY,
    WEATHER_3D_ROUTE_STRATEGY,
    WEATHER_GRID_ROUTE_STRATEGY,
)
from src.marl.scenario_env import build_marl_env_from_scenario
from src.marl.train_mappo import MAPPOPrototypeTrainer


@dataclass(frozen=True)
class MappoCheckpointEvaluation:
    raw_metrics: dict[str, float]
    comparable_metrics: dict[str, float]
    assignment_result: AssignmentResult


def mappo_metrics_to_comparable_metrics(
    raw_metrics: dict[str, float],
    task_count: int,
) -> dict[str, float]:
    completed = float(raw_metrics.get("mean_completed_task_count", 0.0))
    return {
        "task_completion_rate": completed / task_count if task_count else 0.0,
        "completed_task_count": completed,
        "rejected_task_count": max(0.0, float(task_count) - completed),
        "total_reward": float(raw_metrics.get("mean_total_reward", 0.0)),
        "total_path_cost": float(raw_metrics.get("mean_total_path_cost", 0.0)),
        "total_assignment_score": 0.0,
        "total_distance_km": float(raw_metrics.get("mean_total_distance_km", 0.0)),
        "average_max_segment_distance_km": float(
            raw_metrics.get("mean_average_max_segment_distance_km", 0.0)
        ),
        "max_segment_distance_km": float(raw_metrics.get("mean_peak_segment_distance_km", 0.0)),
        "trackability_penalty": float(raw_metrics.get("mean_trackability_penalty", 0.0)),
        "average_weather_cost": float(raw_metrics.get("mean_average_weather_cost", 0.0)),
        "uav_conflict_count": float(raw_metrics.get("mean_conflict_count", 0.0)),
        "direct_action_count": float(raw_metrics.get("mean_direct_action_count", 0.0)),
        "weather_grid_action_count": float(raw_metrics.get("mean_weather_grid_action_count", 0.0)),
        "weather_3d_action_count": float(raw_metrics.get("mean_weather_3d_action_count", 0.0)),
        "uses_weather_grid_paths": float(raw_metrics.get("mean_weather_grid_action_count", 0.0) > 0.0),
        "uses_weather_3d_paths": float(raw_metrics.get("mean_weather_3d_action_count", 0.0) > 0.0),
    }


def evaluate_mappo_checkpoint_for_scenario(
    scenario: PlanningScenario,
    checkpoint_path: str | Path,
    episodes: int,
) -> MappoCheckpointEvaluation:
    mappo_config = scenario.config.get("mappo", {})
    trainer = MAPPOPrototypeTrainer(
        lambda: build_marl_env_from_scenario(scenario),
        episodes=1,
        ppo_epochs=1,
        mask_wait_when_tasks_available=bool(
            mappo_config.get("mask_wait_when_tasks_available", True)
        ),
        seed=int(mappo_config["seed"]) if "seed" in mappo_config else None,
    )
    trainer.load_checkpoint(checkpoint_path)
    raw_metrics = trainer.evaluate_policy(episodes=episodes, deterministic=True)
    assignment_result = rollout_mappo_assignment_result(scenario, trainer)
    return MappoCheckpointEvaluation(
        raw_metrics=raw_metrics,
        comparable_metrics=mappo_metrics_to_comparable_metrics(
            raw_metrics,
            task_count=len(scenario.tasks),
        ),
        assignment_result=assignment_result,
    )


def evaluate_mappo_checkpoint_for_config(
    config_path: str | Path,
    checkpoint_path: str | Path,
    episodes: int,
) -> MappoCheckpointEvaluation:
    scenario = build_scenario(config_path)
    return evaluate_mappo_checkpoint_for_scenario(
        scenario,
        checkpoint_path=checkpoint_path,
        episodes=episodes,
    )


def rollout_mappo_assignment_result(
    scenario: PlanningScenario,
    trainer: MAPPOPrototypeTrainer,
) -> AssignmentResult:
    env = build_marl_env_from_scenario(scenario)
    observations = env.reset()
    weather_grid_weight = float(scenario.config.get("baseline", {}).get("weather_grid_weight", 20.0))
    done = False
    total_reward = 0.0
    total_score = 0.0
    total_cost = 0.0
    task_counts = {uav.uav_id: 0 for uav in scenario.uavs}
    strategy_counts = {
        DEFAULT_ROUTE_STRATEGY: 0,
        WEATHER_GRID_ROUTE_STRATEGY: 0,
        WEATHER_3D_ROUTE_STRATEGY: 0,
    }
    conflict_count = 0
    assignments: list[RoutePlan] = []

    while not done:
        before_uavs = {uav_id: replace(uav) for uav_id, uav in env.uavs.items()}
        before_tasks = {task_id: replace(task) for task_id, task in env.tasks.items()}
        actions = trainer.policy_actions(
            observations,
            env.valid_actions(),
            deterministic=True,
            avoid_duplicate_tasks=True,
        )
        observations, rewards, done, info = env.step(actions)
        total_reward += sum(rewards.values())
        for event in info["events"]:
            if event.get("event") == "completed":
                task_id = str(event["task_id"])
                uav_id = str(event["uav_id"])
                route_strategy = str(event.get("route_strategy", DEFAULT_ROUTE_STRATEGY))
                if route_strategy in strategy_counts:
                    strategy_counts[route_strategy] += 1
                start_uav = before_uavs[uav_id]
                original_task = before_tasks[task_id]
                selected_task = replace(
                    original_task,
                    target_height_m=float(event.get("selected_height_m", original_task.target_height_m)),
                )
                event_score = float(event.get("assignment_score", 0.0))
                path_cost = float(event.get("path_cost", 0.0))
                total_score += event_score
                total_cost += path_cost
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
                        total_cost=path_cost,
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
            elif event.get("event") in {
                "conflict",
                "invalid_task",
                "payload_overload",
                "invalid_route_strategy",
            }:
                conflict_count += 1

    rejected_tasks = sorted(
        task_id for task_id, task in env.tasks.items() if task.status == "pending"
    )
    return AssignmentResult(
        assignments=assignments,
        rejected_tasks=rejected_tasks,
        total_score=total_score,
        total_cost=total_cost,
        metadata={
            "task_counts": task_counts,
            "route_strategy_counts": strategy_counts,
            "total_reward": total_reward,
            "conflict_count": conflict_count,
        },
    )
