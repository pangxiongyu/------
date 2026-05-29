from __future__ import annotations

from dataclasses import replace
from typing import Any

from src.baseline.shortest_path import direct_route
from src.core.geo_utils import haversine_distance_km, max_route_segment_distance_km
from src.core.schemas import TaskState, UavState
from src.data_io.profile_loader import RISK_ORDER
from src.data_io.weather_loader import WeatherMap
from src.marl.action_space import (
    DEFAULT_ROUTE_STRATEGY,
    WEATHER_3D_ROUTE_STRATEGY,
    WEATHER_GRID_ROUTE_STRATEGY,
    build_task_actions,
    parse_task_action_with_strategy,
)
from src.marl.reward import task_reward
from src.planning.weather_3d_path import Weather3DPathPlanner
from src.planning.weather_grid_path import WeatherGridPathPlanner


WAIT_ACTIONS = {None, -1, "wait", "WAIT"}


class MultiUavTaskEnv:
    """Small MARL-style environment for early task-allocation experiments.

    This is intentionally framework-light. It exposes reset/step methods similar
    to Gymnasium/PettingZoo while keeping the project runnable before a full
    MAPPO stack is introduced.
    """

    def __init__(
        self,
        uavs: list[UavState],
        tasks: list[TaskState],
        weather_map: WeatherMap,
        time: str | None = None,
        max_steps: int = 20,
        conflict_penalty: float = 50.0,
        wait_penalty: float = 1.0,
        height_layers: list[float] | None = None,
        use_weather_grid_paths: bool = False,
        weather_grid_weight: float = 20.0,
        route_strategies: list[str] | None = None,
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
    ) -> None:
        self.initial_uavs = uavs
        self.initial_tasks = tasks
        self.weather_map = weather_map
        self.time = time
        self.max_steps = max_steps
        self.conflict_penalty = conflict_penalty
        self.wait_penalty = wait_penalty
        self.height_layers = height_layers
        self.use_weather_grid_paths = use_weather_grid_paths
        self.weather_grid_weight = weather_grid_weight
        self.route_strategies = route_strategies
        self.task_complete_reward = task_complete_reward
        self.distance_weight = distance_weight
        self.weather_weight = weather_weight
        self.energy_weight = energy_weight
        self.risk_weight = risk_weight
        self.path_cost_weight = path_cost_weight
        self.trackability_weight = trackability_weight
        self.max_distance_km = max_distance_km
        self.max_path_cost = max_path_cost
        self.max_trackable_segment_km = max_trackable_segment_km
        self._grid_planners: dict[float, WeatherGridPathPlanner] = {}
        self._weather_3d_planner: Weather3DPathPlanner | None = None
        self.uavs: dict[str, UavState] = {}
        self.tasks: dict[str, TaskState] = {}
        self.step_count = 0

    @property
    def agent_ids(self) -> list[str]:
        return list(self.uavs)

    def reset(self) -> dict[str, list[float]]:
        self.uavs = {uav.uav_id: replace(uav) for uav in self.initial_uavs}
        self.tasks = {task.task_id: replace(task) for task in self.initial_tasks}
        self.step_count = 0
        return self.observations()

    def observations(self) -> dict[str, list[float]]:
        pending_tasks = [task for task in self.tasks.values() if task.status == "pending"]
        obs: dict[str, list[float]] = {}
        for uav in self.uavs.values():
            nearest_distance = 0.0
            nearest_weather = 0.0
            if pending_tasks:
                nearest_task = min(
                    pending_tasks,
                    key=lambda task: haversine_distance_km(
                        uav.current_lat,
                        uav.current_lon,
                        task.target_lat,
                        task.target_lon,
                    ),
                )
                nearest_distance = haversine_distance_km(
                    uav.current_lat,
                    uav.current_lon,
                    nearest_task.target_lat,
                    nearest_task.target_lon,
                )
                nearest_weather = self.weather_map.query_nearest(
                    nearest_task.target_lat,
                    nearest_task.target_lon,
                    nearest_task.target_height_m,
                    time=self.time,
                ).cost

            risk_rank = RISK_ORDER.get(uav.profile.dynamic_risk_level, 3)
            obs[uav.uav_id] = [
                uav.current_lat,
                uav.current_lon,
                uav.current_height_m / 100.0,
                uav.profile.dynamic_health_score / 100.0,
                risk_rank / 2.0,
                uav.profile.pred_avg_current_a,
                uav.profile.pred_voltage_drop_v,
                uav.profile.pred_stability_risk,
                nearest_distance,
                nearest_weather,
                float(len(pending_tasks)),
            ]
        return obs

    def valid_actions(self) -> dict[str, list[str]]:
        pending = [task_id for task_id, task in self.tasks.items() if task.status == "pending"]
        actions = build_task_actions(pending, self.height_layers, self.route_strategies)
        return {uav_id: actions for uav_id in self.uavs}

    def _grid_planner(self, height_m: float) -> WeatherGridPathPlanner:
        height = float(height_m)
        if height not in self._grid_planners:
            if self.time is None:
                raise ValueError("Weather-grid path rewards require a fixed env time.")
            self._grid_planners[height] = WeatherGridPathPlanner(
                self.weather_map,
                time=self.time,
                height_m=height,
                weather_weight=self.weather_grid_weight,
            )
        return self._grid_planners[height]

    def _grid_3d_planner(self) -> Weather3DPathPlanner:
        if self._weather_3d_planner is None:
            if self.time is None:
                raise ValueError("3D weather path rewards require a fixed env time.")
            self._weather_3d_planner = Weather3DPathPlanner(
                self.weather_map,
                time=self.time,
                weather_weight=self.weather_grid_weight,
            )
        return self._weather_3d_planner

    def step(
        self,
        actions: dict[str, str | int | None],
    ) -> tuple[dict[str, list[float]], dict[str, float], bool, dict[str, Any]]:
        self.step_count += 1
        rewards = {uav_id: 0.0 for uav_id in self.uavs}
        info: dict[str, Any] = {"events": []}
        claimed_tasks: set[str] = set()

        for uav_id, action in actions.items():
            if uav_id not in self.uavs:
                continue
            if action in WAIT_ACTIONS:
                rewards[uav_id] -= self.wait_penalty
                info["events"].append({"uav_id": uav_id, "action": "wait"})
                continue

            task_id, selected_height_m, selected_strategy = parse_task_action_with_strategy(action)
            if task_id is None:
                rewards[uav_id] -= self.wait_penalty
                info["events"].append({"uav_id": uav_id, "action": "wait"})
                continue
            uav = self.uavs[uav_id]
            task = self.tasks.get(task_id)
            if task is None or task.status != "pending":
                rewards[uav_id] -= self.conflict_penalty
                info["events"].append(
                    {"uav_id": uav_id, "task_id": task_id, "event": "invalid_task"}
                )
                continue
            if task_id in claimed_tasks:
                rewards[uav_id] -= self.conflict_penalty
                info["events"].append(
                    {"uav_id": uav_id, "task_id": task_id, "event": "conflict"}
                )
                continue
            if task.payload_g > uav.payload_capacity_g:
                rewards[uav_id] -= self.conflict_penalty
                info["events"].append(
                    {"uav_id": uav_id, "task_id": task_id, "event": "payload_overload"}
                )
                continue

            selected_task = (
                replace(task, target_height_m=selected_height_m)
                if selected_height_m is not None
                else task
            )
            reward_kwargs: dict[str, Any] = {}
            route_strategy = selected_strategy
            if route_strategy is None:
                route_strategy = (
                    WEATHER_GRID_ROUTE_STRATEGY
                    if self.use_weather_grid_paths
                    else DEFAULT_ROUTE_STRATEGY
                )
            route_waypoints = direct_route(uav, selected_task)
            if route_strategy == WEATHER_GRID_ROUTE_STRATEGY:
                grid_path = self._grid_planner(selected_task.target_height_m).plan(
                    start_lat=uav.current_lat,
                    start_lon=uav.current_lon,
                    goal_lat=selected_task.target_lat,
                    goal_lon=selected_task.target_lon,
                )
                route_waypoints = grid_path.waypoints
                reward_kwargs = {
                    "path_distance_km": grid_path.distance_km,
                    "weather_cost": grid_path.weather_cost_sum / max(1, len(grid_path.waypoints)),
                    "path_cost": grid_path.total_cost,
                    "path_info": {
                        "grid_waypoint_count": float(len(grid_path.waypoints)),
                        "grid_visited_count": float(grid_path.visited_count),
                        "grid_weather_cost_sum": grid_path.weather_cost_sum,
                    },
                }
            elif route_strategy == WEATHER_3D_ROUTE_STRATEGY:
                grid_path = self._grid_3d_planner().plan(
                    start_lat=uav.current_lat,
                    start_lon=uav.current_lon,
                    start_height_m=uav.current_height_m,
                    goal_lat=selected_task.target_lat,
                    goal_lon=selected_task.target_lon,
                    goal_height_m=selected_task.target_height_m,
                )
                route_waypoints = grid_path.waypoints
                reward_kwargs = {
                    "path_distance_km": grid_path.distance_km,
                    "weather_cost": grid_path.weather_cost_sum / max(1, len(grid_path.waypoints)),
                    "path_cost": grid_path.total_cost,
                    "path_info": {
                        "grid_waypoint_count": float(len(grid_path.waypoints)),
                        "grid_visited_count": float(grid_path.visited_count),
                        "grid_weather_cost_sum": grid_path.weather_cost_sum,
                        "uses_3d_path": 1.0,
                    },
                }
            elif route_strategy != DEFAULT_ROUTE_STRATEGY:
                rewards[uav_id] -= self.conflict_penalty
                info["events"].append(
                    {
                        "uav_id": uav_id,
                        "task_id": task_id,
                        "event": "invalid_route_strategy",
                        "route_strategy": route_strategy,
                    }
                )
                continue
            route_path_info = reward_kwargs.setdefault("path_info", {})
            route_path_info.update(
                {
                    "waypoint_count": float(len(route_waypoints)),
                    "max_segment_distance_km": max_route_segment_distance_km(route_waypoints),
                }
            )
            reward_kwargs["max_segment_distance_km"] = route_path_info["max_segment_distance_km"]
            reward, reward_info = task_reward(
                uav,
                selected_task,
                self.weather_map,
                time=self.time,
                task_complete_reward=self.task_complete_reward,
                distance_weight=self.distance_weight,
                weather_weight=self.weather_weight,
                energy_weight=self.energy_weight,
                risk_weight=self.risk_weight,
                path_cost_weight=self.path_cost_weight,
                trackability_weight=self.trackability_weight,
                max_distance_km=self.max_distance_km,
                max_path_cost=self.max_path_cost,
                max_trackable_segment_km=self.max_trackable_segment_km,
                **reward_kwargs,
            )
            rewards[uav_id] += reward
            task.status = "completed"
            uav.current_lat = selected_task.target_lat
            uav.current_lon = selected_task.target_lon
            uav.current_height_m = selected_task.target_height_m
            uav.assigned_task_id = task.task_id
            claimed_tasks.add(task_id)
            info["events"].append(
                {
                    "uav_id": uav_id,
                    "task_id": task_id,
                    "selected_height_m": selected_task.target_height_m,
                    "route_strategy": route_strategy,
                    "event": "completed",
                    **reward_info,
                }
            )

        done = self.step_count >= self.max_steps or all(
            task.status == "completed" for task in self.tasks.values()
        )
        return self.observations(), rewards, done, info
