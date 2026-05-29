#!/usr/bin/env python3
"""
Generate a dynamic 3D weather cost map with Gaussian Process Regression.

This script upgrades the previous IDW prototype to the project-book algorithm
wording: GPR-based 3D dynamic weather modeling. It keeps the same output schema
as `build_weather_cost_map.py`, so downstream path-planning code can switch data
files without changing loaders.

The current raw data only contains sparse named-region observations. Therefore,
this is a sparse-observation GPR prototype. It is suitable for project alignment,
Web/QT visualization, and path-planning integration. For final research-grade
weather fields, replace `output_data/` with ERA5/Open-Meteo multi-grid data.
"""

from __future__ import annotations

import csv
import json
import math
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF, WhiteKernel
from sklearn.preprocessing import StandardScaler


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "output_data"
OUTPUT_DIR = BASE_DIR / "generated_weather_cost_map"
OUTPUT_FILE = OUTPUT_DIR / "weather_cost_map_gpr.csv"
SAMPLE_OUTPUT_FILE = OUTPUT_DIR / "weather_cost_map_gpr_sample_24h.csv"
METRICS_FILE = OUTPUT_DIR / "gpr_weather_metrics.json"

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
PREDICT_FIELDS = [
    "cost",
    "wind_speed",
    "wind_direction",
    "temperature_2m",
    "relative_humidity_2m",
    "weather_code",
]


def parse_region_name(file_path: Path) -> str:
    return file_path.name.split("_", 1)[0]


def weather_penalty(weather_code: float) -> float:
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

    wind_cost = normalize(wind_speed, 0.0, 18.0)
    gust_cost = normalize(gust, 0.0, 25.0)
    humidity_cost = normalize(humidity, 50.0, 100.0)
    code_cost = weather_penalty(weather_code)
    cost = 0.52 * wind_cost + 0.24 * gust_cost + 0.14 * humidity_cost + 0.10 * code_cost
    return max(0.0, min(1.0, cost)), wind_speed, wind_direction


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


def fit_predict_gpr(
    observations: list[dict[str, float]],
    grid: list[tuple[float, float]],
) -> tuple[list[dict[str, float]], dict[str, float]]:
    train_xy = np.asarray(
        [[obs["latitude"], obs["longitude"]] for obs in observations],
        dtype=np.float64,
    )
    grid_xy = np.asarray(grid, dtype=np.float64)

    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train_xy)
    grid_scaled = scaler.transform(grid_xy)

    kernel = ConstantKernel(1.0, (0.1, 10.0)) * RBF(length_scale=1.0, length_scale_bounds=(0.2, 10.0)) + WhiteKernel(
        noise_level=1e-4,
        noise_level_bounds=(1e-6, 1e-1),
    )
    y_matrix = np.asarray(
        [[obs[field] for field in PREDICT_FIELDS] for obs in observations],
        dtype=np.float64,
    )
    model = GaussianProcessRegressor(
        kernel=kernel,
        alpha=1e-5,
        normalize_y=True,
        optimizer=None,
        random_state=42,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit(train_scaled, y_matrix)
        mean_matrix, std_matrix = model.predict(grid_scaled, return_std=True)

    predictions = {
        field: mean_matrix[:, field_index]
        for field_index, field in enumerate(PREDICT_FIELDS)
    }
    if std_matrix.ndim == 1:
        uncertainties = {f"{field}_mean_std": float(np.mean(std_matrix)) for field in PREDICT_FIELDS}
    else:
        uncertainties = {
            f"{field}_mean_std": float(np.mean(std_matrix[:, field_index]))
            for field_index, field in enumerate(PREDICT_FIELDS)
        }

    rows: list[dict[str, float]] = []
    for index, (latitude, longitude) in enumerate(grid):
        rows.append(
            {
                "latitude": latitude,
                "longitude": longitude,
                "cost": float(np.clip(predictions["cost"][index], 0.0, 1.0)),
                "wind_speed": float(max(0.0, predictions["wind_speed"][index])),
                "wind_direction": float(predictions["wind_direction"][index] % 360.0),
                "temperature_2m": float(predictions["temperature_2m"][index]),
                "relative_humidity_2m": float(np.clip(predictions["relative_humidity_2m"][index], 0.0, 100.0)),
                "weather_code": float(max(0.0, predictions["weather_code"][index])),
            }
        )
    return rows, uncertainties


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
    uncertainty_accumulator: dict[str, list[float]] = defaultdict(list)

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
            predicted_rows, uncertainties = fit_predict_gpr(observations, grid)
            for key, value in uncertainties.items():
                uncertainty_accumulator[key].append(value)

            for row in predicted_rows:
                output_row = {
                    "time": time_value,
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "height_m": height_m,
                    "cost": round(row["cost"], 6),
                    "wind_speed": round(row["wind_speed"], 6),
                    "wind_direction": round(row["wind_direction"], 6),
                    "temperature_2m": round(row["temperature_2m"], 6),
                    "relative_humidity_2m": round(row["relative_humidity_2m"], 6),
                    "weather_code": round(row["weather_code"], 6),
                }
                full_writer.writerow(output_row)
                if time_value in sample_times:
                    sample_writer.writerow(output_row)

    metrics = {
        "method": "GaussianProcessRegressor",
        "input_observation_points": len(REGION_COORDS),
        "height_layers": list(HEIGHT_LAYERS),
        "grid_points_per_slice": len(grid),
        "time_height_slices": len(sorted_slices),
        "kernel": "ConstantKernel * RBF + WhiteKernel",
        "mean_predictive_std": {
            key: float(np.mean(values)) for key, values in uncertainty_accumulator.items()
        },
        "note": "Sparse-region GPR prototype. Replace raw inputs with ERA5/Open-Meteo grid data for final high-resolution modeling.",
    }
    METRICS_FILE.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Generated: {OUTPUT_FILE}")
    print(f"Generated sample: {SAMPLE_OUTPUT_FILE}")
    print(f"Generated metrics: {METRICS_FILE}")
    print(f"Time-height slices: {len(sorted_slices)}")
    print(f"Grid points per slice: {len(grid)}")


if __name__ == "__main__":
    main()
