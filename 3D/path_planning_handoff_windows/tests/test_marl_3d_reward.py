from __future__ import annotations

import pandas as pd

from src.core.schemas import TaskState, UavProfile, UavState
from src.data_io.weather_loader import WeatherMap
from src.marl.env import MultiUavTaskEnv


def make_profile() -> UavProfile:
    return UavProfile(
        flight_id=1,
        route="R",
        payload_g=0.0,
        target_altitude_m=10.0,
        window_start_s=0.0,
        window_end_s=1.0,
        pred_voltage_drop_v=0.0,
        pred_avg_current_a=0.0,
        pred_stability_risk=0.0,
        pred_stability_pressure=0.0,
        dynamic_health_score=90.0,
        dynamic_risk_level="low",
    )


def test_env_weather_3d_reward_adds_3d_info() -> None:
    rows = []
    for height in [10.0, 100.0]:
        for lat in [0.0, 1.0]:
            for lon in [0.0, 1.0]:
                rows.append(
                    {
                        "time": "t0",
                        "latitude": lat,
                        "longitude": lon,
                        "height_m": height,
                        "cost": 0.1,
                        "wind_speed": 0.0,
                        "wind_direction": 0.0,
                        "temperature_2m": 20.0,
                        "relative_humidity_2m": 50.0,
                        "weather_code": 0.0,
                    }
                )
    env = MultiUavTaskEnv(
        uavs=[UavState("U1", 0.0, 0.0, 10.0, 500.0, make_profile())],
        tasks=[TaskState("T1", 1.0, 1.0, 100.0, payload_g=100.0)],
        weather_map=WeatherMap(pd.DataFrame(rows)),
        time="t0",
        height_layers=[10.0, 100.0],
        route_strategies=["weather_3d"],
    )
    env.reset()
    _, rewards, done, info = env.step({"U1": "T1@100m#weather_3d"})
    assert done
    assert rewards["U1"] > 0.0
    event = info["events"][0]
    assert event["uses_3d_path"] == 1.0
    assert event["selected_height_m"] == 100.0

