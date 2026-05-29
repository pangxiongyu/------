from __future__ import annotations

import pandas as pd

from src.data_io.weather_loader import WeatherMap
from src.planning.weather_3d_path import Weather3DPathPlanner


def test_weather_3d_path_connects_height_layers() -> None:
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
    planner = Weather3DPathPlanner(WeatherMap(pd.DataFrame(rows)), time="t0")
    result = planner.plan(0.0, 0.0, 10.0, 1.0, 1.0, 100.0)
    assert result.waypoints[0] == (0.0, 0.0, 10.0)
    assert result.waypoints[-1] == (1.0, 1.0, 100.0)
    assert 10.0 in {point[2] for point in result.waypoints}
    assert 100.0 in {point[2] for point in result.waypoints}

