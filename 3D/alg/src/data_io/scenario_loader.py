from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from src.core.schemas import TaskState, UavState
from src.data_io.profile_loader import DynamicProfileStore, load_dynamic_profiles
from src.data_io.task_loader import load_tasks_csv, make_demo_tasks
from src.data_io.weather_loader import WeatherMap, load_weather_map


@dataclass
class PlanningScenario:
    weather_map: WeatherMap
    profile_store: DynamicProfileStore
    uavs: list[UavState]
    tasks: list[TaskState]
    time: str
    height_m: float
    config: dict[str, Any]


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file) or {}
    loaded["_config_path"] = str(config_path)
    loaded["_root"] = str(config_path.resolve().parents[1])
    return loaded


def resolve_project_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def build_scenario_from_config(config: dict[str, Any], root: str | Path) -> PlanningScenario:
    config = dict(config)
    root = Path(root)
    config.setdefault("_root", str(root))
    paths = config.get("paths", {})
    scenario_options = config.get("scenario", {})

    weather_map = load_weather_map(resolve_project_path(root, paths["weather_map"]))
    profile_store = load_dynamic_profiles(resolve_project_path(root, paths["dynamic_profiles"]))

    time = scenario_options.get("time")
    if time is None:
        time_index = int(scenario_options.get("time_index", 0))
        time = weather_map.times[time_index]
    height_m = float(scenario_options.get("height_m", weather_map.height_layers[0]))

    task_path = paths.get("tasks")
    if task_path:
        tasks = load_tasks_csv(resolve_project_path(root, task_path))
    else:
        task_count = int(scenario_options.get("task_count", 5))
        cells = weather_map.sample_spread_cells(task_count, time=time, height_m=height_m)
        tasks = make_demo_tasks(cells)

    uav_count = int(scenario_options.get("uav_count", 3))
    max_profile_risk = str(scenario_options.get("max_profile_risk", "medium"))
    profiles = profile_store.best_profiles(count=uav_count, max_risk=max_profile_risk)
    if len(profiles) < uav_count:
        raise ValueError(
            f"Only {len(profiles)} profiles are available for max risk {max_profile_risk!r}."
        )

    start_strategy = scenario_options.get("uav_start_strategy", "low_cost")
    if start_strategy == "low_cost":
        start_cells = weather_map.sample_low_cost_cells(uav_count, time=time, height_m=height_m)
    elif start_strategy == "spread":
        start_cells = weather_map.sample_spread_cells(uav_count, time=time, height_m=height_m)
    else:
        raise ValueError(f"Unsupported uav_start_strategy: {start_strategy}")

    payload_margin = float(scenario_options.get("payload_capacity_margin_g", 300.0))
    uavs = []
    for index, profile in enumerate(profiles):
        cell = start_cells[index % len(start_cells)]
        uavs.append(
            UavState(
                uav_id=f"U{index + 1}",
                current_lat=cell.latitude,
                current_lon=cell.longitude,
                current_height_m=cell.height_m,
                payload_capacity_g=max(500.0, profile.payload_g + payload_margin),
                profile=profile,
            )
        )

    return PlanningScenario(
        weather_map=weather_map,
        profile_store=profile_store,
        uavs=uavs,
        tasks=tasks,
        time=str(time),
        height_m=height_m,
        config=config,
    )


def build_scenario(config_path: str | Path = "configs/default.yaml") -> PlanningScenario:
    config = load_config(config_path)
    return build_scenario_from_config(config, config["_root"])
