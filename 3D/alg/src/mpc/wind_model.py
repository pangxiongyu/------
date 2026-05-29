from __future__ import annotations

from src.core.schemas import WeatherCell
from src.mpc.dynamics import WindVector, wind_from_speed_direction


def weather_cell_to_wind(cell: WeatherCell) -> WindVector:
    return wind_from_speed_direction(cell.wind_speed, cell.wind_direction)

