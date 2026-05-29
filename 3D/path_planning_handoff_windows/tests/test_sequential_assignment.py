from __future__ import annotations

import pandas as pd

from src.baseline.sequential_assignment import sequential_greedy_assignment
from src.core.schemas import TaskState, UavProfile, UavState
from src.data_io.weather_loader import WeatherMap


def make_profile(flight_id: int, health: float = 95.0) -> UavProfile:
    return UavProfile(
        flight_id=flight_id,
        route="R",
        payload_g=0.0,
        target_altitude_m=10.0,
        window_start_s=0.0,
        window_end_s=1.0,
        pred_voltage_drop_v=0.0,
        pred_avg_current_a=0.0,
        pred_stability_risk=0.0,
        pred_stability_pressure=0.0,
        dynamic_health_score=health,
        dynamic_risk_level="low",
    )


def test_sequential_assignment_can_assign_more_tasks_than_uavs() -> None:
    weather = WeatherMap(
        pd.DataFrame(
            [
                {
                    "time": "t0",
                    "latitude": 30.0,
                    "longitude": 110.0,
                    "height_m": 10.0,
                    "cost": 0.1,
                    "wind_speed": 1.0,
                    "wind_direction": 0.0,
                    "temperature_2m": 20.0,
                    "relative_humidity_2m": 50.0,
                    "weather_code": 0.0,
                }
            ]
        )
    )
    uavs = [
        UavState("U1", 30.0, 110.0, 10.0, 500.0, make_profile(1)),
        UavState("U2", 30.1, 110.1, 10.0, 500.0, make_profile(2)),
    ]
    tasks = [
        TaskState("T1", 30.0, 110.0, 10.0, payload_g=100.0),
        TaskState("T2", 30.05, 110.05, 10.0, payload_g=100.0),
        TaskState("T3", 30.1, 110.1, 10.0, payload_g=100.0),
    ]
    result = sequential_greedy_assignment(uavs, tasks, weather, time="t0")
    assert len(result.assignments) == 3
    assert result.rejected_tasks == []

