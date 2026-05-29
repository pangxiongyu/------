#!/usr/bin/env python3
"""
Prototype generator for a dynamic 3D weather cost map.

This script uses the existing output_data/*.csv files as sparse weather
observations. Each named region is treated as one observation point, and
10m / 100m wind layers are treated as two vertical layers.

Output format:
    time, latitude, longitude, height_m, cost, wind_speed, wind_direction,
    temperature_2m, relative_humidity_2m, weather_code

The generated CSV is intended for the first Web/QT visualization prototype.
It is not a replacement for ERA5 or other dense meteorological datasets.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "output_data"
OUTPUT_DIR = BASE_DIR / "generated_weather_cost_map"
OUTPUT_FILE = OUTPUT_DIR / "weather_cost_map_prototype.csv"
SAMPLE_OUTPUT_FILE = OUTPUT_DIR / "weather_cost_map_sample_24h.csv"

# Approximate representative coordinates for each named region.
# These are intentionally coarse because the source files do not contain
# explicit latitude/longitude columns.
REGION_COORDS = {
    "四川盆地": (30.67, 104.06),
    "云南大理苍山": (25.70, 100.16),
    "安徽合肥巢湖": (31.60, 117.87),
    "海南万宁": (18.80, 110.39),
    "西藏拉萨": (29.65, 91.12),
    "新疆": (43.79, 87.62),
}

HEIGHT_LAYERS = (10, 100)
GRID_LAT_COUNT = 18
GRID_LON_COUNT = 18


def parse_region_name(file_path: Path) -> str:
    return file_path.name.split("_", 1)[0]


def weather_penalty(weather_code: float) -> float:
    """Map Open-Meteo style weather code to a simple risk penalty."""
    code = int(weather_code)
    if code == 0:
        return 0.0
    if code in {1, 2, 3}:
        return 0.08
    if 45 <= code <= 48:
        return 0.18
    if 51 <= code <= 67:
        return 0.30
    if 71 <= code <= 77:
        return 0.36
    if 80 <= code <= 99:
        return 0.45
    return 0.12


def normalize(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    return max(0.0, min(1.0, (value - low) / (high - low)))


def compute_cost(row: dict[str, str], height_m: int) -> tuple[float, float, float]:
    if height_m == 10:
        wind_speed = float(row["wind_speed_10m"])
        wind_direction = float(row["wind_direction_10m"])
    elif height_m == 100:
        wind_speed = float(row["wind_speed_100m"])
        wind_direction = float(row["wind_direction_100m"])
    else:
        raise ValueError(f"Unsupported height layer: {height_m}")

    gust = float(row["wind_gusts_10m"])
    humidity = float(row["relative_humidity_2m"])
    weather_code = float(row["weather_code"])

    # Prototype cost function:
    # Wind is the main disturbance, gusts represent sudden risk, humidity and
    # weather code provide secondary environmental penalties.
    wind_cost = normalize(wind_speed, 0.0, 18.0)
    gust_cost = normalize(gust, 0.0, 25.0)
    humidity_cost = normalize(humidity, 50.0, 100.0)
    code_cost = weather_penalty(weather_code)

    cost = (
        0.52 * wind_cost
        + 0.24 * gust_cost
        + 0.14 * humidity_cost
        + 0.10 * code_cost
    )
    return max(0.0, min(1.0, cost)), wind_speed, wind_direction


def inverse_distance_weighted(
    target_lat: float,
    target_lon: float,
    observations: list[dict[str, float]],
    field: str,
    power: float = 2.0,
) -> float:
    weighted_sum = 0.0
    weight_total = 0.0
    for obs in observations:
        d_lat = target_lat - obs["latitude"]
        d_lon = target_lon - obs["longitude"]
        distance = math.sqrt(d_lat * d_lat + d_lon * d_lon)
        if distance < 1e-8:
            return obs[field]
        weight = 1.0 / (distance**power)
        weighted_sum += weight * obs[field]
        weight_total += weight
    return weighted_sum / weight_total if weight_total else 0.0


def build_grid() -> list[tuple[float, float]]:
    lats = [coord[0] for coord in REGION_COORDS.values()]
    lons = [coord[1] for coord in REGION_COORDS.values()]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    lat_step = (max_lat - min_lat) / (GRID_LAT_COUNT - 1)
    lon_step = (max_lon - min_lon) / (GRID_LON_COUNT - 1)
    return [
        (round(min_lat + i * lat_step, 6), round(min_lon + j * lon_step, 6))
        for i in range(GRID_LAT_COUNT)
        for j in range(GRID_LON_COUNT)
    ]


def load_observations() -> dict[tuple[str, int], list[dict[str, float]]]:
    observations_by_time_height: dict[tuple[str, int], list[dict[str, float]]] = defaultdict(list)

    for file_path in sorted(INPUT_DIR.glob("*.csv")):
        region = parse_region_name(file_path)
        if region not in REGION_COORDS:
            continue

        latitude, longitude = REGION_COORDS[region]
        with file_path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                for height_m in HEIGHT_LAYERS:
                    cost, wind_speed, wind_direction = compute_cost(row, height_m)
                    observations_by_time_height[(row["date"], height_m)].append(
                        {
                            "latitude": latitude,
                            "longitude": longitude,
                            "cost": cost,
                            "wind_speed": wind_speed,
                            "wind_direction": wind_direction,
                            "temperature_2m": float(row["temperature_2m"]),
                            "relative_humidity_2m": float(row["relative_humidity_2m"]),
                            "weather_code": float(row["weather_code"]),
                        }
                    )
    return observations_by_time_height


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    grid = build_grid()
    observations_by_time_height = load_observations()
    sorted_slices = sorted(observations_by_time_height.items())
    sample_times = {time_value for (time_value, _height_m), _observations in sorted_slices[:48]}

    fieldnames = [
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

    with (
        OUTPUT_FILE.open("w", encoding="utf-8", newline="") as full_file,
        SAMPLE_OUTPUT_FILE.open("w", encoding="utf-8", newline="") as sample_file,
    ):
        full_writer = csv.DictWriter(full_file, fieldnames=fieldnames)
        sample_writer = csv.DictWriter(sample_file, fieldnames=fieldnames)
        full_writer.writeheader()
        sample_writer.writeheader()

        for (time_value, height_m), observations in sorted_slices:
            if len(observations) < 2:
                continue
            for latitude, longitude in grid:
                output_row = {
                    "time": time_value,
                    "latitude": latitude,
                    "longitude": longitude,
                    "height_m": height_m,
                    "cost": round(
                        inverse_distance_weighted(latitude, longitude, observations, "cost"),
                        6,
                    ),
                    "wind_speed": round(
                        inverse_distance_weighted(latitude, longitude, observations, "wind_speed"),
                        6,
                    ),
                    "wind_direction": round(
                        inverse_distance_weighted(latitude, longitude, observations, "wind_direction"),
                        6,
                    ),
                    "temperature_2m": round(
                        inverse_distance_weighted(latitude, longitude, observations, "temperature_2m"),
                        6,
                    ),
                    "relative_humidity_2m": round(
                        inverse_distance_weighted(latitude, longitude, observations, "relative_humidity_2m"),
                        6,
                    ),
                    "weather_code": round(
                        inverse_distance_weighted(latitude, longitude, observations, "weather_code"),
                        6,
                    ),
                }
                full_writer.writerow(output_row)
                if time_value in sample_times:
                    sample_writer.writerow(output_row)

    print(f"Generated: {OUTPUT_FILE}")
    print(f"Generated sample: {SAMPLE_OUTPUT_FILE}")
    print(f"Time-height slices: {len(observations_by_time_height)}")
    print(f"Grid points per slice: {len(grid)}")


if __name__ == "__main__":
    main()
