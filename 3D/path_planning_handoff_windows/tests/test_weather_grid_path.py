from __future__ import annotations

import pandas as pd

from src.data_io.weather_loader import WeatherMap
from src.planning.weather_grid_path import WeatherGridPathPlanner


def test_weather_grid_path_finds_path_on_small_grid() -> None:
    rows = []
    for lat in [0.0, 1.0, 2.0]:
        for lon in [0.0, 1.0, 2.0]:
            rows.append(
                {
                    "time": "t0",
                    "latitude": lat,
                    "longitude": lon,
                    "height_m": 10.0,
                    "cost": 0.1,
                    "wind_speed": 0.0,
                    "wind_direction": 0.0,
                    "temperature_2m": 20.0,
                    "relative_humidity_2m": 50.0,
                    "weather_code": 0.0,
                }
            )
    weather_map = WeatherMap(pd.DataFrame(rows))
    planner = WeatherGridPathPlanner(weather_map, time="t0", height_m=10.0)
    result = planner.plan(0.0, 0.0, 2.0, 2.0)
    assert result.waypoints[0] == (0.0, 0.0, 10.0)
    assert result.waypoints[-1] == (2.0, 2.0, 10.0)
    assert result.distance_km > 0.0

