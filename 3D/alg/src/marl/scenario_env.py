from __future__ import annotations

from src.data_io.scenario_loader import PlanningScenario
from src.marl.env import MultiUavTaskEnv


def build_marl_env_from_scenario(scenario: PlanningScenario) -> MultiUavTaskEnv:
    marl_config = scenario.config.get("marl", {})
    baseline_config = scenario.config.get("baseline", {})
    reward_config = marl_config.get("reward", {})
    height_layers = scenario.weather_map.height_layers if marl_config.get("use_height_actions") else None
    return MultiUavTaskEnv(
        scenario.uavs,
        scenario.tasks,
        scenario.weather_map,
        time=scenario.time,
        max_steps=int(marl_config.get("max_steps", 4)),
        conflict_penalty=float(marl_config.get("conflict_penalty", 50.0)),
        wait_penalty=float(marl_config.get("wait_penalty", 1.0)),
        height_layers=height_layers,
        use_weather_grid_paths=bool(marl_config.get("use_weather_grid_paths", False)),
        weather_grid_weight=float(baseline_config.get("weather_grid_weight", 20.0)),
        route_strategies=marl_config.get("route_strategies"),
        task_complete_reward=float(reward_config.get("task_complete_reward", 100.0)),
        distance_weight=float(reward_config.get("distance_weight", 10.0)),
        weather_weight=float(reward_config.get("weather_weight", 20.0)),
        energy_weight=float(reward_config.get("energy_weight", 5.0)),
        risk_weight=float(reward_config.get("risk_weight", 1.0)),
        path_cost_weight=float(reward_config.get("path_cost_weight", 0.0)),
        trackability_weight=float(reward_config.get("trackability_weight", 0.0)),
        max_distance_km=float(reward_config.get("max_distance_km", 1500.0)),
        max_path_cost=float(reward_config.get("max_path_cost", 12000.0)),
        max_trackable_segment_km=float(
            reward_config.get("max_trackable_segment_km", 1000.0)
        ),
    )
