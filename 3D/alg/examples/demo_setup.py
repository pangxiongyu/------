from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_io.scenario_loader import build_scenario


WEATHER_SAMPLE = ROOT / "data" / "weather_cost_map" / "weather_cost_map_sample_24h.csv"
UAV_PROFILE = ROOT / "data" / "uav_profiles" / "torch_mamba_uav_dynamic_profiles.csv"


def build_demo_problem(uav_count: int = 3, task_count: int = 5):
    scenario = build_scenario(ROOT / "configs" / "default.yaml")
    return (
        scenario.weather_map,
        scenario.uavs[:uav_count],
        scenario.tasks[:task_count],
        scenario.time,
    )
