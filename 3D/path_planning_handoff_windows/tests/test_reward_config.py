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


def make_weather_map() -> WeatherMap:
    return WeatherMap(
        pd.DataFrame(
            [
                {
                    "time": "t0",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "height_m": 10.0,
                    "cost": 0.1,
                    "wind_speed": 0.0,
                    "wind_direction": 0.0,
                    "temperature_2m": 20.0,
                    "relative_humidity_2m": 50.0,
                    "weather_code": 0.0,
                },
                {
                    "time": "t0",
                    "latitude": 1.0,
                    "longitude": 1.0,
                    "height_m": 10.0,
                    "cost": 0.7,
                    "wind_speed": 0.0,
                    "wind_direction": 0.0,
                    "temperature_2m": 20.0,
                    "relative_humidity_2m": 50.0,
                    "weather_code": 0.0,
                },
            ]
        )
    )


def run_single_reward(
    weather_weight: float = 20.0,
    path_cost_weight: float = 0.0,
    trackability_weight: float = 0.0,
) -> tuple[float, dict]:
    env = MultiUavTaskEnv(
        uavs=[UavState("U1", 0.0, 0.0, 10.0, 500.0, make_profile())],
        tasks=[TaskState("T1", 1.0, 1.0, 10.0, payload_g=100.0)],
        weather_map=make_weather_map(),
        time="t0",
        max_steps=1,
        weather_weight=weather_weight,
        path_cost_weight=path_cost_weight,
        trackability_weight=trackability_weight,
        max_trackable_segment_km=100.0,
    )
    env.reset()
    _, rewards, _, info = env.step({"U1": "T1"})
    return rewards["U1"], info["events"][0]


def test_weather_reward_weight_changes_environment_reward() -> None:
    low_weather_penalty, _ = run_single_reward(weather_weight=1.0)
    high_weather_penalty, _ = run_single_reward(weather_weight=50.0)

    assert high_weather_penalty < low_weather_penalty


def test_path_cost_reward_weight_changes_environment_reward() -> None:
    no_path_penalty, no_path_event = run_single_reward(path_cost_weight=0.0)
    high_path_penalty, high_path_event = run_single_reward(path_cost_weight=50.0)

    assert no_path_event["normalized_path_cost"] > 0.0
    assert high_path_event["normalized_path_cost"] == no_path_event["normalized_path_cost"]
    assert high_path_penalty < no_path_penalty


def test_trackability_reward_weight_penalizes_long_route_segments() -> None:
    no_trackability_penalty, no_trackability_event = run_single_reward(trackability_weight=0.0)
    high_trackability_penalty, high_trackability_event = run_single_reward(trackability_weight=50.0)

    assert no_trackability_event["max_segment_distance_km"] > 100.0
    assert high_trackability_event["normalized_trackability_penalty"] == 1.0
    assert high_trackability_event["trackability_penalty"] == 50.0
    assert high_trackability_penalty < no_trackability_penalty
