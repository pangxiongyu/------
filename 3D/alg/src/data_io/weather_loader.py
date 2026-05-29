from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from src.core.schemas import WeatherCell


WEATHER_COLUMNS = [
    "time",
    "latitude",
    "longitude",
    "height_m",
    "cost",
    "wind_speed",
    "wind_direction",
    "temperature_2m",
    "relative_humidity_2m",
    "weather_code",
]


@dataclass
class WeatherMap:
    frame: pd.DataFrame

    @classmethod
    def from_csv(cls, path: str | Path) -> "WeatherMap":
        frame = pd.read_csv(path)
        missing = sorted(set(WEATHER_COLUMNS) - set(frame.columns))
        if missing:
            raise ValueError(f"Weather map is missing columns: {missing}")
        frame = frame.copy()
        frame["height_m"] = frame["height_m"].astype(float)
        return cls(frame)

    @property
    def times(self) -> list[str]:
        return list(self.frame["time"].drop_duplicates())

    @property
    def height_layers(self) -> list[float]:
        return sorted(float(value) for value in self.frame["height_m"].drop_duplicates())

    def layer(self, time: str | None = None, height_m: float | None = None) -> pd.DataFrame:
        selected = self.frame
        if time is not None:
            selected = selected[selected["time"] == time]
        if height_m is not None:
            selected = selected[selected["height_m"] == float(height_m)]
        return selected.copy()

    def query_nearest(
        self,
        latitude: float,
        longitude: float,
        height_m: float,
        time: str | None = None,
    ) -> WeatherCell:
        selected = self.layer(time=time, height_m=height_m)
        if selected.empty and time is not None:
            selected = self.layer(height_m=height_m)
        if selected.empty:
            raise ValueError(f"No weather cells found for height={height_m}, time={time}")

        distances = (selected["latitude"] - latitude) ** 2 + (
            selected["longitude"] - longitude
        ) ** 2
        row = selected.loc[distances.idxmin()]
        return row_to_weather_cell(row)

    def sample_low_cost_cells(
        self,
        count: int,
        time: str | None = None,
        height_m: float | None = None,
    ) -> list[WeatherCell]:
        selected = self.layer(time=time, height_m=height_m)
        if selected.empty:
            selected = self.frame
        return [
            row_to_weather_cell(row)
            for _, row in selected.sort_values("cost", ascending=True).head(count).iterrows()
        ]

    def sample_spread_cells(
        self,
        count: int,
        time: str | None = None,
        height_m: float | None = None,
    ) -> list[WeatherCell]:
        selected = self.layer(time=time, height_m=height_m).sort_values("cost")
        if selected.empty:
            selected = self.frame.sort_values("cost")
        if count <= 0:
            return []
        if len(selected) <= count:
            rows: Iterable = selected.iterrows()
        else:
            positions = [
                round(index * (len(selected) - 1) / max(1, count - 1))
                for index in range(count)
            ]
            rows = selected.iloc[positions].iterrows()
        return [row_to_weather_cell(row) for _, row in rows]


def row_to_weather_cell(row: pd.Series) -> WeatherCell:
    return WeatherCell(
        time=str(row["time"]),
        latitude=float(row["latitude"]),
        longitude=float(row["longitude"]),
        height_m=float(row["height_m"]),
        cost=float(row["cost"]),
        wind_speed=float(row["wind_speed"]),
        wind_direction=float(row["wind_direction"]),
        temperature_2m=float(row["temperature_2m"]),
        relative_humidity_2m=float(row["relative_humidity_2m"]),
        weather_code=float(row["weather_code"]),
    )


def load_weather_map(path: str | Path) -> WeatherMap:
    return WeatherMap.from_csv(path)

